from pathlib import Path

import pytest

from app.skills.registry import SkillAccessError, SkillRegistry


def create_skill(root: Path) -> None:
    skill = root / "legal-plain-explanation"
    references = skill / "references"
    references.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: legal-plain-explanation\n"
        "description: 将合同条款翻译为日常语言。\n"
        "---\n\n"
        "# 法律条款通俗解释\n",
        encoding="utf-8",
    )
    (references / "contract-terms.md").write_text(
        "# 合同术语\n",
        encoding="utf-8",
    )


def test_registry_preloads_only_name_and_description(tmp_path: Path) -> None:
    create_skill(tmp_path)
    registry = SkillRegistry(tmp_path)

    catalog = registry.catalog_prompt()

    assert "legal-plain-explanation" in catalog
    assert "将合同条款翻译为日常语言" in catalog
    assert "# 法律条款通俗解释" not in catalog


def test_registry_reads_registered_skill_files(tmp_path: Path) -> None:
    create_skill(tmp_path)
    registry = SkillRegistry(tmp_path)

    assert "# 法律条款通俗解释" in registry.read_file(
        "legal-plain-explanation",
        "SKILL.md",
    )
    assert "# 合同术语" in registry.read_file(
        "legal-plain-explanation",
        "references/contract-terms.md",
    )


@pytest.mark.parametrize(
    "relative_path",
    ["../secret.txt", "C:/Windows/win.ini", "references/../../secret.txt"],
)
def test_registry_rejects_paths_outside_skill(
    tmp_path: Path,
    relative_path: str,
) -> None:
    create_skill(tmp_path)
    registry = SkillRegistry(tmp_path)

    with pytest.raises(SkillAccessError):
        registry.read_file("legal-plain-explanation", relative_path)