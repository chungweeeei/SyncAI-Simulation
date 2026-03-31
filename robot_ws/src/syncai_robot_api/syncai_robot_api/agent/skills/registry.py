from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from syncai_robot_api.repositories.task.schema import StepType


@dataclass
class SkillDefinition:
    name: str
    description: str
    step_type: StepType
    params: dict
    instructions: str


class SkillRegistry:

    def __init__(self, skills_dir: Optional[Path] = None):
        if skills_dir is None:
            skills_dir = Path(__file__).parent
        self._skills: Dict[str, SkillDefinition] = {}
        self._load_skills(skills_dir)

    def _load_skills(self, skills_dir: Path):
        for md_file in sorted(skills_dir.glob("*.md")):
            skill = self._parse_skill_file(md_file)
            if skill:
                self._skills[skill.name] = skill

    def _parse_skill_file(self, path: Path) -> Optional[SkillDefinition]:
        text = path.read_text(encoding="utf-8")

        if not text.startswith("---"):
            return None

        parts = text.split("---", 2)
        if len(parts) < 3:
            return None

        frontmatter = yaml.safe_load(parts[1])
        instructions = parts[2].strip()

        return SkillDefinition(
            name=frontmatter["name"],
            description=frontmatter["description"],
            step_type=StepType(frontmatter["step_type"]),
            params=frontmatter.get("params", {}),
            instructions=instructions,
        )

    def get(self, name: str) -> Optional[SkillDefinition]:
        return self._skills.get(name)

    def get_all(self) -> List[SkillDefinition]:
        return list(self._skills.values())

    def build_prompt_context(self) -> str:
        lines = []
        for skill in self._skills.values():
            params_desc = ", ".join(
                f"{k}: {v['type']} ({v['description']})"
                for k, v in skill.params.items()
            )
            lines.append(
                f"## Skill: {skill.name}\n"
                f"Description: {skill.description}\n"
                f"Parameters: {params_desc}\n"
                f"{skill.instructions}\n"
            )
        return "\n".join(lines)
