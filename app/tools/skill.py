from langchain_core.tools import BaseTool, tool

from app.skills.registry import SkillAccessError, SkillRegistry


def create_skill_tools(registry: SkillRegistry) -> list[BaseTool]:
    @tool
    def read_skill_file(skill_name: str, relative_path: str) -> str:
        """读取已登记 Skill 的 SKILL.md 或 references 文件；不能读取其他路径。"""
        try:
            return registry.read_file(skill_name, relative_path)
        except SkillAccessError as error:
            return f"Skill 文件读取失败：{error}"

    return [read_skill_file]