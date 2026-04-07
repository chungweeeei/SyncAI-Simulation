export enum OperatingMode {
  AUTO = 'AUTO',
  MANUAL = 'MANUAL',
  MAINTENANCE = 'MAINTENANCE',
}

export class AgvPositionDto {
  x: number;
  y: number;
  theta: number;
  mapId: string;
  positionInitialized: boolean;
}

export class VelocityDto {
  vx: number;
  omega: number;
}

export class BatteryStateDto {
  batteryCharge: number;
  charging: boolean;
  batteryVoltage: number;
}

export class Vda5050StateDto {
  timestamp: number;
  version: string;
  manufacturer: string;
  serialNumber: string;
  agvPosition: AgvPositionDto;
  velocity: VelocityDto;
  batteryState: BatteryStateDto;
  operatingMode: OperatingMode;
  paused: boolean;
}
