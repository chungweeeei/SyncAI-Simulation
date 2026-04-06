import { Module } from '@nestjs/common';
import { RobotController } from './robot.controller';
import { RobotService } from './robot.service';
import { RobotGrpcClient } from './robot-grpc.client';

@Module({
  controllers: [RobotController],
  providers: [RobotService, RobotGrpcClient],
  exports: [RobotService],
})
export class RobotModule {}
