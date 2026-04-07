import { Module } from '@nestjs/common';
import { RobotModule } from './modules/robot/robot.module';
import { MapModule } from './modules/map/map.module';
import { TaskModule } from './modules/task/task.module';

@Module({
  imports: [RobotModule, MapModule, TaskModule],
  controllers: [],
  providers: [],
})
export class AppModule {}
