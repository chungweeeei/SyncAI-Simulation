import { Injectable } from '@nestjs/common';
import { RobotConfig, RobotState } from './interfaces/robot-state.interface';
import { Vda5050StateDto } from './dto/vda5050-state.dto';
import { buildVda5050State } from './robot.aggregate';

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

  getVda5050State(): Vda5050StateDto | null {
    if (!this.robotState) {
      return null;
    }
    return buildVda5050State(this.robotState);
  }

  getConfig(): RobotConfig {
    return this.mockConfig;
  }
}
