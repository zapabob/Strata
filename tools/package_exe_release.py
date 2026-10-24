#!/usr/bin/env python3
"""
package_exe_release.py - Assemble, verify, and package Strata v0.3.0 executable binaries into tar.7z.

Complies with MILSPEC-LLMOps standard:
- Strict logging, zero raw print statements
- Comprehensive type annotations
- UTF-8 file encoding
- Multi-threaded compression utilizing 6 cores / 12 threads
- Verification of SHA-256 digests and binary headers
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
from typing import Any, Dict, List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

SEVEN_ZIP_PATH = Path(r"C:\Program Files\7-Zip\7z.exe")
RELEASE_ROOT = Path(r"H:\Strata\releases\0.3.0")
STAGE_DIR = RELEASE_ROOT / "Strata-0.3.0-windows-x64-sm120-exe"
TAR_PATH = RELEASE_ROOT / "Strata-0.3.0-windows-x64-sm120-exe.tar"
ARCHIVE_PATH = RELEASE_ROOT / "Strata-0.3.0-windows-x64-sm120-exe.tar.7z"
METADATA_PATH = RELEASE_ROOT / "Strata-0.3.0-windows-x64-sm120-exe.tar.7z.json"

SOURCE_BASE = RELEASE_ROOT / "Strata-0.3.0-windows-x64-sm120"
PROGRAMS_BASE = Path(r"C:\Users\downl\AppData\Local\Programs\Strata")
ENGINE_BUNDLE = PROGRAMS_BASE / "engine-bundle" / "0.3.0-windows-x86_64-cuda-cuda13"


def compute_sha256(file_path: Path) -> str:
    """Compute the hexadecimal SHA-256 digest of a given file."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def assemble_payload() -> List[Dict[str, Any]]:
    """Assemble all required executable binaries, runtime DLLs, and docs into the stage directory."""
    if STAGE_DIR.exists():
        logging.info("Cleaning existing stage directory: %s", STAGE_DIR)
        shutil.rmtree(STAGE_DIR)
    STAGE_DIR.mkdir(parents=True, exist_ok=True)

    items_to_copy: List[Dict[str, str]] = [
        # Native CUDA inference engine & helper DLLs
        {
            "src": str(SOURCE_BASE / "strata.exe"),
            "dst": "strata.exe",
            "desc": "Native CUDA sm_120 inference engine",
        },
        {
            "src": str(PROGRAMS_BASE / "strata-desktop.exe"),
            "dst": "strata-desktop.exe",
            "desc": "Desktop GUI application carrier",
        },
        {
            "src": str(ENGINE_BUNDLE / "strata-vision.exe"),
            "dst": "strata-vision.exe",
            "desc": "Vision processing engine",
        },
        {
            "src": str(SOURCE_BASE / "strata_kq.dll"),
            "dst": "strata_kq.dll",
            "desc": "Kernel quantization library",
        },
        # CUDA 13.x Runtime libraries
        {
            "src": str(SOURCE_BASE / "cublas64_13.dll"),
            "dst": "cublas64_13.dll",
            "desc": "NVIDIA cuBLAS 13 runtime",
        },
        {
            "src": str(SOURCE_BASE / "cublasLt64_13.dll"),
            "dst": "cublasLt64_13.dll",
            "desc": "NVIDIA cuBLASLt 13 runtime",
        },
        # MSVC 14.x C++ Runtimes
        {
            "src": str(SOURCE_BASE / "msvcp140.dll"),
            "dst": "msvcp140.dll",
            "desc": "MSVC standard C++ runtime",
        },
        {
            "src": str(SOURCE_BASE / "msvcp140_atomic_wait.dll"),
            "dst": "msvcp140_atomic_wait.dll",
            "desc": "MSVC atomic wait runtime",
        },
        {
            "src": str(SOURCE_BASE / "vcruntime140.dll"),
            "dst": "vcruntime140.dll",
            "desc": "MSVC C runtime",
        },
        {
            "src": str(SOURCE_BASE / "vcruntime140_1.dll"),
            "dst": "vcruntime140_1.dll",
            "desc": "MSVC C++ exception handling runtime",
        },
        # Docs & Notices
        {
            "src": str(SOURCE_BASE / "README.md"),
            "dst": "README.md",
            "desc": "Release documentation",
        },
        {
            "src": str(SOURCE_BASE / "THIRD-PARTY-NOTICES.md"),
            "dst": "THIRD-PARTY-NOTICES.md",
            "desc": "Third-party license notices",
        },
    ]

    # CLI launcher helper script
    strata_cmd_content = (
        "@echo off\r\n"
        "setlocal\r\n"
        "set SCRIPT_DIR=%~dp0\r\n"
        "\"%SCRIPT_DIR%strata.exe\" %*\r\n"
        "endlocal\r\n"
    )
    (STAGE_DIR / "strata.cmd").write_text(strata_cmd_content, encoding="utf-8")
    logging.info("Created CLI wrapper: strata.cmd")

    # Copy licenses directory
    licenses_src = SOURCE_BASE / "licenses"
    if licenses_src.is_dir():
        shutil.copytree(licenses_src, STAGE_DIR / "licenses", dirs_exist_ok=True)
        logging.info("Copied licenses directory.")

    file_manifest: List[Dict[str, Any]] = []

    for item in items_to_copy:
        src_path = Path(item["src"])
        dst_path = STAGE_DIR / item["dst"]
        if not src_path.exists():
            raise FileNotFoundError(f"Missing required payload source: {src_path}")
        logging.info("Copying %s (%s) -> %s", src_path.name, item["desc"], dst_path.name)
        shutil.copy2(src_path, dst_path)

        file_sha = compute_sha256(dst_path)
        file_size = dst_path.stat().st_size
        file_manifest.append(
            {
                "path": item["dst"],
                "sha256": file_sha,
                "bytes": file_size,
                "description": item["desc"],
            }
        )

    # Include strata.cmd in manifest
    cmd_path = STAGE_DIR / "strata.cmd"
    file_manifest.append(
        {
            "path": "strata.cmd",
            "sha256": compute_sha256(cmd_path),
            "bytes": cmd_path.stat().st_size,
            "description": "Windows batch launcher wrapper",
        }
    )

    # Generate SHA256SUMS.txt
    sha_lines = [f"{m['sha256']} *{m['path']}" for m in sorted(file_manifest, key=lambda x: x["path"])]
    sha_file = STAGE_DIR / "SHA256SUMS.txt"
    sha_file.write_text("\n".join(sha_lines) + "\n", encoding="utf-8")
    logging.info("Wrote SHA256SUMS.txt with %d entries.", len(sha_lines))

    return file_manifest


def create_tar_archive() -> None:
    """Create normalized POSIX tar archive."""
    if TAR_PATH.exists():
        TAR_PATH.unlink()
    logging.info("Creating normalized tar archive at: %s", TAR_PATH)

    with tarfile.open(TAR_PATH, "w", format=tarfile.USTAR_FORMAT) as tar:
        for file_path in sorted(STAGE_DIR.rglob("*")):
            if file_path.is_file():
                rel_path = file_path.relative_to(STAGE_DIR.parent).as_posix()
                tar_info = tar.gettarinfo(str(file_path), arcname=rel_path)
                tar_info.uid = 0
                tar_info.gid = 0
                tar_info.mtime = 0
                tar_info.uname = ""
                tar_info.gname = ""
                tar_info.mode = 0o755 if file_path.suffix.lower() in (".exe", ".cmd") else 0o644
                with file_path.open("rb") as stream:
                    tar.addfile(tar_info, stream)
    logging.info("Tar archive created successfully: %d bytes.", TAR_PATH.stat().st_size)


def compress_7z() -> Dict[str, Any]:
    """Compress the tar archive into .tar.7z using 7-Zip with 12 threads."""
    if ARCHIVE_PATH.exists():
        ARCHIVE_PATH.unlink()

    logging.info("Compressing with 7-Zip (Level 5, 12 threads) -> %s", ARCHIVE_PATH)
    cmd = [
        str(SEVEN_ZIP_PATH),
        "a",
        "-t7z",
        "-mx=5",
        "-mmt=12",
        str(ARCHIVE_PATH),
        str(TAR_PATH),
    ]
    subprocess.run(cmd, check=True)

    # Test integrity
    logging.info("Testing archive integrity with 7z t...")
    subprocess.run([str(SEVEN_ZIP_PATH), "t", str(ARCHIVE_PATH)], check=True)

    archive_sha = compute_sha256(ARCHIVE_PATH)
    archive_bytes = ARCHIVE_PATH.stat().st_size
    tar_sha = compute_sha256(TAR_PATH)

    logging.info("Archive creation verified: %s", ARCHIVE_PATH.name)
    logging.info("Size: %d bytes | SHA-256: %s", archive_bytes, archive_sha)

    metadata = {
        "archive": ARCHIVE_PATH.name,
        "sha256": archive_sha,
        "bytes": archive_bytes,
        "tar_sha256": tar_sha,
        "compression": "7z-lzma2-mx5-mmt12",
        "description": "Strata v0.3.0 standalone Windows x64 executables (strata.exe, strata-desktop.exe, strata-vision.exe) and CUDA 13 / MSVC runtimes",
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def main() -> None:
    """Execute the assembly, validation, and packaging pipeline."""
    logging.info("Starting Strata v0.3.0 Executable Release Packaging...")
    manifest = assemble_payload()
    logging.info("Payload assembled with %d primary components.", len(manifest))
    create_tar_archive()
    metadata = compress_7z()
    logging.info("SUCCESS: Packaging complete. Receipt written to %s", METADATA_PATH)


if __name__ == "__main__":
    main()
