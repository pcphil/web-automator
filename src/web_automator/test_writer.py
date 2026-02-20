"""Utility for writing generated Playwright test files to disk."""

from __future__ import annotations

import os
import pathlib


def get_tests_dir() -> pathlib.Path:
    return pathlib.Path(os.getenv("TESTS_DIR", "generated_tests"))


def write_test(filename: str, content: str) -> str:
    d = get_tests_dir()
    d.mkdir(parents=True, exist_ok=True)
    p = d / filename
    p.write_text(content, encoding="utf-8")
    return f"Test written to {p.resolve()}"
