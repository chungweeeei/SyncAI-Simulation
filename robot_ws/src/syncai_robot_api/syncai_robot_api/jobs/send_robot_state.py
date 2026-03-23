import time
import structlog
import threading

from syncai_robot_api.repositories.robot.robot import RobotRepo

from syncai_robot_api.gateways.agent import AgentGateway

class SendRobotStateJob:
    def __init__(self, 
        logger: structlog.stdlib.BoundLogger,
        robot_repo: RobotRepo,
        agent_gateway: AgentGateway
    ):
        self._logger = logger

        self._robot_repo = robot_repo
        self._agent_gateway = agent_gateway

    def register(self, start_delay: float, interval: float):
        self._logger.info(
            "[SendRobotStateJob][register] Registering send robot state job"
        )
        self._start_delay = start_delay
        self._interval = interval

        job = threading.Thread(target=self.run, daemon=True)
        job.start()

    def run(self):
        time.sleep(self._start_delay)

        while True:
            current_robot_state = self._robot_repo.get_robot_state()
            if current_robot_state is None:
                time.sleep(self._interval)
                continue

            try:
                self._agent_gateway.send_robot_state(current_robot_state)
            except Exception as err:
                self._logger.error(f"[SendRobotStateJob][run] Failed to send robot state to agent: {str(err)}")

            time.sleep(self._interval)


def init_send_robot_state_job(
        logger: structlog.stdlib.BoundLogger, 
        robot_repo: RobotRepo, 
        agent_gateway: AgentGateway
    ) -> None:
    job =  SendRobotStateJob(logger=logger, robot_repo=robot_repo, agent_gateway=agent_gateway)
    job.register(start_delay=3.0, interval=1.0)