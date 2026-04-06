export interface Pose {
  x: number;
  y: number;
  yaw: number;
}

export interface Twist {
  vx: number;
  vy: number;
  omega: number;
}

export interface Battery {
  percentage: number;
  voltage: number;
}

export interface RobotState {
  robotId: string;
  robotName: string;
  model: string;
  map: string;
  pose: Pose;
  twist: Twist;
  battery: Battery;
  timestamp: number;
}

export interface RobotConfig {
  robotId: string;
  robotName: string;
  model: string;
}
