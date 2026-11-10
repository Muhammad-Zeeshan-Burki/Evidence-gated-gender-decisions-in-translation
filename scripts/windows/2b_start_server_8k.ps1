# Model server with 8,192 tokens per parallel slot (was 4,096). The KV cache is stored in 8-bit (q8_0) so the doubled
# context fits in the same ~7.4 GB of GPU memory. Keep this window open.
. "$PSScriptRoot\env.ps1"
$srvExe = (Get-ChildItem "$RT\llama" -Recurse -Filter llama-server.exe | Select-Object -First 1).FullName
& $srvExe -m "$RT\models\Qwen3-8B-Q4_K_M.gguf" --alias qwen3-8b -c 32768 -np 4 -ngl 99 -fa on -ctk q8_0 -ctv q8_0 --port 8080 --jinja --log-file "$RT\logs\server_8k.txt"
