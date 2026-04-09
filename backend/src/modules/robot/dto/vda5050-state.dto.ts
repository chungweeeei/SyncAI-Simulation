import { ApiProperty } from '@nestjs/swagger';

export enum OperatingMode {
  AUTO = 'AUTO',
  MANUAL = 'MANUAL',
  MAINTENANCE = 'MAINTENANCE',
}

export class AgvPositionDto {
  @ApiProperty({ description: 'X coordinate' })
  x: number;

  @ApiProperty({ description: 'Y coordinate' })
  y: number;

  @ApiProperty({ description: 'Orientation angle (rad)' })
  theta: number;

  @ApiProperty({ description: 'Map identifier' })
  mapId: string;

  @ApiProperty({ description: 'Whether the position has been initialized' })
  positionInitialized: boolean;
}

export class VelocityDto {
  @ApiProperty({ description: 'Linear velocity in x direction (m/s)' })
  vx: number;

  @ApiProperty({ description: 'Angular velocity (rad/s)' })
  omega: number;
}

export class BatteryStateDto {
  @ApiProperty({ description: 'Battery charge percentage' })
  batteryCharge: number;

  @ApiProperty({ description: 'Whether the battery is charging' })
  charging: boolean;

  @ApiProperty({ description: 'Battery voltage (V)' })
  batteryVoltage: number;
}

export class Vda5050StateDto {
  @ApiProperty({ description: 'Unix timestamp' })
  timestamp: number;

  @ApiProperty({ description: 'VDA5050 protocol version' })
  version: string;

  @ApiProperty({ description: 'AGV manufacturer' })
  manufacturer: string;

  @ApiProperty({ description: 'AGV serial number' })
  serialNumber: string;

  @ApiProperty({ type: AgvPositionDto })
  agvPosition: AgvPositionDto;

  @ApiProperty({ type: VelocityDto })
  velocity: VelocityDto;

  @ApiProperty({ type: BatteryStateDto })
  batteryState: BatteryStateDto;

  @ApiProperty({ enum: OperatingMode, description: 'Current operating mode' })
  operatingMode: OperatingMode;

  @ApiProperty({ description: 'Whether the AGV is paused' })
  paused: boolean;
}
