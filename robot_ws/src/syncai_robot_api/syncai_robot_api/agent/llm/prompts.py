from typing import List, Optional

from syncai_robot_api.agent.skills.registry import SkillRegistry
from syncai_robot_api.repositories.robot.schema import RobotState


def build_system_prompt(skill_registry: SkillRegistry, vertices: List[dict]) -> str:
    skills_context = skill_registry.build_prompt_context()

    vertices_context = ""
    if vertices:
        vertex_lines = []
        for v in vertices:
            pose = v.get("pose", {})
            vertex_lines.append(
                f"  - {v['name']}: x={pose.get('x', 0)}, y={pose.get('y', 0)}, theta={pose.get('theta', 0)}"
            )
        vertices_context = "## Map Locations (Vertices)\n" + "\n".join(vertex_lines)

    return f"""You are a robot task planner. Given a natural language command, you must produce a JSON plan using the available skills.

## Available Skills

{skills_context}

{vertices_context}

## Output Format

You MUST respond with valid JSON matching this exact schema:
{{
  "steps": [
    {{
      "skill": "<skill_name>",
      "params": {{ ... }}
    }}
  ]
}}

## Rules
- Only use skills from the available skills list above.
- Use the map vertex coordinates when the user refers to a named location.
- If a parameter has a default value and the user does not specify it, use the default.
- Do not add a separate move step before or after a skill that already includes navigation (e.g., charge). Use only the composite skill.
- Output ONLY the JSON object. No explanation, no markdown, no extra text.
"""


def build_user_prompt(command: str, robot_state: Optional[RobotState]) -> str:
    context = ""
    if robot_state:
        context = (
            f"\n\nCurrent robot state:\n"
            f"- Position: x={robot_state.pose.x:.2f}, y={robot_state.pose.y:.2f}, yaw={robot_state.pose.yaw:.2f} rad\n"
            f"- Battery: {robot_state.battery.percentage:.1f}%\n"
        )

    return f"Command: {command}{context}"
