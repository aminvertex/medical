#!/usr/bin/env python3
"""Dependency-free structural QA for the MAHDAI project.

This script intentionally runs before Django is installed. Runtime behavior is
covered by the Django test suite; here we catch syntax, route, template, static,
JavaScript, database-integrity and known authentication-configuration mistakes.
"""
from __future__ import annotations

import ast
import compileall
import re
import shutil
import sqlite3
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
    "accounts/security.py",
    "accounts/checks.py",
    "catalog/models.py",
    "orders/models.py",
    "orders/services.py",
    "templates/base.html",
    "static/css/app.css",
]
SOURCE_SUFFIXES = {".py", ".html", ".js", ".css", ".md", ".sh", ".bat"}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def check_required_files() -> None:
    missing = [path for path in REQUIRED if not (ROOT / path).exists()]
    if missing:
        fail("Missing required files: " + ", ".join(missing))
    print(f"[OK] Required files: {len(REQUIRED)}")


def check_python_syntax() -> None:
    folders = ["accounts", "catalog", "config", "core", "dashboard", "orders", "scripts"]
    ok = all(compileall.compile_dir(ROOT / folder, quiet=1) for folder in folders)
    for file_name in ("manage.py", "tests_support.py"):
        ok = compileall.compile_file(ROOT / file_name, quiet=1) and ok
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


def check_duplicate_template_ids() -> None:
    id_pattern = re.compile(r'\bid\s*=\s*["\']([^"\']+)["\']')
    problems: list[str] = []
    for path in (ROOT / "templates").rglob("*.html"):
        ids = id_pattern.findall(path.read_text(encoding="utf-8"))
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        if duplicates:
            problems.append(f"{path.relative_to(ROOT)}: {', '.join(duplicates)}")
    if problems:
        fail("Duplicate HTML ids: " + "; ".join(problems))
    print("[OK] Template id uniqueness")


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


def _router_prefixes() -> dict[str, str]:
    source = (ROOT / "config" / "api.py").read_text(encoding="utf-8")
    pattern = re.compile(
        r'api\.add_router\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^."\']+)\.api\.router["\']'
    )
    return {app: prefix for prefix, app in pattern.findall(source)}


def _api_patterns() -> list[re.Pattern[str]]:
    patterns: list[re.Pattern[str]] = []
    for app, prefix in _router_prefixes().items():
        path = ROOT / app / "api.py"
        if not path.exists():
            fail(f"Router module missing: {app}.api")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not decorator.args:
                    continue
                func = decorator.func
                if not (
                    isinstance(func, ast.Attribute)
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "router"
                    and func.attr in {"get", "post", "put", "patch", "delete"}
                ):
                    continue
                if not isinstance(decorator.args[0], ast.Constant):
                    continue
                route = f"/api{prefix}{decorator.args[0].value}"
                escaped = re.escape(route)
                escaped = re.sub(r"\\\{[^}]+\\\}", r"[^/]+", escaped)
                patterns.append(re.compile(f"^{escaped}/?$"))
    return patterns


def check_frontend_api_routes() -> None:
    route_patterns = _api_patterns()
    call_pattern = re.compile(r'(?:apiFetch|fetch)\(\s*[`"\'](/api/[^`"\']+)[`"\']')
    missing: list[str] = []
    checked = 0
    for path in sorted((ROOT / "static" / "js").glob("*.js")):
        source = path.read_text(encoding="utf-8")
        for endpoint in call_pattern.findall(source):
            checked += 1
            normalized = re.sub(r"\$\{[^}]+\}", "value", endpoint)
            if not any(pattern.match(normalized) for pattern in route_patterns):
                missing.append(f"{path.name}: {endpoint}")
    if missing:
        fail("Frontend API calls without backend route: " + "; ".join(missing))
    print(f"[OK] Frontend/backend API route alignment: {checked} calls")


def check_ninja_status_schemas() -> None:
    problems: list[str] = []
    for path in ROOT.glob("*/api.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            returns_status = any(
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == "Status"
                for child in ast.walk(node)
            )
            if not returns_status:
                continue
            route_decorators = [
                dec
                for dec in node.decorator_list
                if isinstance(dec, ast.Call)
                and isinstance(dec.func, ast.Attribute)
                and isinstance(dec.func.value, ast.Name)
                and dec.func.value.id == "router"
            ]
            has_response = any(
                any(keyword.arg == "response" for keyword in dec.keywords)
                for dec in route_decorators
            )
            if not has_response:
                problems.append(f"{path.relative_to(ROOT)}:{node.lineno} {node.name}")
    if problems:
        fail("Ninja Status responses without response schema: " + "; ".join(problems))
    print("[OK] Django Ninja response schemas")


def check_role_auth_structure() -> None:
    path = ROOT / "accounts" / "security.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    auth_class = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "RoleSessionAuth"
        ),
        None,
    )
    if auth_class is None:
        fail("RoleSessionAuth class is missing")
    init = next((node for node in auth_class.body if isinstance(node, ast.FunctionDef) and node.name == "__init__"), None)
    authenticate = next((node for node in auth_class.body if isinstance(node, ast.FunctionDef) and node.name == "authenticate"), None)
    if init is None or not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "__init__"
        and isinstance(node.func.value, ast.Call)
        and isinstance(node.func.value.func, ast.Name)
        and node.func.value.func.id == "super"
        for node in ast.walk(init)
    ):
        fail("RoleSessionAuth.__init__ must call super().__init__")
    arg_names = [arg.arg for arg in authenticate.args.args] if authenticate else []
    if arg_names[:3] != ["self", "request", "key"]:
        fail("RoleSessionAuth.authenticate must accept (self, request, key)")
    print("[OK] RoleSessionAuth parent initialization and signature")


def check_sqlite_integrity() -> None:
    database = ROOT / "db.sqlite3"
    if not database.exists():
        print("[SKIP] db.sqlite3 not present")
        return
    connection = sqlite3.connect(database)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
    finally:
        connection.close()
    if integrity != "ok":
        fail(f"SQLite integrity_check: {integrity}")
    if foreign_keys:
        fail(f"SQLite foreign-key violations: {foreign_keys[:5]}")

    connection = sqlite3.connect(database)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        required_tables = {
            "orders_order",
            "orders_orderitem",
            "orders_payment",
            "orders_enrollment",
        }
        if required_tables.issubset(tables):
            invalid_totals = connection.execute(
                "SELECT number FROM orders_order "
                "WHERE discount_amount > subtotal "
                "OR total_amount != subtotal - discount_amount"
            ).fetchall()
            invalid_paid = connection.execute(
                "SELECT o.number FROM orders_order o "
                "LEFT JOIN orders_payment p ON p.order_id = o.id "
                "WHERE o.status = 'PAID' "
                "AND (p.id IS NULL OR p.status != 'SUCCESS' OR p.amount != o.total_amount)"
            ).fetchall()
            invalid_success = connection.execute(
                "SELECT o.number FROM orders_payment p "
                "JOIN orders_order o ON o.id = p.order_id "
                "WHERE p.status = 'SUCCESS' AND o.status != 'PAID'"
            ).fetchall()
            invalid_enrollments = connection.execute(
                "SELECT e.id FROM orders_enrollment e "
                "JOIN orders_orderitem i ON i.id = e.order_item_id "
                "JOIN orders_order o ON o.id = i.order_id "
                "WHERE e.is_active = 1 "
                "AND (e.course_id != i.course_id OR e.user_id != o.user_id OR o.status != 'PAID')"
            ).fetchall()
            problems = invalid_totals + invalid_paid + invalid_success + invalid_enrollments
            if problems:
                fail(
                    "SQLite business invariants failed: "
                    f"totals={invalid_totals[:3]}, paid={invalid_paid[:3]}, "
                    f"success={invalid_success[:3]}, enrollments={invalid_enrollments[:3]}"
                )
    finally:
        connection.close()
    print("[OK] SQLite integrity, foreign keys and business invariants")


def check_no_machine_specific_paths() -> None:
    pattern = re.compile(r"/home/[^/]+/(?:project_web|Code)/")
    problems: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
            continue
        if any(part in {"legacy_frontend", ".git", ".venv", "__pycache__"} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if pattern.search(text):
            problems.append(str(path.relative_to(ROOT)))
    if problems:
        fail("Machine-specific absolute paths found: " + ", ".join(problems))
    print("[OK] No machine-specific source paths")


def main() -> int:
    check_required_files()
    check_python_syntax()
    check_template_urls()
    check_static_references()
    check_duplicate_template_ids()
    check_javascript()
    check_frontend_api_routes()
    check_ninja_status_schemas()
    check_role_auth_structure()
    check_sqlite_integrity()
    check_no_machine_specific_paths()
    print("Preflight completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
