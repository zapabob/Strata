"""Use the checked-in resource guard with a fresh 0.5.8 output, retaining 0.5.7 evidence."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('H:/Strata/releases/stable-058-20261111-codex')

if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    spec = importlib.util.spec_from_file_location('stable058_guard_driver', ROOT / '_docs/stable-057-20261111/run.py')
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    driver.OUT = OUT
    raise SystemExit(driver.main())
