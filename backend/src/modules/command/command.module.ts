import { Module } from '@nestjs/common';
import { CommandGrpcClient } from './command-grpc.client';

@Module({
  providers: [CommandGrpcClient],
  exports: [CommandGrpcClient],
})
export class CommandModule {}
