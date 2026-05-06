"""
installer.py — Auto-installs missing Python packages at startup.
S: One responsibility — dependency bootstrap only.
"""
import sys, importlib, subprocess

_REQUIRED = [("flask", "flask"), ("rich", "rich"), ("requests", "requests")]

def ensure_dependencies(packages: list[tuple[str, str]] = _REQUIRED) -> None:
    for pkg, mod in packages:
        try:
            importlib.import_module(mod)
        except ImportError:
            print(f"  [bootstrap] installing {pkg}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "-q"], check=True
            )
