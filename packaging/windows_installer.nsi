Unicode True
!include "MUI2.nsh"

!ifndef APP_VERSION
  !define APP_VERSION "0.2.0"
!endif
!ifndef TARGET
  !define TARGET "window10"
!endif
!ifndef PAYLOAD_DIR
  !error "PAYLOAD_DIR 未定义"
!endif
!ifndef OUTPUT_DIR
  !error "OUTPUT_DIR 未定义"
!endif

!if "${TARGET}" == "window10"
  !define OS_LABEL "Windows10"
!else
  !define OS_LABEL "Windows11"
!endif

Name "STA-Lite ${APP_VERSION}"
OutFile "${OUTPUT_DIR}\STA-Lite-${APP_VERSION}-${OS_LABEL}-x64-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\STA-Lite"
InstallDirRegKey HKCU "Software\STA-Lite" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
BrandingText "STA-Lite RTL Review"

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\STA-Lite\STA-Lite.exe"
!define MUI_FINISHPAGE_RUN_TEXT "启动 STA-Lite"
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

Section "STA-Lite" SEC_MAIN
  SetOutPath "$INSTDIR"
  File /r "${PAYLOAD_DIR}\*"
  WriteRegStr HKCU "Software\STA-Lite" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\STA-Lite" "DisplayName" "STA-Lite"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\STA-Lite" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\STA-Lite" "Publisher" "STA-Lite Project"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\STA-Lite" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  CreateDirectory "$SMPROGRAMS\STA-Lite"
  CreateShortcut "$SMPROGRAMS\STA-Lite\STA-Lite.lnk" "$INSTDIR\STA-Lite\STA-Lite.exe"
  CreateShortcut "$SMPROGRAMS\STA-Lite\STA-Lite CLI.lnk" "$SYSDIR\cmd.exe" '/K ""$INSTDIR\sta-lite-cli\sta-lite-cli.exe" --help"' "$INSTDIR\sta-lite-cli\sta-lite-cli.exe"
  CreateShortcut "$SMPROGRAMS\STA-Lite\卸载 STA-Lite.lnk" "$INSTDIR\Uninstall.exe"
  CreateShortcut "$DESKTOP\STA-Lite.lnk" "$INSTDIR\STA-Lite\STA-Lite.exe"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\STA-Lite.lnk"
  RMDir /r "$SMPROGRAMS\STA-Lite"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "Software\STA-Lite"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\STA-Lite"
  ; 用户工作区 Documents\STA-Lite-Workspace 刻意保留。
SectionEnd
