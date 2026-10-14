"""Convenience launcher script for the FastAPI REST backend.

Usage:
    python run_backend.py
"""

import sys
import os
import uvicorn

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Smart Grid Solar PV & Battery EMS - FastAPI Backend")
    print("Interactive Documentation: http://localhost:8000/docs")
    print("Alternative ReDoc:         http://localhost:8000/redoc")
    print("Health Check:              http://localhost:8000/api/v1/health")
    print("=" * 60)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
