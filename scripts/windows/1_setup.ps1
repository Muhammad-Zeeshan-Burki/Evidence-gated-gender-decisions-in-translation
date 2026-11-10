# STEP A: one-time setup. Downloads llama.cpp, the Qwen3-8B model (~5 GB) and Python packages into <repository>\_runtime.
# Safe to re-run: finished parts are skipped, an interrupted model download resumes.
. "$PSScriptRoot\env.ps1"
$V2 = Split-Path $RT
Start-Transcript -Path "$RT\logs\setup.txt" -Append | Out-Null
$ErrorActionPreference = "Stop"
try {
  Write-Host "`n=== [1/3] llama.cpp (b11642, CUDA 12.4) ===" -ForegroundColor Cyan
  $B = "b11642"; $base = "https://github.com/ggml-org/llama.cpp/releases/download/$B"
  $srvExe = Get-ChildItem "$RT\llama" -Recurse -Filter llama-server.exe -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $srvExe) {
    curl.exe -L --fail -o "$RT\dl\llama.zip"  "$base/llama-$B-bin-win-cuda-12.4-x64.zip";   if ($LASTEXITCODE) { throw "llama.cpp download failed" }
    curl.exe -L --fail -o "$RT\dl\cudart.zip" "$base/cudart-llama-bin-win-cuda-12.4-x64.zip"; if ($LASTEXITCODE) { throw "cudart download failed" }
    tar -xf "$RT\dl\llama.zip" -C "$RT\llama"; tar -xf "$RT\dl\cudart.zip" -C "$RT\llama"
    $srvExe = Get-ChildItem "$RT\llama" -Recurse -Filter llama-server.exe | Select-Object -First 1
    Get-ChildItem "$RT\llama" -Recurse -Filter "cu*.dll" | Where-Object { $_.DirectoryName -ne $srvExe.DirectoryName } | Copy-Item -Destination $srvExe.DirectoryName -Force
  } else { Write-Host "already installed" }
  & $srvExe.FullName --version

  Write-Host "`n=== [2/3] Qwen3-8B Q4_K_M model (~5 GB, resumes if interrupted) ===" -ForegroundColor Cyan
  $gguf = "$RT\models\Qwen3-8B-Q4_K_M.gguf"
  if ((Test-Path $gguf) -and ((Get-Item $gguf).Length -gt 4.5GB)) { Write-Host "already downloaded" }
  else { curl.exe -L --fail -C - -o $gguf "https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf"; if ($LASTEXITCODE) { throw "model download failed (re-run this script to resume)" } }
  Write-Host ("model size: {0:N2} GB" -f ((Get-Item $gguf).Length / 1GB))

  Write-Host "`n=== [3/3] Python environment ===" -ForegroundColor Cyan
  if (-not (Test-Path "$RT\venv\Scripts\python.exe")) { py -3.12 -m venv "$RT\venv"; if ($LASTEXITCODE) { throw "venv creation failed" } }
  & "$RT\venv\Scripts\python.exe" -m pip install --upgrade pip
  & "$RT\venv\Scripts\python.exe" -m pip install -r "$V2\requirements_ccl.txt" ipykernel nbconvert psutil
  if ($LASTEXITCODE) { throw "pip install failed" }
  & "$RT\venv\Scripts\python.exe" -c "import pandas, scipy, sklearn, matplotlib, requests, sacrebleu, statsmodels, nbconvert; print('python packages OK')"
  Write-Host "`nSETUP FINISHED OK" -ForegroundColor Green
} catch { Write-Host "`nSETUP STOPPED: $_" -ForegroundColor Red }
finally { Stop-Transcript | Out-Null }
