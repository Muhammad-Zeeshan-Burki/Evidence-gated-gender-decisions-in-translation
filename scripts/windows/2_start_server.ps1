# STEP B: starts the model server on the GPU. Keep this window open while experiments run. Ctrl+C stops it.
. "$PSScriptRoot\env.ps1"
$srvExe = (Get-ChildItem "$RT\llama" -Recurse -Filter llama-server.exe | Select-Object -First 1).FullName
& $srvExe -m "$RT\models\Qwen3-8B-Q4_K_M.gguf" --alias qwen3-8b -c 16384 -np 4 -ngl 99 -fa on --port 8080 --jinja --log-file "$RT\logs\server.txt"
