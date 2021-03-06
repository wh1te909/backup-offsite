#define MyAppName "Tactical Backup"
#define MyAppVersion "1.3.0"
#define MyAppPublisher "Tactical Techs"
#define MyAppURL "https://github.com/wh1te909"
#define MyAppExeName "backupagent.exe"
#define AppId "{B2E71ABF-56CE-4606-9ADD-86118D95D095}"
#define SetupReg "Software\Microsoft\Windows\CurrentVersion\Uninstall\" + AppId + "_is1"
#define NSSM "nssm.exe"

[Setup]
AppId={#StringChange(AppId, '{', '{{')}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName="C:\Program Files\TacticalBackup"
DisableDirPage=yes
DisableProgramGroupPage=yes
OutputBaseFilename=backupagent-v{#MyAppVersion}
SetupIconFile=C:\Users\Public\Documents\pubsub\onit.ico
WizardSmallImageFile=C:\Users\Public\Documents\pubsub\bin\onit.bmp
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "C:\Users\Public\Documents\backupagent_go\backupagent.exe"; DestDir: "{app}"; Flags: ignoreversion; BeforeInstall: StopService;
Source: "C:\Users\Public\Documents\pubsub\bin\nssm.exe"; DestDir: "{app}";

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}";

[Run]
Filename: "{app}\{#NSSM}"; Parameters: "install backupagent ""{app}\{#MyAppExeName}""";
Filename: "{app}\{#NSSM}"; Parameters: "set backupagent DisplayName ""Tactical Backup""";
Filename: "{app}\{#NSSM}"; Parameters: "set backupagent Description ""Tactical Backup""";
Filename: "{app}\{#NSSM}"; Parameters: "set backupagent AppRestartDelay 5000";
Filename: "{app}\{#NSSM}"; Parameters: "start backupagent";

[UninstallRun]
Filename: "{app}\{#NSSM}"; Parameters: "stop backupagent"; RunOnceId: "stoptacbackup";
Filename: "{app}\{#NSSM}"; Parameters: "remove backupagent confirm"; RunOnceId: "removetacbackup";

[UninstallDelete]
Type: filesandordirs; Name: "{app}";

[Code]

procedure StopService();
var
  ResultCode: Integer;
  StopCmd: string;
begin
  StopCmd := ExpandConstant(' /c "{app}\{#NSSM}"' + ' stop backupagent && ping 127.0.0.1 -n 5');
  Exec('cmd.exe', StopCmd, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;