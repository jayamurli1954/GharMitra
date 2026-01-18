' ============================================
' GharMitra - Create Desktop Shortcut
' ============================================
' This VBScript creates a desktop shortcut for GharMitra
' Works on all Windows versions

Set oWS = WScript.CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
sLinkFile = oWS.SpecialFolders("Desktop") & "\GharMitra.lnk"

' Get the script directory (where this VBS file is located)
scriptPath = fso.GetParentFolderName(WScript.ScriptFullName)

' Try to find the launcher script (prefer START_GHARMITRA.bat, fallback to others)
launcherPath = ""
If fso.FileExists(scriptPath & "\START_GHARMITRA.bat") Then
    launcherPath = scriptPath & "\START_GHARMITRA.bat"
ElseIf fso.FileExists(scriptPath & "\start_gharmitra.bat") Then
    launcherPath = scriptPath & "\start_gharmitra.bat"
ElseIf fso.FileExists(scriptPath & "\launch_gharmitra.bat") Then
    launcherPath = scriptPath & "\launch_gharmitra.bat"
Else
    MsgBox "ERROR: Could not find launcher script!" & vbCrLf & vbCrLf & "Expected one of:" & vbCrLf & "- START_GHARMITRA.bat" & vbCrLf & "- start_gharmitra.bat" & vbCrLf & "- launch_gharmitra.bat", vbCritical, "GharMitra - Error"
    WScript.Quit 1
End If

' Check for icon files (prefer .ico, fallback to .png, then default)
iconPath = ""
If fso.FileExists(scriptPath & "\GharMitra_Logo.png") Then
    iconPath = scriptPath & "\GharMitra_Logo.png"
ElseIf fso.FileExists(scriptPath & "\GharMitra Logo.png") Then
    iconPath = scriptPath & "\GharMitra Logo.png"
ElseIf fso.FileExists(scriptPath & "\Logo1.png") Then
    iconPath = scriptPath & "\Logo1.png"
End If

Set oLink = oWS.CreateShortcut(sLinkFile)
' Direct batch file execution (simpler and more reliable)
oLink.TargetPath = launcherPath
oLink.WorkingDirectory = scriptPath
oLink.Description = "Launch GharMitra - Apartment Accounting & Management System"
If iconPath <> "" Then
    oLink.IconLocation = iconPath & ",0"
Else
    oLink.IconLocation = "shell32.dll,137"  ' Application icon
End If
oLink.WindowStyle = 1  ' Normal window
oLink.Save

MsgBox "Desktop shortcut created successfully!" & vbCrLf & vbCrLf & "Shortcut location: " & sLinkFile & vbCrLf & vbCrLf & "You can now double-click 'GharMitra' on your desktop to start the application.", vbInformation, "GharMitra - Success"
