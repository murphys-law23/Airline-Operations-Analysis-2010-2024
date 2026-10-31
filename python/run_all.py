from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
for f in ['analyze.py','build_dashboard.py','build_previews.py','build_documentation.py','build_notebook.py']:
 subprocess.run([sys.executable,str(ROOT/'python'/f)],check=True,cwd=ROOT)
subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],check=True,cwd=ROOT)
