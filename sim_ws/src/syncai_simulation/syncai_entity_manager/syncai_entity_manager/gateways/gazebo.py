import math
import os
import re
from typing import Tuple

from ament_index_python.packages import get_package_share_directory
from rclpy.impl.rcutils_logger import RcutilsLogger
from gz.msgs10.boolean_pb2 import Boolean
from gz.msgs10.entity_factory_pb2 import EntityFactory
from gz.msgs10.entity_pb2 import Entity
from gz.msgs10.pose_pb2 import Pose
from gz.msgs10.quaternion_pb2 import Quaternion
from gz.msgs10.vector3d_pb2 import Vector3d
from gz.transport13 import Node


class GazeboGateway:

    def __init__(self, logger: RcutilsLogger):
        self._logger = logger
        self._world_name = os.environ.get('GZ_WORLD_NAME', 'demo_world')
        self._models_dir = os.path.join(
            get_package_share_directory('syncai_demo_gz'), 'models'
        )
        self._origin_x = float(os.environ.get('GZ_ORIGIN_X', '5.0'))
        self._origin_y = float(os.environ.get('GZ_ORIGIN_Y', '15.0'))
        self._node = Node()

    @property
    def models_dir(self) -> str:
        return self._models_dir

    @staticmethod
    def generate_box_sdf(name: str, sx: float, sy: float, sz: float) -> str:
        mass = max(sx * sy * sz * 1000.0, 0.1)  # density ~1000 kg/m³
        ixx = mass / 12.0 * (sy ** 2 + sz ** 2)
        iyy = mass / 12.0 * (sx ** 2 + sz ** 2)
        izz = mass / 12.0 * (sx ** 2 + sy ** 2)
        return f"""<?xml version="1.0" ?>
<sdf version="1.8">
  <model name="{name}">
    <static>true</static>
    <link name="link">
      <inertial>
        <mass>{mass}</mass>
        <inertia>
          <ixx>{ixx:.6f}</ixx><iyy>{iyy:.6f}</iyy><izz>{izz:.6f}</izz>
          <ixy>0</ixy><ixz>0</ixz><iyz>0</iyz>
        </inertia>
      </inertial>
      <visual name="visual">
        <geometry>
          <box><size>{sx} {sy} {sz}</size></box>
        </geometry>
        <material>
          <ambient>0.3 0.3 0.3 1</ambient>
          <diffuse>0.4 0.4 0.4 1</diffuse>
        </material>
      </visual>
      <collision name="collision">
        <geometry>
          <box><size>{sx} {sy} {sz}</size></box>
        </geometry>
      </collision>
    </link>
  </model>
</sdf>"""

    @staticmethod
    def _euler_to_quaternion(roll: float, pitch: float, yaw: float) -> Tuple[float, float, float, float]:
        cr = math.cos(roll / 2)
        sr = math.sin(roll / 2)
        cp = math.cos(pitch / 2)
        sp = math.sin(pitch / 2)
        cy = math.cos(yaw / 2)
        sy = math.sin(yaw / 2)

        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy
        return w, x, y, z

    @staticmethod
    def prepare_sdf(sdf_path: str, entity_name: str) -> str:
        try:
            with open(sdf_path, 'r') as f:
                sdf = f.read()
            return re.sub(
                r'<model\s+name="[^"]*"',
                f'<model name="{entity_name}"',
                sdf,
                count=1
            )
        except FileNotFoundError:
            raise FileNotFoundError(f'SDF file not found: {sdf_path}')

    def spawn_entity(
        self,
        sdf_string: str,
        entity_name: str,
        x: float, y: float, z: float,
        roll: float, pitch: float, yaw: float,
    ) -> Tuple[bool, str]:
        gx = x + self._origin_x
        gy = y + self._origin_y

        w, qx, qy, qz = self._euler_to_quaternion(roll, pitch, yaw)

        req = EntityFactory(
            sdf=sdf_string,
            name=entity_name,
            pose=Pose(
                position=Vector3d(x=gx, y=gy, z=z),
                orientation=Quaternion(w=w, x=qx, y=qy, z=qz),
            )
        )

        self._logger.info(f'[GazeboGateway] Spawning entity: {entity_name}')

        result, response = self._node.request(
            service=f'/world/{self._world_name}/create',
            request=req,
            request_type=EntityFactory,
            response_type=Boolean,
            timeout=5000,
        )

        if not result:
            msg = 'gz service call timed out or failed'
            self._logger.error(f'[GazeboGateway] Spawn failed: {entity_name}')
            return False, msg

        if not response.data:
            msg = 'Gazebo returned false for spawn request'
            self._logger.error(f'[GazeboGateway] Spawn rejected: {entity_name}')
            return False, msg

        self._logger.info(f'[GazeboGateway] Entity spawned: {entity_name}')
        return True, 'Entity spawned successfully'

    def delete_entity(self, entity_name: str) -> Tuple[bool, str]:
        req = Entity(
            name=entity_name,
            type=Entity.MODEL
        )

        self._logger.info(f'[GazeboGateway] Deleting entity: {entity_name}')

        result, response = self._node.request(
            service=f'/world/{self._world_name}/remove',
            request=req,
            request_type=Entity,
            response_type=Boolean,
            timeout=5000,
        )

        if not result:
            msg = 'gz service call timed out or failed'
            self._logger.error(f'[GazeboGateway] Delete failed: {entity_name}')
            return False, msg

        if not response.data:
            msg = 'Gazebo returned false for delete request'
            self._logger.error(f'[GazeboGateway] Delete rejected: {entity_name}')
            return False, msg

        self._logger.info(f'[GazeboGateway] Entity deleted: {entity_name}')
        return True, 'Entity deleted successfully'
