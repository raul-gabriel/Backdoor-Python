Dim texto
Dim i,k,repetir

set ws = WScript.CreateObject("WScript.Shell" ) 
Set VarApp = ws.Exec("notepad" )


ws.AppActivate VarApp.ProcessID
WScript.Sleep 1000


texto = "fuiste hackeado ahora eres mio jaajajajajajajaajjjajaj"
repetir=3
escribir()



function escribir()
'repetir el procedimiento segun repetir
For k = 1 To repetir
   'recorrer segun la cantida del texto
   For i = 1 To Len(texto)
     verificar()
     WScript.Sleep 100
     ws.SendKeys Mid(texto, i, 1)
   Next 
   WScript.Sleep 180000
ws.SendKeys "{ENTER}"
Next

end function

'si se cierra el notepad la vuelve a abrir
function verificar()
    If VarApp.Status = 1 Then 
    set VarApp = ws.Exec("notepad" )
    End If 
end function








