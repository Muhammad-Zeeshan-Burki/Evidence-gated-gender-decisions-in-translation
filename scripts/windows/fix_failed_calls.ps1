# Run ONLY while the pilot notebook is stopped.
. "$PSScriptRoot\env.ps1"
& "$RT\venv\Scripts\python.exe" "$PSScriptRoot\fix_failed_calls.py" "$RT\ccl_work\cache\llm_cache_pilot.sqlite"
