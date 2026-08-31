from functools import lru_cache
from pathlib import Path, PurePosixPath

import yaml

from app.skills.models import SkillMetadata


class SkillRegistryError(ValueError):
    pass


class SkillAccessError(SkillRegistryError):
    pass


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise SkillRegistryError("SKILL.md 缺少 YAML frontmatter")
    _, raw_metadata, _ = text.split("---", maxsplit=2)
    data = yaml.safe_load(raw_metadata) or {}
    if not isinstance(data.get("name"), str) or not isinstance(
        data.get("description"), str
    ):
        raise SkillRegistryError("SKILL.md 必须包含 name 和 description")
    return data


class SkillRegistry:
    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()
        self._skills = {skill.name: skill for skill in self.discover()}

    def discover(self) -> tuple[SkillMetadata, ...]:
        if not self.root.exists():
            return ()
        discovered: list[SkillMetadata] = []
        for skill_file in sorted(self.root.glob("*/SKILL.md")):
            text = skill_file.read_text(encoding="utf-8")
            metadata = _frontmatter(text)
            discovered.append(
                SkillMetadata(
                    name=metadata["name"],
                    description=metadata["description"],
                    root=skill_file.parent.resolve(),
                )
            )
        return tuple(discovered)

    def catalog_prompt(self) -> str:
        if not self._skills:
            return "当前没有已登记的 Skill。"
        lines = ["可用 Skills："]
        lines.extend(
            f"- {skill.name}: {skill.description}"
            for skill in self._skills.values()
        )
        return "\n".join(lines)

    @lru_cache(maxsize=64)
    def read_file(self, skill_name: str, relative_path: str) -> str:
        skill = self._skills.get(skill_name)
        if skill is None:
            raise SkillAccessError(f"未登记的 Skill: {skill_name}")

        posix_path = PurePosixPath(relative_path.replace("\\", "/"))
        if posix_path.is_absolute() or ".." in posix_path.parts:
            raise SkillAccessError("Skill 文件路径不合法")
        if posix_path.as_posix() != "SKILL.md" and (
            len(posix_path.parts) < 2 or posix_path.parts[0] != "references"
        ):
            raise SkillAccessError("只允许读取 SKILL.md 或 references 目录")

        target = (skill.root / Path(*posix_path.parts)).resolve()
        try:
            target.relative_to(skill.root)
        except ValueError as error:
            raise SkillAccessError("Skill 文件路径越界") from error
        if not target.is_file():
            raise SkillAccessError(f"Skill 文件不存在: {relative_path}")
        return target.read_text(encoding="utf-8")