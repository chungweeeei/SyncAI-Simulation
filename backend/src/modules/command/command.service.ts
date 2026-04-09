import { Injectable } from '@nestjs/common';
import {
  CommandGrpcClient,
  CommandResponsePayload,
} from './command-grpc.client';
import { SendCommandDto } from './dto/send-command.dto';

@Injectable()
export class CommandService {
  constructor(private readonly commandGrpcClient: CommandGrpcClient) {}

  async sendCommand(dto: SendCommandDto): Promise<CommandResponsePayload> {
    return this.commandGrpcClient.sendCommand({
      deviceId: dto.deviceId,
      command: dto.command,
      timeoutSec: dto.timeoutSec,
      modbus: dto.modbus,
      rest: dto.rest
        ? {
            method: dto.rest.method,
            url: dto.rest.url,
            body: dto.rest.body ? JSON.stringify(dto.rest.body) : '',
            headers: dto.rest.headers,
          }
        : undefined,
    });
  }
}
