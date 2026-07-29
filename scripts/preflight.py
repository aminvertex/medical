#!/usr/bin/env python3
"""Dependency-free structural checks for the MAHDAI project.

Run before installing Django to catch missing files, Python syntax errors,
broken named template URLs, missing static assets, and JavaScript syntax issues
when Node.js is available.
"""
from __future__ import annotations

import compileall
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED = [
    "manage.py",
    "requirements.txt",
    "config/settings.py",
    "config/urls.py",
    "config/api.py",
    "accounts/models.py",
    "catalog/models.py",
    "orders/models.py",
    "orders/services.py",
    "templates/base.html",
    "static/css/app.css",
]


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def check_required_files() -> None:
    missing = [path for path in REQUIRED if not (ROOT / path).exists()]
    if missing:
        fail("Missing required files: " + ", ".join(missing))
    print(f"[OK] Required files: {len(REQUIRED)}")


def check_python_syntax() -> None:
    folders = ["accounts", "catalog", "config", "core", "dashboard", "orders"]
    ok = all(compileall.compile_dir(ROOT / folder, quiet=1) for folder in folders)
    ok = compileall.compile_file(ROOT / "manage.py", quiet=1) and ok
    if not ok:
        fail("Python syntax check failed")
    print("[OK] Python syntax")


def collect_url_names() -> set[str]:
    names: set[str] = set()
    pattern = re.compile(r"\bname\s*=\s*[\"']([^\"']+)[\"']")
    for path in ROOT.rglob("urls.py"):
        names.update(pattern.findall(path.read_text(encoding="utf-8")))
    return names


def check_template_urls() -> None:
    known = collect_url_names()
    used: set[str] = set()
    pattern = re.compile(r"{%\s*url\s+[\"']([^\"']+)[\"']")
    for path in (ROOT / "templates").rglob("*.html"):
        used.update(pattern.findall(path.read_text(encoding="utf-8")))
    missing = sorted(used - known)
    if missing:
        fail("Unknown named template URLs: " + ", ".join(missing))
    print(f"[OK] Named template URLs: {len(used)}")


def check_static_references() -> None:
    pattern = re.compile(r"{%\s*static\s+[\"']([^\"']+)[\"']")
    missing: list[str] = []
    count = 0
    for path in (ROOT / "templates").rglob("*.html"):
        for relative in pattern.findall(path.read_text(encoding="utf-8")):
            count += 1
            if not (ROOT / "static" / relative).exists():
                missing.append(f"{path.relative_to(ROOT)} -> {relative}")
    if missing:
        fail("Missing static references: " + "; ".join(missing))
    print(f"[OK] Static references: {count}")


def check_javascript() -> None:
    node = shutil.which("node")
    files = sorted((ROOT / "static" / "js").glob("*.js"))
    if not node:
        print("[SKIP] Node.js not found; JavaScript syntax not checked")
        return
    for path in files:
        result = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
        if result.returncode:
            fail(f"JavaScript syntax failed for {path.name}: {result.stderr.strip()}")
    print(f"[OK] JavaScript syntax: {len(files)} files")


def main() -> int:
    check_required_files()
    check_python_syntax()
    check_template_urls()
    check_static_references()
    check_javascript()
    print("Preflight completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
