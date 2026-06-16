$ErrorActionPreference = "Stop"
$env:Path = "C:\Program Files\Git\cmd;C:\Program Files\nodejs;C:\Users\lebre\AppData\Local\Programs\Python\Python312;C:\Users\lebre\AppData\Local\Programs\Python\Python312\Scripts;" + $env:Path

Set-Location $PSScriptRoot\..\frontend
if (-not (Test-Path "node_modules")) {
  npm install
}

npm run dev
