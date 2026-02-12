"""Tests for src/config_loader.py — atom 0.5."""
import pytest
from pathlib import Path

from src.config_loader import SkillConfig, load_skills


@pytest.mark.unit
def test_load_skills_finds_task_manager(tmp_path):
    skill_dir = tmp_path / "task-manager"
    skill_dir.mkdir()
    config = skill_dir / "config.yaml"
    config.write_text(
        """
name: "Задачник"
type: executor
description: "Управление задачами"
llm:
  provider: anthropic
  model: haiku
  max_tokens: 1000
  temperature: 0.3
tools:
  - todoist_api
  - ask_user
priority: 2
triggers:
  - "задача"
  - "напомни"
cron:
  - schedule: "0 8 * * *"
    intent: "Показать задачи"
    silent: false
""",
        encoding="utf-8",
    )

    registry = load_skills(tmp_path)
    assert "task-manager" in registry
    skill = registry["task-manager"]
    assert skill.name == "Задачник"
    assert skill.type == "executor"
    assert skill.priority == 2
    assert "задача" in skill.triggers
    assert len(skill.cron) == 1
    assert skill.llm["model"] == "haiku"


@pytest.mark.unit
def test_load_skills_empty_dir(tmp_path):
    registry = load_skills(tmp_path)
    assert registry == {}


@pytest.mark.unit
def test_load_skills_nonexistent_dir():
    registry = load_skills("/nonexistent/path")
    assert registry == {}


@pytest.mark.unit
def test_load_skills_multiple(tmp_path):
    for name, stype in [("a-skill", "executor"), ("b-skill", "expert")]:
        d = tmp_path / name
        d.mkdir()
        (d / "config.yaml").write_text(
            f'name: "{name}"\ntype: {stype}\ndescription: "test"\n',
            encoding="utf-8",
        )

    registry = load_skills(tmp_path)
    assert len(registry) == 2
    assert registry["a-skill"].type == "executor"
    assert registry["b-skill"].type == "expert"
