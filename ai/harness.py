#!/usr/bin/env python3
"""Reusable AI-work harness CLI.

Everything project-specific lives in ai/harness.json; this file is generic and
can be copied unchanged into another repository.

Usage:
    python ai/harness.py check [--offline] [--only ID[,ID...]]
    python ai/harness.py sync-agents
    python ai/harness.py new-task "short title"

Standard library only; Python 3.10+.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
ROOT = HARNESS_DIR.parent
CONFIG_PATH = HARNESS_DIR / "harness.json"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# --------------------------------------------------------------------------- utils

def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def tracked_files() -> list[str]:
    """Files tracked by git plus untracked-but-not-ignored files (posix paths)."""
    try:
        out = subprocess.run(
            ["git", "-c", "core.quotepath=false", "ls-files", "-z",
             "--cached", "--others", "--exclude-standard"],
            cwd=ROOT, capture_output=True, check=True,
        ).stdout
        files = sorted({p for p in out.decode("utf-8").split("\0") if p})
        return [p for p in files if (ROOT / p).is_file()]
    except (OSError, subprocess.CalledProcessError):
        return sorted(p.relative_to(ROOT).as_posix()
                      for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts)


def match_any(path: str, patterns: list[str]) -> bool:
    name = path.rsplit("/", 1)[-1]
    for pat in patterns:
        if fnmatch.fnmatchcase(path, pat) or fnmatch.fnmatchcase(name, pat):
            return True
        if pat.startswith("**/") and fnmatch.fnmatchcase(path, pat[3:]):
            return True
    return False


def select(files: list[str], globs: list[str], exclude: list[str] | None = None) -> list[str]:
    return [f for f in files if match_any(f, globs) and not match_any(f, exclude or [])]


def read_text(path: str) -> str | None:
    try:
        return (ROOT / path).read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


@dataclass
class Result:
    check_id: str
    level: str
    status: str = "pass"          # pass | fail | skip
    messages: list[str] = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.status = "fail"
        self.messages.append(msg)


# --------------------------------------------------------------------------- checks

def check_forbidden_tracked(c: dict, files: list[str], r: Result, **_) -> None:
    for f in files:
        if match_any(f, c["patterns"]):
            r.fail(f"must not be committed: {f}")


def check_max_file_size(c: dict, files: list[str], r: Result, **_) -> None:
    limit = c["max_mb"] * 1024 * 1024
    for f in files:
        if match_any(f, c.get("allow", [])):
            continue
        size = (ROOT / f).stat().st_size
        if size > limit:
            r.fail(f"{f} is {size / 1024 / 1024:.1f} MB (limit {c['max_mb']} MB)")


def check_secret_scan(c: dict, files: list[str], r: Result, **_) -> None:
    regexes = [re.compile(p) for p in c["patterns"]]
    for f in select(files, c.get("globs", ["*"]), c.get("exclude")):
        text = read_text(f)
        if text is None:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for rx in regexes:
                m = rx.search(line)
                if m:
                    shown = m.group(0)
                    shown = shown[:8] + "…" if len(shown) > 8 else shown
                    r.fail(f"{f}:{lineno} possible secret ({shown})")


def check_python_compile(c: dict, files: list[str], r: Result, **_) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        for f in select(files, c["globs"], c.get("exclude")):
            try:
                py_compile.compile(str(ROOT / f), cfile=str(Path(tmp) / "x.pyc"), doraise=True)
            except py_compile.PyCompileError as e:
                r.fail(f"{f}: {e.msg.strip().splitlines()[-1]}")


def check_json_valid(c: dict, files: list[str], r: Result, **_) -> None:
    for f in select(files, c["globs"], c.get("exclude")):
        text = read_text(f)
        if text is None:
            r.fail(f"{f}: not valid UTF-8")
            continue
        try:
            json.loads(text)
        except json.JSONDecodeError as e:
            r.fail(f"{f}:{e.lineno} {e.msg}")


def check_api_contract(c: dict, files: list[str], r: Result, **_) -> None:
    def collect(globs: list[str], pattern: str) -> dict[str, set[str]]:
        rx = re.compile(pattern)
        found: dict[str, set[str]] = {}
        for f in select(files, globs):
            for m in rx.finditer(read_text(f) or ""):
                found.setdefault(m.group(1).rstrip("/") or "/", set()).add(f)
        return found

    client = collect(c["client_globs"], c["client_regex"])
    server = collect(c["server_globs"], c["server_regex"])
    if not server:
        r.fail("no server routes found — check server_regex/server_globs")
    for route, where in sorted(client.items()):
        if route not in server:
            r.fail(f"client calls {route} ({', '.join(sorted(where))}) but no server route defines it")
    r.messages.append(f"client routes: {sorted(client)} | server routes: {sorted(server)}")


def check_requirements(c: dict, files: list[str], r: Result, offline: bool = False, **_) -> None:
    line_rx = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?\s*==\s*([^\s;#]+)")
    for req in c["files"]:
        text = read_text(req)
        if text is None:
            r.fail(f"{req}: missing or unreadable")
            continue
        for lineno, raw in enumerate(text.splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith(("#", "-")):
                continue
            m = line_rx.match(line)
            if not m:
                if c.get("require_pins", True):
                    r.fail(f"{req}:{lineno} not pinned with == : {line}")
                continue
            if offline or not c.get("verify_on_pypi", False):
                continue
            name, ver = m.groups()
            url = f"https://pypi.org/pypi/{name}/{ver}/json"
            try:
                with urllib.request.urlopen(url, timeout=10):
                    pass
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    r.fail(f"{req}:{lineno} {name}=={ver} does not exist on PyPI")
                else:
                    r.messages.append(f"{name}: PyPI HTTP {e.code}, not verified")
            except (urllib.error.URLError, TimeoutError):
                r.messages.append("PyPI unreachable — remaining packages not verified")
                return


def check_dir_sync(c: dict, files: list[str], r: Result, **_) -> None:
    src, dst = ROOT / c["src"], ROOT / c["dst"]
    for s in sorted(src.glob("*.md")):
        d = dst / s.name
        if not d.exists():
            r.fail(f"{c['dst']}/{s.name} missing — run: python ai/harness.py sync-agents")
        elif d.read_bytes().replace(b"\r\n", b"\n") != s.read_bytes().replace(b"\r\n", b"\n"):
            r.fail(f"{c['dst']}/{s.name} differs from {c['src']} — run: python ai/harness.py sync-agents")


def check_command(c: dict, files: list[str], r: Result, **_) -> None:
    exe = c["cmd"][0]
    if shutil.which(exe) is None:
        if c.get("optional", False):
            r.status = "skip"
            r.messages.append(f"'{exe}' not installed")
        else:
            r.fail(f"'{exe}' not installed")
        return
    targets = select(files, c["globs"]) if "globs" in c else [None]
    for t in targets:
        cmd = [part.replace("{file}", t) if t else part for part in c["cmd"]]
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if p.returncode != 0:
            tail = (p.stderr or p.stdout).strip().splitlines()[-3:]
            r.fail(f"{' '.join(cmd)} -> exit {p.returncode}: {' | '.join(tail)}")


CHECKS = {
    "forbidden_tracked": check_forbidden_tracked,
    "max_file_size": check_max_file_size,
    "secret_scan": check_secret_scan,
    "python_compile": check_python_compile,
    "json_valid": check_json_valid,
    "api_contract": check_api_contract,
    "requirements": check_requirements,
    "dir_sync": check_dir_sync,
    "command": check_command,
}


# --------------------------------------------------------------------------- commands

def cmd_check(args: argparse.Namespace) -> int:
    cfg = load_config()
    files = tracked_files()
    only = set(args.only.split(",")) if args.only else None
    results: list[Result] = []
    for c in cfg["checks"]:
        if only and c["id"] not in only:
            continue
        r = Result(c["id"], c.get("level", "error"))
        fn = CHECKS.get(c["type"])
        if fn is None:
            r.fail(f"unknown check type '{c['type']}'")
        else:
            try:
                fn(c, files, r, offline=args.offline)
            except Exception as e:  # a broken check must not hide the others
                r.fail(f"check crashed: {type(e).__name__}: {e}")
        results.append(r)

    icon = {"pass": "PASS", "skip": "SKIP", "fail": "FAIL"}
    for r in results:
        label = icon[r.status] if r.status != "fail" or r.level == "error" else "WARN"
        print(f"[{label}] {r.check_id}")
        for m in r.messages:
            print(f"       - {m}")
    errors = [r for r in results if r.status == "fail" and r.level == "error"]
    warns = [r for r in results if r.status == "fail" and r.level != "error"]
    print(f"\n{len(results)} checks, {len(errors)} error(s), {len(warns)} warning(s)")
    return 1 if errors else 0


def cmd_sync_agents(_: argparse.Namespace) -> int:
    paths = load_config()["paths"]
    src, dst = ROOT / paths["agents_src"], ROOT / paths["agents_dst"]
    dst.mkdir(parents=True, exist_ok=True)
    for s in sorted(src.glob("*.md")):
        shutil.copyfile(s, dst / s.name)
        print(f"synced {paths['agents_dst']}/{s.name}")
    return 0


def cmd_new_task(args: argparse.Namespace) -> int:
    paths = load_config()["paths"]
    tasks = ROOT / paths["tasks"]
    tasks.mkdir(parents=True, exist_ok=True)
    nums = [int(m.group(1)) for p in tasks.glob("*.md") if (m := re.match(r"(\d{4})-", p.name))]
    num = max(nums, default=0) + 1
    slug = re.sub(r"[^\w]+", "-", args.title.strip().lower(), flags=re.UNICODE).strip("-") or "task"
    path = tasks / f"{num:04d}-{slug}.md"
    template = (ROOT / paths["task_template"]).read_text(encoding="utf-8")
    path.write_text(template.replace("{{ID}}", f"{num:04d}")
                            .replace("{{TITLE}}", args.title.strip())
                            .replace("{{DATE}}", date.today().isoformat()), encoding="utf-8")
    print(path.relative_to(ROOT).as_posix())
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="AI work harness")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check", help="run verification checks from ai/harness.json")
    p.add_argument("--offline", action="store_true", help="skip checks that need network")
    p.add_argument("--only", help="comma-separated check ids")
    p.set_defaults(func=cmd_check)
    sub.add_parser("sync-agents", help="copy ai/agents/*.md into .claude/agents").set_defaults(func=cmd_sync_agents)
    p = sub.add_parser("new-task", help="create a task record from the template")
    p.add_argument("title")
    p.set_defaults(func=cmd_new_task)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
