import { Controller, Get, NotFoundException } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { RobotService } from './robot.service';

@ApiTags('Robot')
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
