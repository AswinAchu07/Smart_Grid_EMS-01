"""Convenience launcher script for the Streamlit Analytics Dashboard.

Usage:
    python run_dashboard.py
"""

import sys
import os
import subprocess

if __name__ == "__main__":
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    dashboard_path = os.path.join(repo_dir, "dashboard", "Home.py")
    
    # Auto-detect venv python to ensure isolated dependencies are used
    venv_py_win = os.path.join(repo_dir, "venv", "Scripts", "python.exe")
    venv_py_nix = os.path.join(repo_dir, "venv", "bin", "python")
    py_exec = sys.executable
    if os.path.exists(venv_py_win):
        py_exec = venv_py_win
    elif os.path.exists(venv_py_nix):
        py_exec = venv_py_nix

    print("=" * 60)
    print("Starting Smart Grid Solar PV & Battery EMS - Streamlit Dashboard")
    print(f"Target:     {dashboard_path}")
    print(f"Python Env: {py_exec}")
    print("UI URL:     http://localhost:8501")
    print("=" * 60)
    
    # Run with repo_dir in PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = repo_dir + os.pathsep + env.get("PYTHONPATH", "")
    
    subprocess.run([py_exec, "-m", "streamlit", "run", dashboard_path], cwd=repo_dir, env=env)
