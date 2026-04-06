import { Module } from '@nestjs/common';
import { RobotModule } from './modules/robot/robot.module';

@Module({
  imports: [RobotModule],
  controllers: [],
  providers: [],
})
export class AppModule {}
