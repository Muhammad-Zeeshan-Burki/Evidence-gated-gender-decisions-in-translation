# STEP C: 1-minute test that the server answers the way the notebook needs. Also logs GPU memory.
. "$PSScriptRoot\env.ps1"
nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv | Tee-Object "$RT\logs\gpu_at_check.csv"
& "$RT\venv\Scripts\python.exe" "$PSScriptRoot\server_check.py"
