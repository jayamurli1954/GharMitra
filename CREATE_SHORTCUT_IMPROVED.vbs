' ============================================
' GharMitra - Create Desktop Shortcut (Improved)
' ============================================
' This VBScript creates a desktop shortcut for GharMitra
' Uses a more reliable method that works on all Windows versions

On Error Resume Next

Set WshShell = WScript.CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get the script directory
ScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Find the launcher script
LauncherScript = ""
If fso.FileExists(ScriptDir & "\START_GHARMITRA.bat") Then
    LauncherScript = ScriptDir & "\START_GHARMITRA.bat"
ElseIf fso.FileExists(ScriptDir & "\start_gharmitra.bat") Then
    LauncherScript = ScriptDir & "\start_gharmitra.bat"
ElseIf fso.FileExists(ScriptDir & "\launch_gharmitra.bat") Then
    LauncherScript = ScriptDir & "\launch_gharmitra.bat"
Else
    MsgBox "ERROR: Could not find launcher script!" & vbCrLf & vbCrLf & "Expected one of:" & vbCrLf & "- START_GHARMITRA.bat" & vbCrLf & "- start_gharmitra.bat" & vbCrLf & "- launch_gharmitra.bat" & vbCrLf & vbCrLf & "Script directory: " & ScriptDir, vbCritical, "GharMitra - Error"
    WScript.Quit 1
End If

' Get desktop path
DesktopPath = WshShell.SpecialFolders("Desktop")
ShortcutPath = DesktopPath & "\GharMitra.lnk"

' Delete existing shortcut if it exists
If fso.FileExists(ShortcutPath) Then
    fso.DeleteFile ShortcutPath, True
End If

' Create shortcut - Method 1: Direct batch file execution
Set Shortcut = WshShell.CreateShortcut(ShortcutPath)
Shortcut.TargetPath = LauncherScript
Shortcut.WorkingDirectory = ScriptDir
Shortcut.Description = "Launch GharMitra - Apartment Accounting & Management System"
Shortcut.IconLocation = "shell32.dll,137"
Shortcut.WindowStyle = 1  ' Normal window
Shortcut.Save

If Err.Number <> 0 Then
    MsgBox "ERROR creating shortcut: " & Err.Description, vbCritical, "GharMitra - Error"
    WScript.Quit 1
End If

' Verify shortcut was created
If Not fso.FileExists(ShortcutPath) Then
    MsgBox "ERROR: Shortcut file was not created!" & vbCrLf & vbCrLf & "Expected location: " & ShortcutPath, vbCritical, "GharMitra - Error"
    WScript.Quit 1
End If

' Success message
MsgBox "Desktop shortcut created successfully!" & vbCrLf & vbCrLf & _
       "Shortcut location: " & ShortcutPath & vbCrLf & _
       "Target: " & LauncherScript & vbCrLf & vbCrLf & _
       "You can now double-click 'GharMitra' on your desktop to start the application." & vbCrLf & vbCrLf & _
       "If the shortcut doesn't work:" & vbCrLf & _
       "1. Right-click the shortcut and select Properties" & vbCrLf & _
       "2. Check that 'Target' points to: " & LauncherScript & vbCrLf & _
       "3. Check that 'Start in' points to: " & ScriptDir, vbInformation, "GharMitra - Success"

WScript.Quit 0
