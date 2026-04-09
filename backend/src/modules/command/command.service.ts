import { Injectable } from '@nestjs/common';
import { CommandGrpcClient } from './command-grpc.client';
import { SendCommandDto } from './dto/send-command.dto';
import { CommandResponseDto } from './dto/command-response.dto';

@Injectable()
export class CommandService {
  constructor(private readonly commandGrpcClient: CommandGrpcClient) {}

  async sendCommand(dto: SendCommandDto): Promise<CommandResponseDto> {
    const response = await this.commandGrpcClient.sendCommand({
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

    let parsedData: Record<string, any> | null = null;
    if (response.data) {
      try {
        parsedData = JSON.parse(response.data);
      } catch {
        parsedData = { raw: response.data };
      }
    }

    return {
      success: response.success,
      message: response.message,
      data: parsedData,
    };
  }
}
