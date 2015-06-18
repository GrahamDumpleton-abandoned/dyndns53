import os

SCRIPT = os.path.join(os.path.dirname(__file__), 'app.sh')

os.execl('/bin/bash', 'bash (python -u app.py)', SCRIPT)
