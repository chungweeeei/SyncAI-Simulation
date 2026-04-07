import { Controller, Get, NotFoundException } from '@nestjs/common';
import { RobotService } from './robot.service';

@Controller('robot')
export class RobotController {
  constructor(private readonly robotService: RobotService) {}

  @Get('state')
  getState() {
    const state = this.robotService.getVda5050State();
    if (!state) {
      throw new NotFoundException('Robot state not available');
    }
    return state;
  }

  @Get('config')
  getConfig() {
    return { data: this.robotService.getConfig() };
  }
}
