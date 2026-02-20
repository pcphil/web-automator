"""Skill loader utilities — discover and read markdown playbooks from the skills/ folder."""

from __future__ import annotations

import os
import pathlib


def get_skills_dir() -> pathlib.Path:
    return pathlib.Path(os.getenv("SKILLS_DIR", "skills"))


def list_skills() -> list[str]:
    d = get_skills_dir()
    if not d.exists():
        return []
    return [
        str(p.relative_to(d).with_suffix("")).replace("\\", "/")
        for p in sorted(d.rglob("*.md"))
    ]


def read_skill(name: str) -> str:
    d = get_skills_dir()
    p = d / f"{name}.md"
    if not p.exists():
        return f"Skill {name!r} not found. Available: {list_skills()}"
    return p.read_text(encoding="utf-8")
