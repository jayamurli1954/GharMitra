' ============================================
' GharMitra - Create Desktop Shortcut (VBScript)
' ============================================
' This VBScript creates a desktop shortcut for GharMitra
' Works on all Windows versions without PowerShell execution policy issues

Set WshShell = WScript.CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the script directory
ScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
StartScript = ScriptDir & "\START_GHARMITRA.bat"

' Check if START_GHARMITRA.bat exists
If Not fso.FileExists(StartScript) Then
    ' Try alternative name
    StartScript = ScriptDir & "\start_gharmitra.bat"
    If Not fso.FileExists(StartScript) Then
        MsgBox "ERROR: START_GHARMITRA.bat not found!" & vbCrLf & vbCrLf & "Expected: " & StartScript, vbCritical, "GharMitra - Error"
        WScript.Quit 1
    End If
End If

' Get desktop path
DesktopPath = WshShell.SpecialFolders("Desktop")
ShortcutPath = DesktopPath & "\GharMitra.lnk"

' Create shortcut
Set Shortcut = WshShell.CreateShortcut(ShortcutPath)
' Use cmd.exe to run the batch file so the window stays open and shows output
Shortcut.TargetPath = "cmd.exe"
Shortcut.Arguments = "/c """ & StartScript & """"
Shortcut.WorkingDirectory = ScriptDir
Shortcut.Description = "Launch GharMitra - Apartment Accounting & Management System"
Shortcut.IconLocation = "shell32.dll,137"  ' Application icon
Shortcut.WindowStyle = 1  ' Normal window
Shortcut.Save

' Success message
MsgBox "Desktop shortcut created successfully!" & vbCrLf & vbCrLf & "Location: " & ShortcutPath & vbCrLf & vbCrLf & "You can now double-click 'GharMitra' on your desktop to start the application.", vbInformation, "GharMitra - Success"

WScript.Quit 0
