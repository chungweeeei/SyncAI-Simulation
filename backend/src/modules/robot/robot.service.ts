import { Injectable } from '@nestjs/common';
import { RobotConfig, RobotState } from './interfaces/robot-state.interface';

@Injectable()
export class RobotService {
  private robotState: RobotState | null = null;

  private readonly mockConfig: RobotConfig = {
    robotId: 'robot-001',
    robotName: 'SyncBot',
    model: 'AMR-100',
  };

  updateState(state: RobotState): void {
    this.robotState = state;
  }

  getState(): RobotState | null {
    return this.robotState;
  }

  getConfig(): RobotConfig {
    return this.mockConfig;
  }
}
