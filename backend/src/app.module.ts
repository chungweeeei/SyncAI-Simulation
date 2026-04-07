import { Module } from '@nestjs/common';
import { RobotModule } from './modules/robot/robot.module';
import { MapModule } from './modules/map/map.module';

@Module({
  imports: [RobotModule, MapModule],
  controllers: [],
  providers: [],
})
export class AppModule {}
