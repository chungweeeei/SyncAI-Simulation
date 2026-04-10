import json
import os
from rclpy.impl.rcutils_logger import RcutilsLogger

from confluent_kafka import Producer

from typing import Optional

from syncai_iot_collector.gateways.agent_schema import build_building_event, EventDetail, EventSeverity


class AgentGateway: 

    def __init__(self, logger: RcutilsLogger):
        self._logger = logger
        self._server_ip = os.getenv("SYNCAI_SERVER_IP", "10.8.140.105")
        self._producer: Optional[Producer] = None

    def _ensure_connected(self) -> bool:
        if self._producer is not None:
            return True

        try:
            self._producer = Producer({
                "bootstrap.servers": self._server_ip,
                "client.id": "syncai-iot-collector",
            })
            self._logger.info(f"[AgentGateway] Kafka producer created, broker={self._server_ip}")
            return True
        except Exception as err:
            self._producer = None
            self._logger.warning(f"[AgentGateway] Kafka producer creation failed, error={err}")
            return False

    def _on_delivery(self, err, msg):
        if err is None:
            return

        self._logger.warning(f"[AgentGateway] Delivery failed, error={err}")

    def send_building_event(self, severity: EventSeverity, detail: EventDetail, location: str = "lobby"):
        if not self._ensure_connected():
            return

        event = build_building_event(severity=severity, detail=detail, location=location)
        event = event.json(by_alias=True)

        payload = json.dumps(event)

        try:
            self._producer.produce(
                topic="building-events",
                key=detail.device_id,
                value=payload,
                callback=self._on_delivery,
            )
            self._producer.poll(0)
        except Exception as err:
            self._logger.warning(f"[AgentGateway] Produce failed, error={err}")

    def disconnect(self):
        if self._producer:
            self._producer.flush(timeout=5.0)
            self._producer = None


def init_agent_gateway(logger: RcutilsLogger) -> AgentGateway:
    return AgentGateway(logger=logger)
