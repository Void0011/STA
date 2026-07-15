# 宽 mux / 优先级编码器

该 case 用多级 `if/else` 描述选择网络。若不需要优先级，后续可改成明确的 `case/default` 或拆分 mux 层级，降低单周期选择链风险。
