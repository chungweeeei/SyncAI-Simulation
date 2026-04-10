import { Module } from '@nestjs/common';
import { RobotModule } from './modules/robot/robot.module';
import { MapModule } from './modules/map/map.module';
import { TaskModule } from './modules/task/task.module';
import { CommandModule } from './modules/command/command.module';

@Module({
  imports: [RobotModule, MapModule, TaskModule, CommandModule],
  controllers: [],
  providers: [],
})
export class AppModule {}
