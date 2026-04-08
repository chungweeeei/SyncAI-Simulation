import { Module } from '@nestjs/common';
import { CommandGrpcClient } from './command-grpc.client';
import { CommandService } from './command.service';
import { CommandController } from './command.controller';

@Module({
  controllers: [CommandController],
  providers: [CommandGrpcClient, CommandService],
  exports: [CommandGrpcClient],
})
export class CommandModule {}
