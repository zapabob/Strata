#!/usr/bin/env python3
"""Sync Hakua fork product semver across the tree.

Canonical source: repository-root ``VERSION`` (one line, SemVer-compatible
preview such as ``0.3.2-preview.YYYYMMDD.N``).

Engine / Control build numbers stay in CMakeLists.txt (and Metal
STRATA_VERSION) and are intentionally not rewritten here.

Usage:
  py -3 tools/bump_hakua_product_version.py                 # use VERSION as-is; sync others
  py -3 tools/bump_hakua_product_version.py --set 0.3.2-preview.20261029.1
  py -3 tools/bump_hakua_product_version.py --next-today    # next N for today's Japan date
  py -3 tools/bump_hakua_product_version.py --check         # exit 1 on product mismatches
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCT_RE = re.compile(
    r"^0\.\d+\.\d+(?:-preview\.\d{8}\.\d+)?$"
)
PREVIEW_RE = re.compile(r"^0\.\d+\.\d+-preview\.(\d{8})\.(\d+)$")


def read_version() -> str:
    text = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not PRODUCT_RE.fullmatch(text):
        raise SystemExit(f"VERSION is not a Hakua product semver: {text!r}")
    return text


def write_version(version: str) -> None:
    if not PRODUCT_RE.fullmatch(version):
        raise SystemExit(f"refusing non-product semver: {version!r}")
    (ROOT / "VERSION").write_text(version + "\n", encoding="utf-8", newline="\n")


def next_today(base: str = "0.3.3") -> str:
    today = date.today().strftime("%Y%m%d")
    n = 1
    try:
        tags = subprocess.check_output(
            ["git", "tag", "--list", f"v{base}-preview.{today}.*"],
            cwd=ROOT,
            text=True,
        )
        for line in tags.splitlines():
            m = re.fullmatch(rf"v{re.escape(base)}-preview\.{today}\.(\d+)", line.strip())
            if m:
                n = max(n, int(m.group(1)) + 1)
    except (OSError, subprocess.CalledProcessError):
        pass
    current = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    m = PREVIEW_RE.fullmatch(current)
    if m and m.group(1) == today:
        n = max(n, int(m.group(2)) + 1)
    return f"{base}-preview.{today}.{n}"


def replace_once(path: Path, pattern: str, repl: str, flags: int = 0) -> None:
    text = path.read_text(encoding="utf-8")
    new, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count != 1:
        raise SystemExit(f"{path}: expected 1 match for {pattern!r}, got {count}")
    path.write_text(new, encoding="utf-8", newline="\n")


def set_json_version(path: Path, version: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = version
    if "packages" in data and "" in data["packages"]:
        data["packages"][""]["version"] = version
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def set_cargo_lock_package(path: Path, name: str, version: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = rf'(name = "{re.escape(name)}"\r?\n)version = "[^"]+"'
    new, count = re.subn(pattern, rf'\1version = "{version}"', text, count=1)
    if count != 1:
        raise SystemExit(f"{path}: could not set {name} version ({count} matches)")
    path.write_text(new, encoding="utf-8", newline="\n")


def patch_product_constant(path: Path, version: str) -> None:
    replace_once(
        path,
        r'^PRODUCT_VERSION = "[^"]+"',
        f'PRODUCT_VERSION = "{version}"',
        flags=re.M,
    )


def patch_fork_readme(path: Path, version: str) -> None:
    text = path.read_text(encoding="utf-8")
    # Accept prose ("tree: `ver`") or fork-notes table ("tree | `ver`").
    new, count = re.subn(
        r"(App version in this preview tree\s*[:|]\s*`)[^`]+(`)",
        rf"\g<1>{version}\2",
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit(f"{path}: fork notes app version line missing")
    path.write_text(new, encoding="utf-8", newline="\n")


def patch_agents(path: Path, version: str, engine: str, metal: str) -> None:
    text = path.read_text(encoding="utf-8")
    banner = (
        f"Hakua product version {version}, engine {engine} "
        f"(Metal {metal}). Upstream Niko1221 docs in this file still describe "
        f"the v0.2.7.x line.\n"
    )
    # Keep upstream installer file names in the body; only the banner states Hakua product.
    new, count = re.subn(
        r"^(?:Version|Hakua product version) [^\n]+\n",
        banner,
        text,
        count=1,
        flags=re.M,
    )
    if count != 1:
        raise SystemExit(f"{path}: version banner missing")
    path.write_text(new, encoding="utf-8", newline="\n")


def cmake_engine() -> str:
    text = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    m = re.search(r"^project\(strata VERSION ([0-9.]+) ", text, re.M)
    if not m:
        raise SystemExit("CMake project version missing")
    return m.group(1)


def metal_engine() -> str:
    text = (ROOT / "metal" / "CMakeLists.txt").read_text(encoding="utf-8")
    m = re.search(r'STRATA_VERSION="([^"]+)"', text)
    if not m:
        raise SystemExit("Metal STRATA_VERSION missing")
    return m.group(1)


def sync(version: str) -> None:
    write_version(version)
    for rel in (
        "apps/desktop/package.json",
        "apps/desktop/package-lock.json",
        "apps/host/package.json",
        "apps/host/package-lock.json",
    ):
        set_json_version(ROOT / rel, version)
    replace_once(
        ROOT / "apps/desktop/src-tauri/Cargo.toml",
        r'^version = "[^"]+"',
        f'version = "{version}"',
        flags=re.M,
    )
    set_cargo_lock_package(ROOT / "apps/desktop/src-tauri/Cargo.lock", "strata-desktop", version)
    patch_product_constant(ROOT / "strata_cli" / "__init__.py", version)
    for name in sorted(path.name for path in ROOT.glob("README*.md")):
        patch_fork_readme(ROOT / name, version)
    patch_agents(ROOT / "AGENTS.md", version, cmake_engine(), metal_engine())
    folder = f"Strata-{version}"
    # NSIS still carries literal defaults (build can override via /D later).
    nsi = ROOT / "packaging" / "full_installer.nsi"
    nsi_text = nsi.read_text(encoding="utf-8")
    nsi_text = re.sub(
        r'VIAddVersionKey /LANG=1033 "FileVersion" "[^"]+"',
        f'VIAddVersionKey /LANG=1033 "FileVersion" "{version}"',
        nsi_text,
        count=1,
    )
    nsi_text = re.sub(
        r'InstallDir "\$LOCALAPPDATA\\Programs\\Strata-[^"]+"',
        lambda _m: f'InstallDir "$LOCALAPPDATA\\Programs\\{folder}"',
        nsi_text,
        count=1,
    )
    nsi.write_text(nsi_text, encoding="utf-8", newline="\n")
    # Full-package CPU fixture pins the product id in folder / component names.
    fixture = ROOT / "tests" / "terminal" / "test_full_windows.py"
    fx = fixture.read_text(encoding="utf-8")
    fx = re.sub(r"0\.3\.2-preview\.\d{8}\.\d+", version, fx)
    fixture.write_text(fx, encoding="utf-8", newline="\n")
    print(f"synced product version -> {version}")
    print("note: update tests/terminal/test_tui2_023_versions.py expectations if PRODUCT_VERSION asserts fail")


def collect() -> dict[str, str]:
    cargo = re.search(
        r'^version = "([^"]+)"',
        (ROOT / "apps/desktop/src-tauri/Cargo.toml").read_text(encoding="utf-8"),
        re.M,
    ).group(1)
    lock = re.search(
        r'name = "strata-desktop"\r?\nversion = "([^"]+)"',
        (ROOT / "apps/desktop/src-tauri/Cargo.lock").read_text(encoding="utf-8"),
    ).group(1)
    desk = json.loads((ROOT / "apps/desktop/package.json").read_text(encoding="utf-8"))["version"]
    desk_lock = json.loads((ROOT / "apps/desktop/package-lock.json").read_text(encoding="utf-8"))["version"]
    host = json.loads((ROOT / "apps/host/package.json").read_text(encoding="utf-8"))["version"]
    host_lock = json.loads((ROOT / "apps/host/package-lock.json").read_text(encoding="utf-8"))["version"]
    product = re.search(
        r'^PRODUCT_VERSION = "([^"]+)"',
        (ROOT / "strata_cli" / "__init__.py").read_text(encoding="utf-8"),
        re.M,
    ).group(1)
    version_file = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8").splitlines()[2]
    readme = re.search(
        r"App version in this preview tree\s*[:|]\s*`([^`]+)`",
        (ROOT / "README.md").read_text(encoding="utf-8"),
    )
    sys.path.insert(0, str(ROOT / "packaging"))
    import full_windows as fw  # noqa: WPS433

    nsi = (ROOT / "packaging" / "full_installer.nsi").read_text(encoding="utf-8")
    m_nsi = re.search(r'FileVersion" "([^"]+)"', nsi)
    return {
        "VERSION": version_file,
        "Cargo.toml": cargo,
        "Cargo.lock/strata-desktop": lock,
        "desktop/package.json": desk,
        "desktop/package-lock.json": desk_lock,
        "host/package.json": host,
        "host/package-lock.json": host_lock,
        "PRODUCT_VERSION": product,
        "AGENTS.md[banner]": agents,
        "README.md[fork]": readme.group(1) if readme else "",
        "full_windows.programs_folder": fw.programs_folder(),
        "full_installer.nsi[FileVersion]": m_nsi.group(1) if m_nsi else "",
        "engine(CMake)": cmake_engine(),
        "engine(Metal)": metal_engine(),
    }


def check() -> int:
    rows = collect()
    product = rows["VERSION"]
    mismatches = []
    for key in (
        "Cargo.toml",
        "Cargo.lock/strata-desktop",
        "desktop/package.json",
        "desktop/package-lock.json",
        "host/package.json",
        "host/package-lock.json",
        "PRODUCT_VERSION",
        "README.md[fork]",
        "full_installer.nsi[FileVersion]",
    ):
        if rows[key] != product:
            mismatches.append((key, rows[key], product))
    folder = f"Strata-{product}"
    if rows["full_windows.programs_folder"] != folder:
        mismatches.append(("full_windows.programs_folder", rows["full_windows.programs_folder"], folder))
    if product not in rows["AGENTS.md[banner]"]:
        mismatches.append(("AGENTS.md[banner]", rows["AGENTS.md[banner]"], product))
    for key, got, want in mismatches:
        print(f"MISMATCH {key}: got {got!r} want {want!r}")
    if not mismatches:
        print("OK product sources match", product)
        print("engine (separate):", rows["engine(CMake)"], rows["engine(Metal)"])
    return 1 if mismatches else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--set", dest="set_version", help="write VERSION then sync")
    ap.add_argument("--next-today", action="store_true", help="bump to next preview for today")
    ap.add_argument("--check", action="store_true", help="verify product sources agree")
    ap.add_argument("--show", action="store_true", help="print current version map")
    args = ap.parse_args()
    if args.show or (not args.set_version and not args.next_today and not args.check):
        for k, v in collect().items():
            print(f"{k}: {v}")
        if args.show and not args.check and not args.set_version and not args.next_today:
            return 0
    if args.next_today:
        sync(next_today())
    elif args.set_version:
        sync(args.set_version)
    if args.check or args.next_today or args.set_version:
        return check()
    return 0


if __name__ == "__main__":
    sys.exit(main())
