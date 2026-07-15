from __future__ import annotations

from dataclasses import dataclass

from sta_lite.lint.ast_nodes import AlwaysBlock, Assignment, Design, FunctionDecl, GenerateBlock, Instance, Module, Signal, TaskDecl
from sta_lite.lint.lexer import KEYWORDS, Token
from sta_lite.models.diagnostic import Diagnostic


DECL_KEYWORDS = {
    "input",
    "output",
    "inout",
    "wire",
    "reg",
    "logic",
    "bit",
    "byte",
    "shortint",
    "int",
    "longint",
    "integer",
    "time",
    "genvar",
    "signed",
    "unsigned",
}
DATA_TYPES = {"wire", "reg", "logic", "bit", "byte", "shortint", "int", "longint", "integer", "time", "genvar"}
DIRECTIONS = {"input", "output", "inout"}
ASSIGN_OPS = {"=", "<=", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^="}
UNSUPPORTED_KEYWORDS = {
    "program",
    "class",
    "union",
    "for",
    "while",
    "repeat",
    "forever",
    "specify",
    "primitive",
    "assert",
    "assume",
    "cover",
    "property",
    "covergroup",
}
SYSTEMVERILOG_UNSUPPORTED_KEYWORDS = {
    "program",
    "class",
    "union",
    "assert",
    "assume",
    "cover",
    "property",
    "covergroup",
}
UNSUPPORTED_END_KEYWORDS = {
    "program": "endprogram",
    "class": "endclass",
    "specify": "endspecify",
    "primitive": "endprimitive",
    "property": "endproperty",
    "covergroup": "endgroup",
}


@dataclass
class ParseResult:
    design: Design
    diagnostics: list[Diagnostic]


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.index = 0
        self.diagnostics: list[Diagnostic] = []
        self.interface_names: set[str] = set()
        self.typedef_names: set[str] = set()

    def parse(self) -> ParseResult:
        design = Design()
        while not self._at_eof():
            token = self._peek()
            if token.value == "module":
                module = self._parse_module()
                if module:
                    design.modules.append(module)
                continue
            if token.value == "package":
                self._parse_package()
                continue
            if token.value == "interface":
                self._parse_interface()
                continue
            if token.value == "import":
                self._parse_import_statement()
                continue
            if token.value in UNSUPPORTED_KEYWORDS:
                self._unsupported(token, f"暂不支持顶层构造 `{token.value}`。")
                self._skip_unsupported_construct(token.value)
                continue
            if token.kind != "eof":
                self._syntax_error(token, f"顶层只支持 module，当前出现 `{token.value}`。")
            self._advance()
        return ParseResult(design=design, diagnostics=self.diagnostics)

    def _parse_module(self) -> Module | None:
        module_token = self._expect_value("module")
        name_token = self._peek()
        if name_token.kind != "identifier":
            self._syntax_error(name_token, "module 后面需要模块名。")
            self._skip_until({"endmodule"})
            self._match_value("endmodule")
            return None
        self._advance()
        module = Module(name=name_token.value, span=name_token)

        if self._match_value("#"):
            if self._peek().value == "(":
                param_tokens = self._collect_balanced("(", ")")
                self._parse_parameter_header(param_tokens, module)
            else:
                self._syntax_error(self._peek(), "参数化模块的 # 后面需要括号。")

        if self._peek().value == "(":
            port_tokens = self._collect_balanced("(", ")")
            for signal in self._parse_port_header(port_tokens):
                if signal.name in module.ports:
                    self._syntax_error(signal.span, f"端口 `{signal.name}` 重复声明。")
                    continue
                module.ports[signal.name] = signal
                if signal.direction:
                    module.declarations.setdefault(signal.name, signal)
        if not self._expect_value(";"):
            self._skip_until({";", "endmodule"})
            self._match_value(";")

        body_start = self.index
        while not self._at_eof() and self._peek().value != "endmodule":
            self._parse_module_item(module)
        module.body_tokens = self.tokens[body_start:self.index]
        if not self._match_value("endmodule"):
            self._syntax_error(self._peek(), f"模块 `{module.name}` 缺少 endmodule。")
        return module

    def _parse_module_item(self, module: Module) -> None:
        token = self._peek()
        if token.value in DIRECTIONS or token.value in DATA_TYPES:
            decl_tokens = self._collect_until_semicolon()
            self._parse_declarations(decl_tokens, module)
            return
        if token.value == "typedef":
            self._parse_typedef()
            return
        if token.value == "import":
            self._parse_import_statement()
            return
        if token.value in {"parameter", "localparam"}:
            param_tokens = self._collect_until_semicolon()
            self._parse_parameters(param_tokens, module)
            return
        if token.value == "generate":
            module.generate_blocks.append(self._parse_generate_block(module))
            return
        if token.value == "function":
            function = self._parse_function()
            if function:
                if function.name in module.functions:
                    self._syntax_error(function.span, f"function `{function.name}` 重复声明。")
                else:
                    module.functions[function.name] = function
            return
        if token.value == "task":
            task = self._parse_task()
            if task:
                if task.name in module.tasks:
                    self._syntax_error(task.span, f"task `{task.name}` 重复声明。")
                else:
                    module.tasks[task.name] = task
            return
        if token.value == "assign":
            self._advance()
            assign_tokens = self._collect_until_semicolon()
            assignment = self._parse_assignment_tokens(assign_tokens, "continuous")
            if assignment:
                module.continuous_assigns.append(assignment)
            return
        if token.value in {"always", "always_comb", "always_ff", "always_latch"}:
            module.always_blocks.append(self._parse_always())
            return
        if token.value == "initial":
            self._unsupported(token, "initial 块不属于当前可综合 lint 子集。", severity="warning")
            self._advance()
            self._collect_statement_tokens()
            return
        if token.value in UNSUPPORTED_KEYWORDS:
            self._unsupported(token, f"暂不支持构造 `{token.value}`。")
            self._skip_unsupported_construct(token.value)
            return
        if self._looks_like_interface_instance():
            self._parse_interface_instance()
            return
        if self._looks_like_user_type_declaration():
            self._parse_user_type_declaration(module)
            return
        if self._looks_like_instance():
            instance = self._parse_instance()
            if instance:
                module.instances.append(instance)
            return
        if token.value in {";", ","}:
            self._advance()
            return
        self._syntax_error(token, f"模块项无法解析：`{token.value}`。")
        self._advance()

    def _parse_parameter_header(self, tokens: list[Token], module: Module) -> None:
        for segment in self._split_top_level(tokens, ","):
            signal = self._signal_from_decl_segment(segment, [], default_direction=None)
            if signal:
                module.parameters[signal.name] = signal

    def _parse_package(self) -> None:
        package_token = self._advance()
        name_token = self._peek()
        if name_token.kind != "identifier":
            self._syntax_error(name_token, "package 后面需要包名。")
        else:
            self._advance()
        if not self._expect_value(";"):
            self._skip_until({";", "endpackage"})
            self._match_value(";")
        while not self._at_eof() and self._peek().value != "endpackage":
            token = self._peek()
            if token.value == "typedef":
                self._parse_typedef()
                continue
            if token.value == "import":
                self._parse_import_statement()
                continue
            if token.value in {"parameter", "localparam"}:
                self._collect_until_semicolon()
                continue
            if token.value in DIRECTIONS or token.value in DATA_TYPES:
                self._collect_until_semicolon()
                continue
            if token.value in UNSUPPORTED_KEYWORDS:
                self._unsupported(token, f"package 内暂不支持 `{token.value}`。")
                self._skip_unsupported_construct(token.value)
                continue
            self._advance()
        if not self._match_value("endpackage"):
            self._syntax_error(package_token, "package 没有匹配的 endpackage。")
            return
        if self._peek().value == ":":
            self._advance()
            if self._peek().kind == "identifier":
                self._advance()

    def _parse_interface(self) -> None:
        interface_token = self._advance()
        name_token = self._peek()
        if name_token.kind != "identifier":
            self._syntax_error(name_token, "interface 后面需要接口名。")
        else:
            self.interface_names.add(name_token.value)
            self._advance()
        if self._peek().value == "(":
            self._collect_balanced("(", ")")
        if not self._expect_value(";"):
            self._skip_until({";", "endinterface"})
            self._match_value(";")
        while not self._at_eof() and self._peek().value != "endinterface":
            token = self._peek()
            if token.value == "modport":
                self._parse_modport()
                continue
            if token.value == "typedef":
                self._parse_typedef()
                continue
            if token.value in DIRECTIONS or token.value in DATA_TYPES:
                self._collect_until_semicolon()
                continue
            if token.value in UNSUPPORTED_KEYWORDS:
                self._unsupported(token, f"interface 内暂不支持 `{token.value}`。")
                self._skip_unsupported_construct(token.value)
                continue
            self._advance()
        if not self._match_value("endinterface"):
            self._syntax_error(interface_token, "interface 没有匹配的 endinterface。")
            return
        if self._peek().value == ":":
            self._advance()
            if self._peek().kind == "identifier":
                self._advance()

    def _parse_modport(self) -> None:
        modport_token = self._advance()
        name_token = self._peek()
        if name_token.kind != "identifier":
            self._syntax_error(name_token, "modport 后面需要名称。")
            self._skip_until({";"})
            self._match_value(";")
            return
        self._advance()
        if self._peek().value == "(":
            self._collect_balanced("(", ")")
        else:
            self._syntax_error(self._peek(), "modport 需要端口列表括号。")
        if not self._expect_value(";"):
            self._skip_until({";", "endinterface"})
            self._match_value(";")

    def _parse_import_statement(self) -> None:
        import_token = self._advance()
        if self._peek().kind != "identifier":
            self._syntax_error(self._peek(), "import 后面需要 package 名称。")
            self._skip_until({";"})
            self._match_value(";")
            return
        self._advance()
        if not self._match_value("::"):
            self._syntax_error(import_token, "import 语句需要 `::`。")
        if self._peek().value == "*":
            self._advance()
        elif self._peek().kind == "identifier":
            self._advance()
        else:
            self._syntax_error(self._peek(), "import 语句需要 `*` 或符号名。")
        if not self._expect_value(";"):
            self._skip_until({";", "module", "endmodule"})
            self._match_value(";")

    def _parse_typedef(self) -> None:
        typedef_token = self._advance()
        tokens = self._collect_until_semicolon()
        if not tokens:
            self._syntax_error(typedef_token, "typedef 缺少类型和名称。")
            return
        self._validate_typedef_tokens(tokens, typedef_token)
        self._validate_expression_balance(tokens, typedef_token, "typedef")
        candidates = [token for token in tokens if token.kind == "identifier" and token.value not in KEYWORDS]
        if candidates:
            self.typedef_names.add(candidates[-1].value)

    def _parse_user_type_declaration(self, module: Module) -> None:
        type_token = self._advance()
        name_token = self._peek()
        if name_token.kind != "identifier":
            self._syntax_error(name_token, "用户类型声明缺少变量名。")
            self._skip_until({";"})
            self._match_value(";")
            return
        self._advance()
        tokens = [type_token, name_token] + self._collect_until_semicolon()
        self._validate_range_groups(tokens)
        signal = Signal(name=name_token.value, direction=None, data_type=type_token.value, width=self._first_range_text(tokens), span=name_token)
        if signal.name in module.declarations:
            self._syntax_error(signal.span, f"信号 `{signal.name}` 重复声明。")
            return
        module.declarations[signal.name] = signal

    def _parse_interface_instance(self) -> None:
        self._advance()
        if self._peek().value == ".":
            self._advance()
            if self._peek().kind == "identifier":
                self._advance()
            else:
                self._syntax_error(self._peek(), "interface modport 实例缺少 modport 名。")
        if self._peek().kind != "identifier":
            self._syntax_error(self._peek(), "interface 实例缺少实例名。")
            self._skip_until({";"})
            self._match_value(";")
            return
        self._advance()
        if self._peek().value == "(":
            self._collect_balanced("(", ")")
        if not self._expect_value(";"):
            self._skip_until({";", "endmodule"})
            self._match_value(";")

    def _parse_generate_block(self, module: Module) -> GenerateBlock:
        generate_token = self._advance()
        body_tokens = self._collect_until_end_keyword("generate", "endgenerate", generate_token)
        self._validate_generate_tokens(body_tokens, generate_token)
        assignments: list[Assignment] = []
        instances: list[Instance] = []
        index = 0
        while index < len(body_tokens):
            token = body_tokens[index]
            if token.value == "assign":
                statement, next_index = self._statement_from_tokens(body_tokens, index + 1)
                assignment = self._parse_assignment_tokens(statement, "generate")
                if assignment:
                    assignments.append(assignment)
                    module.continuous_assigns.append(assignment)
                index = next_index
                continue
            if token.kind == "identifier":
                instance, next_index = self._parse_instance_from_tokens(body_tokens, index)
                if instance:
                    instances.append(instance)
                    module.instances.append(instance)
                    index = next_index
                    continue
            index += 1
        return GenerateBlock(
            kind=self._classify_generate_block(body_tokens),
            name=self._first_named_block(body_tokens),
            body_tokens=body_tokens,
            assignments=assignments,
            instances=instances,
            span=generate_token,
        )

    def _parse_function(self) -> FunctionDecl | None:
        function_token = self._advance()
        header = self._collect_until_semicolon()
        name_token = self._function_task_name_token(header, "function")
        body_tokens = self._collect_until_end_keyword("function", "endfunction", function_token)
        self._validate_function_task_body(body_tokens, "function")
        if name_token is None:
            self._syntax_error(function_token, "function 声明缺少函数名。")
            return None
        assignments = self._scan_procedural_assignments(body_tokens, context=f"function:{name_token.value}")
        return FunctionDecl(
            name=name_token.value,
            automatic=any(token.value == "automatic" for token in header),
            body_tokens=body_tokens,
            assignments=assignments,
            span=name_token,
        )

    def _parse_task(self) -> TaskDecl | None:
        task_token = self._advance()
        header = self._collect_until_semicolon()
        name_token = self._function_task_name_token(header, "task")
        body_tokens = self._collect_until_end_keyword("task", "endtask", task_token)
        self._validate_function_task_body(body_tokens, "task")
        if name_token is None:
            self._syntax_error(task_token, "task 声明缺少任务名。")
            return None
        assignments = self._scan_procedural_assignments(body_tokens, context=f"task:{name_token.value}")
        return TaskDecl(
            name=name_token.value,
            automatic=any(token.value == "automatic" for token in header),
            body_tokens=body_tokens,
            assignments=assignments,
            span=name_token,
        )

    def _function_task_name_token(self, header: list[Token], construct: str) -> Token | None:
        candidates = [token for token in header if token.kind == "identifier" and token.value not in KEYWORDS]
        if not candidates:
            return None
        if construct == "function":
            return candidates[-1]
        return candidates[0]

    def _validate_function_task_body(self, tokens: list[Token], construct: str) -> None:
        for index, token in enumerate(tokens):
            if token.value in DIRECTIONS:
                next_token = tokens[index + 1] if index + 1 < len(tokens) else token
                if next_token.value == ";":
                    self._syntax_error(token, f"{construct} 参数方向 `{token.value}` 后面缺少参数名。")
            if token.value in {"function", "task", "generate", "specify", "primitive"}:
                self._unsupported(token, f"{construct} 内暂不支持嵌套 `{token.value}`。")

    def _collect_until_end_keyword(self, start_keyword: str, end_keyword: str, start_token: Token) -> list[Token]:
        tokens: list[Token] = []
        depth = 1
        while not self._at_eof():
            token = self._peek()
            if token.value == end_keyword:
                self._advance()
                depth -= 1
                if depth == 0:
                    return tokens
                tokens.append(token)
                continue
            if token.value == start_keyword:
                depth += 1
            if token.value == "endmodule" and depth > 0:
                self._syntax_error(start_token, f"`{start_keyword}` 没有匹配的 `{end_keyword}`。")
                return tokens
            tokens.append(self._advance())
        self._syntax_error(start_token, f"`{start_keyword}` 没有匹配的 `{end_keyword}`。")
        return tokens

    def _validate_generate_tokens(self, tokens: list[Token], span: Token) -> None:
        self._validate_expression_balance(tokens, span, "generate")
        begin_stack: list[Token] = []
        case_stack: list[Token] = []
        for index, token in enumerate(tokens):
            if token.value == "begin":
                begin_stack.append(token)
            elif token.value == "end":
                if begin_stack:
                    begin_stack.pop()
                else:
                    self._syntax_error(token, "generate 中出现没有匹配 begin 的 end。")
            elif token.value in {"case", "casez", "casex"}:
                self._validate_control_condition(tokens, index, token.value)
                case_stack.append(token)
            elif token.value == "endcase":
                if case_stack:
                    case_stack.pop()
                else:
                    self._syntax_error(token, "generate 中出现没有匹配 case 的 endcase。")
            elif token.value in {"if", "for"}:
                self._validate_control_condition(tokens, index, token.value)
        if begin_stack:
            self._syntax_error(begin_stack[-1], "generate 命名块 begin 没有匹配的 end。")
        if case_stack:
            self._syntax_error(case_stack[-1], "generate case 缺少 endcase。")

    def _classify_generate_block(self, tokens: list[Token]) -> str:
        values = {token.value for token in tokens}
        if "for" in values:
            return "for"
        if values.intersection({"case", "casez", "casex"}):
            return "case"
        if "if" in values:
            return "if"
        return "block"

    def _first_named_block(self, tokens: list[Token]) -> str | None:
        for index, token in enumerate(tokens[:-2]):
            if token.value == "begin" and tokens[index + 1].value == ":" and tokens[index + 2].kind == "identifier":
                return tokens[index + 2].value
        return None

    def _statement_from_tokens(self, tokens: list[Token], start_index: int) -> tuple[list[Token], int]:
        result: list[Token] = []
        depth = 0
        index = start_index
        while index < len(tokens):
            token = tokens[index]
            if token.value in {"(", "[", "{"}:
                depth += 1
            elif token.value in {")", "]", "}"}:
                depth = max(0, depth - 1)
            if depth == 0 and token.value == ";":
                return result, index + 1
            result.append(token)
            index += 1
        return result, index

    def _parse_instance_from_tokens(self, tokens: list[Token], start_index: int) -> tuple[Instance | None, int]:
        module_type = tokens[start_index]
        index = start_index + 1
        if index < len(tokens) and tokens[index].value == "#":
            index += 1
            if index < len(tokens) and tokens[index].value == "(":
                _, close_index = self._balanced_group_from_tokens(tokens, index, "(", ")")
                if close_index is None:
                    return None, start_index + 1
                index = close_index + 1
        if index >= len(tokens) or tokens[index].kind != "identifier":
            return None, start_index + 1
        instance_token = tokens[index]
        index += 1
        if index >= len(tokens) or tokens[index].value != "(":
            return None, start_index + 1
        connection_tokens, close_index = self._balanced_group_from_tokens(tokens, index, "(", ")")
        if close_index is None:
            return None, start_index + 1
        end_index = close_index + 1
        if end_index < len(tokens) and tokens[end_index].value == ";":
            end_index += 1
        self._validate_instance_connections(connection_tokens)
        return Instance(module_type.value, instance_token.value, connection_tokens, module_type), end_index

    def _parse_port_header(self, tokens: list[Token]) -> list[Signal]:
        ports: list[Signal] = []
        prefix: list[Token] = []
        for segment in self._split_top_level(tokens, ","):
            if not segment:
                continue
            combined = segment
            if any(token.value in DECL_KEYWORDS for token in segment):
                prefix = self._prefix_before_decl_name(segment)
            elif prefix:
                combined = prefix + segment
            signal = self._signal_from_decl_segment(combined, [], default_direction=None)
            if signal:
                ports.append(signal)
        return ports

    def _parse_declarations(self, tokens: list[Token], module: Module) -> None:
        self._validate_declaration_tokens(tokens)
        prefix: list[Token] = []
        for segment in self._split_top_level(tokens, ","):
            if not segment:
                continue
            combined = segment
            if any(token.value in DECL_KEYWORDS for token in segment):
                prefix = self._prefix_before_decl_name(segment)
            elif prefix:
                combined = prefix + segment
            signal = self._signal_from_decl_segment(combined, [], default_direction=None)
            if not signal:
                self._syntax_error(segment[0], "无法解析信号声明。")
                continue
            if signal.name in module.declarations:
                self._syntax_error(signal.span, f"信号 `{signal.name}` 重复声明。")
                continue
            if signal.direction:
                module.ports[signal.name] = signal
            module.declarations[signal.name] = signal
            assignment = self._declaration_initializer(signal.name, combined, signal.span)
            if assignment:
                module.continuous_assigns.append(assignment)

    def _parse_parameters(self, tokens: list[Token], module: Module) -> None:
        for segment in self._split_top_level(tokens, ","):
            op_index = self._find_assignment_operator(segment)
            if op_index is not None:
                self._validate_expression(segment[op_index + 1 :], segment[op_index])
            signal = self._signal_from_decl_segment(segment, [], default_direction=None)
            if signal:
                module.parameters[signal.name] = signal

    def _parse_assignment_tokens(self, tokens: list[Token], context: str) -> Assignment | None:
        op_index = self._find_assignment_operator(tokens)
        if op_index is None:
            if tokens:
                self._syntax_error(tokens[0], "assign 语句缺少赋值操作符。")
            return None
        target = self._last_identifier(tokens[:op_index])
        if target is None:
            self._syntax_error(tokens[0], "赋值语句左侧缺少目标信号。")
            return None
        expr_tokens = tokens[op_index + 1 :]
        self._validate_expression(expr_tokens, tokens[op_index])
        return Assignment(
            target=target.value,
            op=tokens[op_index].value,
            expr_tokens=expr_tokens,
            span=target,
            context=context,
        )

    def _parse_always(self) -> AlwaysBlock:
        always_token = self._advance()
        sensitivity_tokens: list[Token] = []
        if self._match_value("@"):
            if self._peek().value == "(":
                sensitivity_tokens = self._collect_balanced("(", ")")
            elif not self._at_eof():
                sensitivity_tokens = [self._advance()]
        self._validate_event_control(always_token, sensitivity_tokens)
        body_tokens = self._collect_statement_tokens()
        for token in body_tokens:
            if token.value in UNSUPPORTED_KEYWORDS:
                self._unsupported(token, f"always 块内暂不支持 `{token.value}`。")
        self._validate_procedural_controls(body_tokens)
        assignments = self._scan_procedural_assignments(body_tokens, context=f"always:{always_token.line}")
        return AlwaysBlock(
            kind=always_token.value,
            sensitivity_tokens=sensitivity_tokens,
            body_tokens=body_tokens,
            assignments=assignments,
            span=always_token,
        )

    def _parse_instance(self) -> Instance | None:
        module_type = self._advance()
        if self._match_value("#") and self._peek().value == "(":
            self._collect_balanced("(", ")")
        instance_token = self._peek()
        if instance_token.kind != "identifier":
            self._syntax_error(instance_token, "模块例化缺少实例名。")
            self._skip_until({";"})
            self._match_value(";")
            return None
        self._advance()
        connection_tokens: list[Token] = []
        if self._peek().value == "(":
            connection_tokens = self._collect_balanced("(", ")")
            self._validate_instance_connections(connection_tokens)
        else:
            self._syntax_error(self._peek(), "模块例化缺少端口连接括号。")
        if not self._expect_value(";"):
            self._skip_until({";", "endmodule"})
            self._match_value(";")
        return Instance(module_type.value, instance_token.value, connection_tokens, module_type)

    def _scan_procedural_assignments(self, tokens: list[Token], context: str) -> list[Assignment]:
        assignments: list[Assignment] = []
        for index, token in enumerate(tokens):
            if token.value not in ASSIGN_OPS:
                continue
            if token.value == "=" and index > 0 and tokens[index - 1].value == "<":
                self._syntax_error(tokens[index - 1], "非阻塞赋值操作符应写成 `<=`，不能拆成 `< =`。")
                continue
            if token.value in {"=", "<="} and self._is_condition_operator(tokens, index):
                continue
            target = self._last_identifier(tokens[:index])
            if target is None:
                continue
            expr_tokens, saw_semicolon, terminator = self._tokens_until_statement_end(tokens[index + 1 :])
            if not saw_semicolon:
                where = terminator or (expr_tokens[-1] if expr_tokens else token)
                self._syntax_error(where, f"赋值语句 `{target.value}` 缺少结尾分号。")
            self._validate_expression(expr_tokens, token)
            assignments.append(Assignment(target.value, token.value, expr_tokens, target, context))
        return assignments

    def _declaration_initializer(self, name: str, tokens: list[Token], span: Token) -> Assignment | None:
        op_index = self._find_assignment_operator(tokens)
        if op_index is None:
            return None
        expr_tokens = tokens[op_index + 1 :]
        self._validate_expression(expr_tokens, tokens[op_index])
        return Assignment(name, "=", expr_tokens, span, "declaration")

    def _signal_from_decl_segment(self, segment: list[Token], prefix: list[Token], default_direction: str | None) -> Signal | None:
        tokens = prefix + segment
        if not tokens:
            return None
        self._validate_range_groups(tokens)
        direction = default_direction
        data_type = None
        direction_tokens = [token for token in tokens if token.value in DIRECTIONS]
        if len(direction_tokens) > 1:
            self._syntax_error(direction_tokens[1], "同一端口/信号声明片段出现多个方向关键字，可能缺少逗号或分号。")
        data_type_tokens = [token for token in tokens if token.value in DATA_TYPES]
        if len(data_type_tokens) > 1:
            self._syntax_error(data_type_tokens[1], "同一声明片段出现多个 net/reg/data type 关键字。")
        for token in tokens:
            if token.value in DIRECTIONS:
                direction = token.value
            if token.value in DATA_TYPES:
                data_type = token.value
        width = self._first_range_text(tokens)
        before_assign = tokens[: self._find_assignment_operator(tokens) or len(tokens)]
        filtered = self._remove_bracket_groups(before_assign)
        candidates = [token for token in filtered if token.kind == "identifier" and token.value not in KEYWORDS]
        if not candidates:
            return None
        name_token = candidates[-1]
        signedness = "signed" if any(token.value == "signed" for token in tokens) else "unsigned"
        assign_index = self._find_assignment_operator(tokens)
        value = " ".join(token.value for token in tokens[assign_index + 1 :]) if assign_index is not None else None
        return Signal(
            name=name_token.value,
            direction=direction,
            data_type=data_type,
            width=width,
            signedness=signedness,
            value=value,
            span=name_token,
        )

    def _prefix_before_decl_name(self, tokens: list[Token]) -> list[Token]:
        before_assign = tokens[: self._find_assignment_operator(tokens) or len(tokens)]
        filtered = self._remove_bracket_groups(before_assign)
        for token in reversed(filtered):
            if token.kind == "identifier" and token.value not in KEYWORDS:
                position = tokens.index(token)
                return tokens[:position]
        return []

    def _first_range_text(self, tokens: list[Token]) -> str | None:
        for index, token in enumerate(tokens):
            if token.value == "[":
                depth = 1
                values = [token.value]
                cursor = index + 1
                while cursor < len(tokens) and depth:
                    values.append(tokens[cursor].value)
                    if tokens[cursor].value == "[":
                        depth += 1
                    elif tokens[cursor].value == "]":
                        depth -= 1
                    cursor += 1
                return "".join(values)
        return None

    def _validate_declaration_tokens(self, tokens: list[Token]) -> None:
        for token in tokens[1:]:
            if token.value in {"assign", "always", "always_comb", "always_ff", "always_latch", "module", "endmodule"}:
                self._syntax_error(token, f"声明语句中出现 `{token.value}`，前一条声明可能缺少分号。")
                return

    def _validate_range_groups(self, tokens: list[Token]) -> None:
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if token.value != "[":
                index += 1
                continue
            inner, close_index = self._balanced_group_from_tokens(tokens, index, "[", "]")
            if close_index is None:
                self._syntax_error(token, "向量范围缺少右中括号。")
                return
            colon_positions = [pos for pos, inner_token in enumerate(inner) if inner_token.value == ":"]
            if len(colon_positions) == 1:
                pos = colon_positions[0]
                if pos == 0 or pos == len(inner) - 1:
                    self._syntax_error(inner[pos], "向量范围冒号两侧都需要表达式。")
                    return
            elif len(colon_positions) > 1:
                self._syntax_error(inner[colon_positions[1]], "向量范围中出现多个冒号。")
                return
            index = close_index + 1

    def _remove_bracket_groups(self, tokens: list[Token]) -> list[Token]:
        result: list[Token] = []
        depth = 0
        for token in tokens:
            if token.value == "[":
                depth += 1
                continue
            if token.value == "]":
                depth = max(0, depth - 1)
                continue
            if depth == 0:
                result.append(token)
        return result

    def _validate_expression(self, tokens: list[Token], span: Token) -> None:
        meaningful = [token for token in tokens if token.value != ","]
        if not meaningful:
            self._syntax_error(span, "表达式为空。")
            return
        if meaningful[-1].kind == "operator" and meaningful[-1].value not in {")", "]", "}"}:
            self._syntax_error(meaningful[-1], "表达式不能以操作符结束。")
        pairs = {"(": ")", "[": "]", "{": "}"}
        stack: list[Token] = []
        pending_ternary: list[Token] = []
        for index, token in enumerate(meaningful):
            if token.value == "inside":
                self._unsupported(token, "表达式操作符 `inside` 当前不支持。")
                return
            if token.value == "@":
                self._syntax_error(token, "表达式中出现非法事件控制符 `@`。")
                return
            if token.value == ".":
                prev_ok = index > 0 and meaningful[index - 1].kind == "identifier"
                next_ok = index + 1 < len(meaningful) and meaningful[index + 1].kind == "identifier"
                if not prev_ok or not next_ok:
                    self._syntax_error(token, "层级引用 `.` 两侧都需要标识符。")
                    return
            if token.value in pairs:
                stack.append(token)
            elif token.value in pairs.values():
                if not stack or pairs[stack[-1].value] != token.value:
                    self._syntax_error(token, "表达式括号不匹配。")
                    return
                stack.pop()
            elif token.value == "?" and not any(open_token.value == "[" for open_token in stack):
                pending_ternary.append(token)
            elif token.value == ":" and not any(open_token.value == "[" for open_token in stack):
                if pending_ternary:
                    pending_ternary.pop()
                else:
                    self._syntax_error(token, "三目表达式冒号缺少匹配的问号。")
                    return
        if stack:
            self._syntax_error(stack[-1], "表达式括号没有闭合。")
            return
        if pending_ternary:
            self._syntax_error(pending_ternary[-1], "三目表达式缺少冒号或假值分支。")
            return
        self._validate_part_selects(meaningful)

    def _validate_part_selects(self, tokens: list[Token]) -> None:
        index = 0
        while index < len(tokens):
            if tokens[index].value != "[":
                index += 1
                continue
            inner, close_index = self._balanced_group_from_tokens(tokens, index, "[", "]")
            if close_index is None:
                self._syntax_error(tokens[index], "位选择或 part-select 缺少右中括号。")
                return
            colon_positions = [pos for pos, token in enumerate(inner) if token.value == ":"]
            if len(colon_positions) == 1:
                pos = colon_positions[0]
                if pos == 0 or pos == len(inner) - 1:
                    self._syntax_error(inner[pos], "part-select 冒号两侧都需要表达式。")
                    return
            elif len(colon_positions) > 1:
                self._syntax_error(inner[colon_positions[1]], "part-select 中出现多个冒号。")
                return
            index = close_index + 1

    def _validate_expression_balance(self, tokens: list[Token], span: Token, construct: str) -> None:
        pairs = {"(": ")", "[": "]", "{": "}"}
        stack: list[Token] = []
        for token in tokens:
            if token.value in pairs:
                stack.append(token)
            elif token.value in pairs.values():
                if not stack or pairs[stack[-1].value] != token.value:
                    self._syntax_error(token, f"{construct} 中括号不匹配。")
                    return
                stack.pop()
        if stack:
            self._syntax_error(stack[-1], f"{construct} 中括号没有闭合。")

    def _validate_typedef_tokens(self, tokens: list[Token], span: Token) -> None:
        for token in tokens:
            if token.value in {"assign", "always", "always_comb", "always_ff", "always_latch", "module", "endmodule"}:
                self._syntax_error(token, "typedef 声明缺少分号，后续语句被并入 typedef。")
                return
        candidates = [token for token in tokens if token.kind == "identifier" and token.value not in KEYWORDS]
        if not candidates:
            self._syntax_error(span, "typedef 缺少类型别名名称。")

    def _is_condition_operator(self, tokens: list[Token], index: int) -> bool:
        if index < 2:
            return False
        cursor = index - 1
        while cursor >= 0 and tokens[cursor].kind not in {"identifier", "number"}:
            cursor -= 1
        return cursor >= 1 and tokens[cursor - 1].value == "(" and any(token.value in {"if", "case"} for token in tokens[max(0, cursor - 4):cursor])

    def _tokens_until_statement_end(self, tokens: list[Token]) -> tuple[list[Token], bool, Token | None]:
        result: list[Token] = []
        depth = 0
        for token in tokens:
            if token.value in {"(", "[", "{"}:
                depth += 1
            elif token.value in {")",
                "]",
                "}",
            }:
                depth = max(0, depth - 1)
            if depth == 0 and token.value == ";":
                return result, True, token
            if depth == 0 and token.value in {"end", "else", "endcase", "endmodule"}:
                return result, False, token
            result.append(token)
        return result, False, None

    def _find_assignment_operator(self, tokens: list[Token]) -> int | None:
        depth = 0
        for index, token in enumerate(tokens):
            if token.value in {"(", "[", "{"}:
                depth += 1
            elif token.value in {")", "]", "}"}:
                depth = max(0, depth - 1)
            if depth == 0 and token.value in ASSIGN_OPS:
                return index
        return None

    def _last_identifier(self, tokens: list[Token]) -> Token | None:
        for token in reversed(tokens):
            if token.kind == "identifier" and token.value not in KEYWORDS:
                return token
        return None

    def _looks_like_instance(self) -> bool:
        first = self._peek()
        second = self._peek(1)
        third = self._peek(2)
        if first.kind != "identifier":
            return False
        if second.value == "#":
            return self._peek(3).kind == "identifier"
        return second.kind == "identifier" and third.value == "("

    def _looks_like_interface_instance(self) -> bool:
        first = self._peek()
        if first.kind != "identifier" or first.value not in self.interface_names:
            return False
        if self._peek(1).value == ".":
            return self._peek(2).kind == "identifier" and self._peek(3).kind == "identifier"
        return self._peek(1).kind == "identifier"

    def _looks_like_user_type_declaration(self) -> bool:
        first = self._peek()
        second = self._peek(1)
        third = self._peek(2)
        if first.kind != "identifier" or second.kind != "identifier":
            return False
        if first.value in self.interface_names:
            return False
        if first.value in self.typedef_names:
            return True
        return third.value in {";", "[", "="}

    def _split_top_level(self, tokens: list[Token], separator: str) -> list[list[Token]]:
        parts: list[list[Token]] = []
        current: list[Token] = []
        depth = 0
        for token in tokens:
            if token.value in {"(", "[", "{"}:
                depth += 1
            elif token.value in {")", "]", "}"}:
                depth = max(0, depth - 1)
            if depth == 0 and token.value == separator:
                parts.append(current)
                current = []
            else:
                current.append(token)
        parts.append(current)
        return parts

    def _collect_until_semicolon(self) -> list[Token]:
        tokens: list[Token] = []
        depth = 0
        while not self._at_eof():
            token = self._peek()
            if depth == 0 and token.value == ";":
                self._advance()
                return tokens
            if token.value in {"(", "[", "{"}:
                depth += 1
            elif token.value in {")", "]", "}"}:
                depth = max(0, depth - 1)
            if depth == 0 and token.value in {"endmodule", "end"}:
                self._syntax_error(token, "语句缺少分号。")
                return tokens
            tokens.append(self._advance())
        self._syntax_error(self._peek(), "文件结束前语句缺少分号。")
        return tokens

    def _collect_statement_tokens(self) -> list[Token]:
        if self._peek().value == "begin":
            return self._collect_begin_end()
        if self._peek().value in {"if", "case", "casez", "casex"}:
            return self._collect_compound_statement()
        return self._collect_until_semicolon()

    def _collect_begin_end(self) -> list[Token]:
        tokens: list[Token] = []
        depth = 0
        while not self._at_eof():
            token = self._advance()
            tokens.append(token)
            if token.value == "begin":
                depth += 1
            elif token.value == "end":
                depth -= 1
                if depth == 0:
                    return tokens
        self._syntax_error(tokens[0] if tokens else self._peek(), "begin 没有匹配的 end。")
        return tokens

    def _collect_compound_statement(self) -> list[Token]:
        tokens: list[Token] = []
        depth_begin = 0
        depth_case = 0
        while not self._at_eof():
            token = self._advance()
            tokens.append(token)
            if token.value == "begin":
                depth_begin += 1
            elif token.value == "end":
                depth_begin = max(0, depth_begin - 1)
                if depth_begin == 0 and depth_case == 0:
                    return tokens
            elif token.value in {"case", "casez", "casex"}:
                depth_case += 1
            elif token.value == "endcase":
                depth_case = max(0, depth_case - 1)
                if depth_begin == 0 and depth_case == 0:
                    return tokens
            elif token.value == ";" and depth_begin == 0 and depth_case == 0:
                if self._peek().value != "else":
                    return tokens
        self._syntax_error(tokens[0] if tokens else self._peek(), "复合语句没有正确结束。")
        return tokens

    def _collect_balanced(self, open_value: str, close_value: str) -> list[Token]:
        if not self._expect_value(open_value):
            return []
        tokens: list[Token] = []
        depth = 1
        while not self._at_eof():
            token = self._advance()
            if token.value == open_value:
                depth += 1
            elif token.value == close_value:
                depth -= 1
                if depth == 0:
                    return tokens
            tokens.append(token)
        self._syntax_error(tokens[0] if tokens else self._peek(), f"`{open_value}` 没有匹配的 `{close_value}`。")
        return tokens

    def _balanced_group_from_tokens(
        self,
        tokens: list[Token],
        open_index: int,
        open_value: str,
        close_value: str,
    ) -> tuple[list[Token], int | None]:
        if open_index >= len(tokens) or tokens[open_index].value != open_value:
            return [], None
        depth = 1
        inner: list[Token] = []
        cursor = open_index + 1
        while cursor < len(tokens):
            token = tokens[cursor]
            if token.value == open_value:
                depth += 1
            elif token.value == close_value:
                depth -= 1
                if depth == 0:
                    return inner, cursor
            inner.append(token)
            cursor += 1
        return inner, None

    def _validate_instance_connections(self, tokens: list[Token]) -> None:
        has_named = False
        has_positional = False
        for segment in self._split_top_level(tokens, ","):
            if not segment:
                continue
            if segment[0].value == ".":
                has_named = True
            else:
                has_positional = True
        if has_named and has_positional:
            token = tokens[0] if tokens else self._peek()
            self._syntax_error(token, "同一个模块例化中不能混用命名端口连接和位置端口连接。")

    def _validate_event_control(self, always_token: Token, tokens: list[Token]) -> None:
        if always_token.value == "always_ff":
            has_edge_event = False
            for index, token in enumerate(tokens):
                if token.value not in {"posedge", "negedge"}:
                    continue
                if index + 1 < len(tokens) and tokens[index + 1].kind == "identifier":
                    has_edge_event = True
                else:
                    self._syntax_error(token, "边沿事件控制缺少信号名。")
            if not has_edge_event:
                self._syntax_error(always_token, "always_ff 需要明确的 posedge/negedge 事件控制。")
            return
        for index, token in enumerate(tokens):
            if token.value in {"posedge", "negedge"} and (index + 1 >= len(tokens) or tokens[index + 1].kind != "identifier"):
                self._syntax_error(token, "边沿事件控制缺少信号名。")

    def _validate_procedural_controls(self, tokens: list[Token]) -> None:
        case_stack: list[Token] = []
        for index, token in enumerate(tokens):
            if token.value == "if":
                self._validate_control_condition(tokens, index, "if")
            elif token.value in {"case", "casez", "casex"}:
                self._validate_control_condition(tokens, index, token.value)
                case_stack.append(token)
            elif token.value == "endcase" and case_stack:
                case_stack.pop()
        for token in case_stack:
            self._syntax_error(token, "case 语句缺少 endcase。")

    def _validate_control_condition(self, tokens: list[Token], keyword_index: int, keyword: str) -> None:
        if keyword_index + 1 >= len(tokens) or tokens[keyword_index + 1].value != "(":
            self._syntax_error(tokens[keyword_index], f"`{keyword}` 后面需要括号条件表达式。")
            return
        inner, close_index = self._balanced_group_from_tokens(tokens, keyword_index + 1, "(", ")")
        if close_index is None:
            self._syntax_error(tokens[keyword_index + 1], f"`{keyword}` 条件缺少右括号。")
            return
        if not inner:
            self._syntax_error(tokens[keyword_index + 1], f"`{keyword}` 条件表达式为空。")

    def _skip_until(self, values: set[str]) -> None:
        while not self._at_eof() and self._peek().value not in values:
            self._advance()

    def _skip_unsupported_construct(self, start_keyword: str) -> None:
        end_keyword = UNSUPPORTED_END_KEYWORDS.get(start_keyword)
        self._advance()
        if not end_keyword:
            self._skip_until({";", "endmodule"})
            self._match_value(";")
            return
        depth = 1
        while not self._at_eof():
            token = self._advance()
            if token.value == start_keyword:
                depth += 1
            elif token.value == end_keyword:
                depth -= 1
                if depth == 0:
                    return

    def _expect_value(self, value: str) -> Token | None:
        if self._peek().value == value:
            return self._advance()
        self._syntax_error(self._peek(), f"期望 `{value}`，实际为 `{self._peek().value}`。")
        return None

    def _match_value(self, value: str) -> bool:
        if self._peek().value == value:
            self._advance()
            return True
        return False

    def _peek(self, offset: int = 0) -> Token:
        position = min(self.index + offset, len(self.tokens) - 1)
        return self.tokens[position]

    def _advance(self) -> Token:
        token = self._peek()
        if self.index < len(self.tokens) - 1:
            self.index += 1
        return token

    def _at_eof(self) -> bool:
        return self._peek().kind == "eof"

    def _syntax_error(self, token: Token, message_zh: str) -> None:
        self.diagnostics.append(
            Diagnostic.make(
                severity="error",
                rule="SYNTAX001",
                category="syntax",
                file=token.file,
                line=token.line,
                column=token.column,
                message="syntax error",
                message_zh=f"语法错误：{message_zh}",
                suggestion_zh="请检查该位置附近的括号、分号、begin/end、case/endcase 或模块端口声明。",
                confidence="high",
            )
        )

    def _unsupported(self, token: Token, message_zh: str, severity: str = "warning") -> None:
        is_systemverilog = token.value in SYSTEMVERILOG_UNSUPPORTED_KEYWORDS or token.file.endswith(".sv")
        rule = "UNSUPPORTED_SYSTEMVERILOG" if is_systemverilog else "UNSUPPORTED_VERILOG"
        category = "unsupported_systemverilog" if is_systemverilog else "unsupported"
        prefix = "SystemVerilog 构造暂不支持" if is_systemverilog else "暂不支持"
        self.diagnostics.append(
            Diagnostic.make(
                severity="error" if is_systemverilog else severity,
                rule=rule,
                category=category,
                file=token.file,
                line=token.line,
                column=token.column,
                message=f"unsupported construct: {token.value}",
                message_zh=f"{prefix}：{message_zh}",
                suggestion_zh="当前版本会明确标记不支持的构造；请简化该 RTL 片段或等待后续解析能力扩展。",
                confidence="high",
            )
        )
