' Instalador do BordadoStudio — inicia SEM janela de console.
' Clique duas vezes para instalar (aparece so a caixinha "Instalando...").
Option Explicit
Dim sh, fso, dir, cmd
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir

' procura o pythonw (Python sem console)
cmd = ""
On Error Resume Next
sh.Run "pythonw.exe """ & dir & "\instalar_gui.pyw""", 0, False
If Err.Number = 0 Then WScript.Quit 0
Err.Clear
sh.Run "pyw.exe -3 """ & dir & "\instalar_gui.pyw""", 0, False
If Err.Number = 0 Then WScript.Quit 0
Err.Clear
sh.Run "py.exe -3w """ & dir & "\instalar_gui.pyw""", 0, False
If Err.Number = 0 Then WScript.Quit 0
On Error GoTo 0

MsgBox "Python nao foi encontrado neste computador." & vbCrLf & vbCrLf & _
       "1) Baixe o Python em: https://www.python.org/downloads/" & vbCrLf & _
       "2) Na instalacao, MARQUE a opcao ""Add Python to PATH""" & vbCrLf & _
       "3) Clique duas vezes em instalar.vbs novamente.", _
       vbCritical, "BordadoStudio - Instalador"
