#define MyAppName "Tactical Backup"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Tactical Techs"
#define MyAppURL "https://github.com/wh1te909"
#define MyAppExeName "backupagent.exe"
#define NSSM "nssm.exe"

[Setup]
AppId={{B2E71ABF-56CE-4606-9ADD-86118D95D095}
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
Source: "C:\Users\Public\Documents\pubsub\dist\backupagent.exe"; DestDir: "{app}";
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
