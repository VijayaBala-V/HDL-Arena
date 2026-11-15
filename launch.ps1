$py = "C:\Users\Vijay\AppData\Local\Programs\Python\Python312\python.exe"
$script = "C:\Users\Vijay\hdl-judge-mvp\start_production.py"
$workDir = "C:\Users\Vijay\hdl-judge-mvp"

Write-Host "Launching server..."
Start-Process -FilePath $py -ArgumentList $script -WorkingDirectory $workDir

Start-Sleep -Seconds 3

# Open default browser
Start-Process "http://127.0.0.1:8000"
Write-Host "Website opened at http://127.0.0.1:8000"
