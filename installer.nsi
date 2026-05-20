!define APP_NAME "CostPlus SolarDocs"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Cost Plus Inc."
!define APP_ICON "assets\icons\app_icon.ico"

InstallDir "$PROGRAMFILES64\${APP_NAME}"

Name "${APP_NAME}"
OutFile "CostPlusSolarDocs_Setup_1.0.0.exe"

Section "Install"
  SetOutPath $INSTDIR
  File /r "dist\CostPlusSolarDocs\*.*"
  CreateShortCut "$SMPROGRAMS\${APP_NAME}.lnk" "$INSTDIR\CostPlusSolarDocs.exe"
  CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\CostPlusSolarDocs.exe"
  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$SMPROGRAMS\${APP_NAME}.lnk"
  Delete "$DESKTOP\${APP_NAME}.lnk"
  RMDir /r "$INSTDIR"
SectionEnd
