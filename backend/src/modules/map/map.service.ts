import { Injectable } from '@nestjs/common';
import { CommandGrpcClient } from '../command/command-grpc.client';
import { MapPayload } from './interfaces/map.interface';

@Injectable()
export class MapService {
  private readonly robotApiUrl =
    process.env.ROBOT_API_URL ?? 'http://localhost:3000';

  constructor(private readonly commandGrpcClient: CommandGrpcClient) {}

  async getMap(): Promise<MapPayload> {
    const response = await this.commandGrpcClient.sendCommand({
      deviceId: '',
      command: 'get_map',
      timeoutSec: 10,
      rest: {
        method: 'GET',
        url: `${this.robotApiUrl}/api/v1/map`,
        body: '',
      },
    });

    if (!response.success) {
      throw new Error(`GetMap failed: ${response.message}`);
    }

    return JSON.parse(response.data) as MapPayload;
  }
}
