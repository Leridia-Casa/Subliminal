; Script do Inno Setup para o Subliminal Pro.
; Como compilar:
;   1. Instale o Inno Setup (gratuito): https://jrsoftware.org/isdl.php
;   2. Rode "python build.py" primeiro, pra gerar dist\SubliminalPro.exe atualizado
;   3. Abra este arquivo (installer.iss) com o Inno Setup e clique em "Compile"
;      (ou, pelo terminal: "ISCC.exe installer.iss")
;   4. O instalador final sai em installer_output\SubliminalPro_Setup.exe

[Setup]
AppId={{1F96342B-EE8B-4D56-9486-362AFFB1EF19}
AppName=Subliminal Pro
AppVersion=1.0
AppPublisher=Subliminal Pro
DefaultDirName={localappdata}\SubliminalPro
DefaultGroupName=Subliminal Pro
UninstallDisplayIcon={app}\SubliminalPro.exe
OutputDir=installer_output
OutputBaseFilename=SubliminalPro_Setup
Compression=lzma
SolidCompression=yes
; Instala só pro usuário atual, sem precisar de permissão de administrador
; (evita problemas de escrita em Program Files, já que o app salva sua
; configuração e estatísticas na própria pasta onde está instalado).
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
SetupIconFile=icon.ico
WizardStyle=modern

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos adicionais:"

[Files]
Source: "dist\SubliminalPro.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Subliminal Pro"; Filename: "{app}\SubliminalPro.exe"
Name: "{group}\Desinstalar Subliminal Pro"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Subliminal Pro"; Filename: "{app}\SubliminalPro.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SubliminalPro.exe"; Description: "Abrir o Subliminal Pro agora"; Flags: nowait postinstall skipifsilent
