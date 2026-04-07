import { RobotState } from './interfaces/robot-state.interface';
import {
  AgvPositionDto,
  BatteryStateDto,
  OperatingMode,
  Vda5050StateDto,
  VelocityDto,
} from './dto/vda5050-state.dto';

export function buildVda5050State(state: RobotState): Vda5050StateDto {
  const agvPosition = new AgvPositionDto();
  agvPosition.x = state.pose.x;
  agvPosition.y = state.pose.y;
  agvPosition.theta = state.pose.yaw;
  agvPosition.mapId = state.map;
  agvPosition.positionInitialized = true;

  const velocity = new VelocityDto();
  velocity.vx = state.twist.vx;
  velocity.omega = state.twist.omega;

  const batteryState = new BatteryStateDto();
  batteryState.batteryCharge = state.battery.percentage;
  batteryState.batteryVoltage = state.battery.voltage;
  batteryState.charging = false;

  const vda5050State = new Vda5050StateDto();
  vda5050State.timestamp = state.timestamp;
  vda5050State.version = '0.0.0';
  vda5050State.manufacturer = 'SyncRobotic';
  vda5050State.serialNumber = state.robotId;
  vda5050State.agvPosition = agvPosition;
  vda5050State.velocity = velocity;
  vda5050State.batteryState = batteryState;
  vda5050State.operatingMode = OperatingMode.AUTO;
  vda5050State.paused = false;

  return vda5050State;
}
