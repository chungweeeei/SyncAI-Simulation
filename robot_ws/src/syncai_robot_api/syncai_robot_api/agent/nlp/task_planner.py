import json
import uuid
from typing import List

import structlog

from syncai_robot_api.agent.llm.client import LLMClient
from syncai_robot_api.agent.llm.prompts import build_system_prompt, build_user_prompt
from syncai_robot_api.agent.llm.schemas import TaskPlan, PlannedStep
from syncai_robot_api.agent.skills.registry import SkillRegistry
from syncai_robot_api.agent.nlp.vertex_resolver import VertexResolver
from syncai_robot_api.repositories.robot.robot import RobotRepo
from syncai_robot_api.repositories.task.schema import (
    Step,
    StepType,
    MoveParams,
    WaitParams,
    DoorParams,
    ChargeParams,
    NavigateWithAlertParams,
)

PARAMS_MODEL_MAP = {
    StepType.MOVE: MoveParams,
    StepType.WAIT: WaitParams,
    StepType.DOOR: DoorParams,
    StepType.CHARGE: ChargeParams,
    StepType.NAVIGATE_WITH_ALERT: NavigateWithAlertParams,
}


class TaskPlannerService:

    def __init__(
        self,
        logger: structlog.stdlib.BoundLogger,
        llm_client: LLMClient,
        skill_registry: SkillRegistry,
        vertex_resolver: VertexResolver,
        robot_repo: RobotRepo,
    ):
        self._log = logger
        self._llm_client = llm_client
        self._skill_registry = skill_registry
        self._vertex_resolver = vertex_resolver
        self._robot_repo = robot_repo

    async def plan_task(self, command: str) -> TaskPlan:
        system_prompt = build_system_prompt(
            self._skill_registry,
            self._vertex_resolver.get_all_vertices(),
        )
        robot_state = self._robot_repo.get_robot_state()
        user_prompt = build_user_prompt(command, robot_state)

        self._log.info("[TaskPlanner] Calling LLM", command=command)
        raw_response = await self._llm_client.generate(system_prompt, user_prompt)

        plan = TaskPlan.model_validate_json(raw_response)

        # Validate all skill names exist in registry
        for step in plan.steps:
            if self._skill_registry.get(step.skill) is None:
                raise ValueError(f"Unknown skill: {step.skill}")

        self._log.info("[TaskPlanner] Plan generated", steps=len(plan.steps))
        return plan

    def convert_to_steps(self, plan: TaskPlan) -> List[Step]:
        steps = []
        for i, planned in enumerate(plan.steps):
            skill = self._skill_registry.get(planned.skill)
            if skill is None:
                raise ValueError(f"Unknown skill: {planned.skill}")

            params_model = PARAMS_MODEL_MAP[skill.step_type]
            params = params_model.model_validate(planned.params)

            steps.append(Step(
                id=str(uuid.uuid4())[:8],
                name=f"{planned.skill}_{i}",
                type=skill.step_type,
                params=params,
            ))

        return steps
