# Executes the final notebook CCL_final.ipynb end to end and writes all outputs to <repository>\Results\pilot.
# Every model call is looked up in the SQLite cache (<repository>\_runtime\ccl_work\cache\llm_cache_pilot.sqlite) first;
# calls that are not cached are sent to the model server (start 2b_start_server_8k.ps1 first). The response cache of the
# reported run is not part of the public repository, so a fresh run issues every call (more than a day on an RTX 4070 Laptop GPU).
. "$PSScriptRoot\env.ps1"
$V2 = Split-Path $RT
$env:CCL_WORK_DIR="$RT\ccl_work"; $env:CCL_LLM_BACKEND="openai"; $env:CCL_OPENAI_BASE_URL="http://localhost:8080/v1"
$env:CCL_TRANSLATOR="qwen3-8b"; $env:CCL_SERVER_KIND="llamacpp"; $env:CCL_SKIP_INSTALL="1"; $env:CCL_RUN_MODE="pilot"; $env:CCL_CONCURRENCY="4"
$env:CCL_RESULTS_DIR="$V2\Results"
# Public-release addition: put the list of development-inspected test items (held-out filter) and the cached LLM name
# priors of the reported run where the notebook expects them.
New-Item -ItemType Directory -Force -Path "$RT\ccl_work\data" | Out-Null
foreach ($f in "dev_inspected_test_items.json","name_gender_lexicon__qwen3-8b.json") { if (-not (Test-Path "$RT\ccl_work\data\$f")) { Copy-Item "$V2\data\$f" "$RT\ccl_work\data\$f" } }
foreach ($v in "CCL_V3","CCL_OUT_TAG","CCL_SYSTEMS","CCL_SWEEP_TAUS","CCL_LAB_BOTH_RESOLVERS") { Remove-Item "Env:$v" -ErrorAction SilentlyContinue }
try { Invoke-WebRequest -UseBasicParsing "http://localhost:8080/health" -TimeoutSec 3 | Out-Null; $env:CCL_SKIP_PROBE="0"; Write-Host "model server is running" }
catch { $env:CCL_SKIP_PROBE="1"; Write-Host "model server not running: fine, results come from the cache" }
& "$RT\venv\Scripts\python.exe" -m pip freeze > "$V2\requirements_lock.txt"
$t0 = Get-Date; Write-Host "Running CCL_final.ipynb ..." -ForegroundColor Cyan
$p = Start-Process "$RT\venv\Scripts\jupyter.exe" -NoNewWindow -Wait -PassThru `
  -ArgumentList "nbconvert --to notebook --execute `"$V2\CCL_final.ipynb`" --output-dir `"$RT\runs`" --output CCL_final_executed.ipynb --ExecutePreprocessor.timeout=-1" `
  -RedirectStandardOutput "$RT\logs\final.out.txt" -RedirectStandardError "$RT\logs\final.txt"
$mins = [math]::Round(((Get-Date) - $t0).TotalMinutes, 1)
"exit=$($p.ExitCode) minutes=$mins finished=$(Get-Date -Format s)" | Out-File -Encoding utf8 "$RT\logs\final.status.txt"
if ($p.ExitCode -eq 0) {
  Copy-Item "$RT\runs\CCL_final_executed.ipynb" "$V2\CCL_final.ipynb" -Force
  Write-Host "FINISHED OK in $mins min. CCL_final.ipynb now contains all outputs; results are in Results\pilot" -ForegroundColor Green
} else { Write-Host "STOPPED WITH AN ERROR after $mins min (tell Claude)" -ForegroundColor Red }
