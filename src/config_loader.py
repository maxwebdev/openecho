"""OpenEcho Config Loader — atom 0.5.

Scans skills/*/config.yaml, parses them, returns a skill registry.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SkillConfig:
    """Parsed skill configuration."""

    name: str
    type: str  # executor | expert
    description: str
    llm: dict[str, Any] = field(default_factory=dict)
    tools: list[str] = field(default_factory=list)
    priority: int = 5
    triggers: list[str] = field(default_factory=list)
    cron: list[dict[str, Any]] = field(default_factory=list)
    path: Path = field(default_factory=lambda: Path("."))

    @classmethod
    def from_yaml(cls, path: Path) -> "SkillConfig":
        """Load from a config.yaml file."""
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        return cls(
            name=raw["name"],
            type=raw["type"],
            description=raw.get("description", ""),
            llm=raw.get("llm", {}),
            tools=raw.get("tools", []),
            priority=raw.get("priority", 5),
            triggers=raw.get("triggers", []),
            cron=raw.get("cron", []),
            path=path.parent,
        )


def load_skills(skills_dir: str | Path = "skills") -> dict[str, SkillConfig]:
    """Scan *skills_dir* for config.yaml files and return a registry.

    Returns mapping: folder-name -> SkillConfig.
    """
    base = Path(skills_dir)
    registry: dict[str, SkillConfig] = {}
    if not base.exists():
        return registry
    for config_path in sorted(base.glob("*/config.yaml")):
        skill_id = config_path.parent.name
        registry[skill_id] = SkillConfig.from_yaml(config_path)
    return registry
