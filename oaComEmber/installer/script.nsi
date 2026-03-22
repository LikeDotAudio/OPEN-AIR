OutFile "EmberCSVInstaller.exe"

InstallDir $PROGRAMFILES64\EmberCSV

Section ; Install


; Add files

SetOutPath $INSTDIR
File ..\out\build\x64-release\EmberCSVService.exe
File sample_data.csv
File config.ini
WriteUninstaller $INSTDIR\uninstaller.exe


; Show Uninstaller in Registry

WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EmberCSV" \
                 "DisplayName" "EmberCSV"
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EmberCSV" \
                 "UninstallString" "$\"$INSTDIR\uninstaller.exe$\""


; Installing the Service

SimpleSC::InstallService "EmberCSVService" EmberCSVService 16 2 $INSTDIR\EmberCSVService.exe "" "" ""
Pop $0

StrCmp "$0" "0" +3 0
    MessageBox MB_OK "Error while creating service: $0. Ensure that the service doesn't already exist."
    Quit

SimpleSC::SetServiceFailure "EmberCSVService" "0" "" "" "1" "60000" "1" "60000" "1" "60000"


; Starting the Service

SimpleSC::StartService "EmberCSVService" "" 10
Pop $0

StrCmp "$0" "0" +3 0
    MessageBox MB_OK "Error while starting service: $0. You can try manually starting the service from windows services"
    Quit

SectionEnd

Section "Uninstall" ; Uninstall


; Stopping the Service

SimpleSC::StopService "EmberCSVService" 2 20
Pop $0

StrCmp "$0" "0" +4 0
    StrCmp "$0" "1062" +3 0 ; The service has already stopped
    MessageBox MB_OK "Error while stopping service: $0"
    Quit


; Delete the Service

SimpleSC::RemoveService "EmberCSVService"
Pop $0

StrCmp "$0" "0" +3 0
    MessageBox MB_OK "Error while removing service: $0"
    Quit


; Delete Files

Delete $INSTDIR\EmberCSV.exe
Delete $INSTDIR\sample_data.csv
Delete $INSTDIR\config.ini
Delete $INSTDIR\uninstaller.exe
RMDir $INSTDIR\ember-csv-logs ; This will only delete when empty
RMDir $INSTDIR

DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EmberCSV"

SectionEnd