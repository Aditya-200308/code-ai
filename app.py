# ============================================================
# Root Entrypoint for Streamlit Cloud
# ============================================================

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")

for p in [current_dir, src_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

app_path = os.path.join(src_dir, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    code = compile(f.read(), app_path, "exec")
    exec(code, globals())
