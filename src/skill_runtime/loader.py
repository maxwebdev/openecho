"""OpenEcho Skill Loader — atom 6.1.

Loads config.yaml + prompt.md into a ready-to-run skill instance.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config_loader import SkillConfig


@dataclass
class LoadedSkill:
    """A fully loaded skill ready for execution."""
    config: SkillConfig
    system_prompt: str
    skill_id: str


def load_skill(skill_id: str, skills_dir: str | Path = "skills") -> LoadedSkill:
    """Load a single skill by ID from the skills directory."""
    base = Path(skills_dir) / skill_id

    config_path = base / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Skill config not found: {config_path}")

    config = SkillConfig.from_yaml(config_path)

    prompt_path = base / "prompt.md"
    system_prompt = ""
    if prompt_path.exists():
        system_prompt = prompt_path.read_text(encoding="utf-8")

    return LoadedSkill(
        config=config,
        system_prompt=system_prompt,
        skill_id=skill_id,
    )


def load_all_skills(skills_dir: str | Path = "skills") -> dict[str, LoadedSkill]:
    """Load all skills from the skills directory."""
    base = Path(skills_dir)
    result: dict[str, LoadedSkill] = {}
    if not base.exists():
        return result
    for config_path in sorted(base.glob("*/config.yaml")):
        skill_id = config_path.parent.name
        result[skill_id] = load_skill(skill_id, skills_dir)
    return result
