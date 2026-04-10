; MetaTag Installer Script (NSIS)
; Compile with: makensis installer.nsi

Unicode true
Name "MetaTag"
OutFile "dist\MetaTag-Installer.exe"
InstallDir "$PROGRAMFILES\MetaTag"
RequestExecutionLevel admin

!include "MUI2.nsh"

; Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "img\logo.ico"
!define MUI_UNICON "img\logo.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "MetaTag"
  SectionIn RO
  SetOutPath "$INSTDIR"
  
  ; Copy distribution files
  File "dist\MetaTag.exe"
  File "LICENSE"
  File "README.md"
  
  ; Create start menu shortcut
  CreateDirectory "$SMPROGRAMS\MetaTag"
  CreateShortcut "$SMPROGRAMS\MetaTag\MetaTag.lnk" "$INSTDIR\MetaTag.exe"
  CreateShortcut "$SMPROGRAMS\MetaTag\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  
  ; Create desktop shortcut (optional)
  ; CreateShortcut "$DESKTOP\MetaTag.lnk" "$INSTDIR\MetaTag.exe"
  
  ; Write uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; Write registry keys for uninstaller
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetaTag" \
                   "DisplayName" "MetaTag"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetaTag" \
                   "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetaTag" \
                   "DisplayIcon" "$INSTDIR\MetaTag.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetaTag" \
                   "Publisher" "MetaTag"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetaTag" \
                   "DisplayVersion" "1.2.0"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetaTag" \
                     "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetaTag" \
                     "NoRepair" 1
SectionEnd

Section "Uninstall"
  ; Remove shortcuts
  Delete "$SMPROGRAMS\MetaTag\MetaTag.lnk"
  Delete "$SMPROGRAMS\MetaTag\Uninstall.lnk"
  RMDir "$SMPROGRAMS\MetaTag"
  ; Delete "$DESKTOP\MetaTag.lnk"
  
  ; Remove installed files
  Delete "$INSTDIR\MetaTag.exe"
  Delete "$INSTDIR\LICENSE"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\MetaTag"
SectionEnd