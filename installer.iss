[Setup]
AppName=NoorMarket
AppVersion=1.0
AppPublisher=Noor Market
AppPublisherURL=http://example.com
AppSupportURL=http://example.com/support
AppUpdatesURL=http://example.com/updates
DefaultDirName={commonpf}\NoorMarket
DefaultGroupName=NoorMarket
OutputBaseFilename=NoorMarketSetup
OutputDir=output
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\NoorMarket.exe
UninstallDisplayName=NoorMarket
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=no
CreateAppDir=yes
WizardStyle=modern
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
AllowNoIcons=yes
DisableDirPage=no

[Tasks]
Name: desktopicon; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Dirs]
Name: "{app}"; Permissions: users-modify

[Files]
Source: "dist\NoorMarket\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\NoorMarket"; Filename: "{app}\NoorMarket.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"
Name: "{group}\Uninstall NoorMarket"; Filename: "{uninstallexe}"
Name: "{commondesktop}\NoorMarket"; Filename: "{app}\NoorMarket.exe"; Tasks: desktopicon; IconFilename: "{app}\icon.ico"

[Run]
Filename: "{app}\NoorMarket.exe"; Description: "Launch NoorMarket"; Flags: nowait postinstall skipifsilent
