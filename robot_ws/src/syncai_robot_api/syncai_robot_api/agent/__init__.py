import structlog
from fastapi import APIRouter

from syncai_robot_api.agent.llm.client import LLMClient
from syncai_robot_api.agent.skills.registry import SkillRegistry
from syncai_robot_api.agent.nlp.vertex_resolver import VertexResolver
from syncai_robot_api.agent.nlp.task_planner import TaskPlannerService
from syncai_robot_api.repositories.robot.robot import RobotRepo
from syncai_robot_api.repositories.task.task import TaskRepo
from syncai_robot_api.gateways.robot import RobotGateway
from syncai_robot_api.routers.agent import init_agent_router


def init_agent(
    logger: structlog.stdlib.BoundLogger,
    robot_repo: RobotRepo,
    task_repo: TaskRepo,
    robot_gateway: RobotGateway,
    robot_id: str,
    map_name: str,
) -> APIRouter:
    # skills
    skill_registry = SkillRegistry()

    # vertexes
    vertex_resolver = VertexResolver(map_name)

    # LLM Client
    llm_client = LLMClient()

    # Task Planner
    task_planner = TaskPlannerService(
        logger=logger,
        llm_client=llm_client,
        skill_registry=skill_registry,
        vertex_resolver=vertex_resolver,
        robot_repo=robot_repo,
    )

    logger.info(
        "[Agent] Initialized",
        skills=len(skill_registry.get_all()),
        vertices=len(vertex_resolver.get_all_vertices()),
    )

    return init_agent_router(
        task_planner=task_planner,
        task_repo=task_repo,
        robot_gateway=robot_gateway,
        robot_id=robot_id,
    )
