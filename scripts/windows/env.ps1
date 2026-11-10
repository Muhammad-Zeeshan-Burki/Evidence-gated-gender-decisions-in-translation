# Shared settings: keeps every cache/temp file inside <repository>\_runtime (git-ignored). Loaded by the other scripts.
# (Public-release change: in the original project these scripts lived in _runtime\scripts, so $RT was their parent folder.)
$RT = Join-Path (Resolve-Path "$PSScriptRoot\..\..").Path "_runtime"
New-Item -ItemType Directory -Force -Path $RT | Out-Null
foreach ($d in "llama","models","dl","tmp","pipcache","hf","mpl","ipython","jupyter","runs","logs") { New-Item -ItemType Directory -Force -Path "$RT\$d" | Out-Null }
$env:TEMP="$RT\tmp"; $env:TMP="$RT\tmp"; $env:PIP_CACHE_DIR="$RT\pipcache"; $env:HF_HOME="$RT\hf"; $env:MPLCONFIGDIR="$RT\mpl"; $env:IPYTHONDIR="$RT\ipython"
$env:JUPYTER_DATA_DIR="$RT\jupyter\data"; $env:JUPYTER_RUNTIME_DIR="$RT\jupyter\runtime"; $env:JUPYTER_CONFIG_DIR="$RT\jupyter\config"
$env:PYTHONNOUSERSITE="1"; $env:PYTHONUTF8="1"; $env:PYTHONIOENCODING="utf-8"
# Make "python" (used by the Jupyter kernel spec) resolve to the project venv, not the system Python.
if (Test-Path "$RT\venv\Scripts\python.exe") { $env:PATH = "$RT\venv\Scripts;" + $env:PATH; $env:JUPYTER_PATH = "$RT\venv\share\jupyter" }
