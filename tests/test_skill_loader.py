"""Tests for src/skill_runtime/loader.py — atom 6.1."""
import pytest
from src.skill_runtime.loader import load_skill, load_all_skills


@pytest.mark.unit
def test_load_skill(tmp_path):
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "config.yaml").write_text('name: "Test"\ntype: executor\ndescription: "x"\n')
    (skill_dir / "prompt.md").write_text("You are a test skill.\n")

    skill = load_skill("test-skill", tmp_path)
    assert skill.config.name == "Test"
    assert skill.config.type == "executor"
    assert "test skill" in skill.system_prompt.lower()
    assert skill.skill_id == "test-skill"


@pytest.mark.unit
def test_load_skill_no_prompt(tmp_path):
    skill_dir = tmp_path / "no-prompt"
    skill_dir.mkdir()
    (skill_dir / "config.yaml").write_text('name: "NP"\ntype: executor\ndescription: "x"\n')

    skill = load_skill("no-prompt", tmp_path)
    assert skill.system_prompt == ""


@pytest.mark.unit
def test_load_skill_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_skill("nonexistent", tmp_path)


@pytest.mark.unit
def test_load_all_skills(tmp_path):
    for name in ["a-skill", "b-skill"]:
        d = tmp_path / name
        d.mkdir()
        (d / "config.yaml").write_text(f'name: "{name}"\ntype: executor\ndescription: "x"\n')
        (d / "prompt.md").write_text(f"Prompt for {name}")

    skills = load_all_skills(tmp_path)
    assert len(skills) == 2
    assert "a-skill" in skills
    assert "b-skill" in skills
