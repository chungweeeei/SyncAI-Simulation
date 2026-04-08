import { Injectable } from '@nestjs/common';
import { CommandGrpcClient } from '../command/command-grpc.client';
import { MapPayload, MapPoseRaw } from './interfaces/map.interface';

interface MapPayloadRaw {
  mapMetadata: {
    mapId: string;
    resolution: number;
    width: number;
    height: number;
    origin: MapPoseRaw;
  };
  vertexes: { name: string; pose: MapPoseRaw }[];
}

@Injectable()
export class MapService {
  constructor(private readonly commandGrpcClient: CommandGrpcClient) {}

  async getMap(): Promise<MapPayload> {
    const response = await this.commandGrpcClient.sendCommand({
      deviceId: '',
      command: 'get_map',
      timeoutSec: 10,
      rest: {
        method: 'GET',
        path: '/api/map',
        body: '',
      },
    });

    if (!response.success) {
      throw new Error(`GetMap failed: ${response.message}`);
    }

    const raw = JSON.parse(response.data) as MapPayloadRaw;
    return this.transformMapPayload(raw);
  }

  private transformMapPayload(raw: MapPayloadRaw): MapPayload {
    return {
      mapMetadata: {
        ...raw.mapMetadata,
        origin: {
          x: raw.mapMetadata.origin.x,
          y: raw.mapMetadata.origin.y,
          theta: raw.mapMetadata.origin.yaw,
        },
      },
      vertexes: raw.vertexes.map((v) => ({
        name: v.name,
        pose: { x: v.pose.x, y: v.pose.y, theta: v.pose.yaw },
      })),
    };
  }
}
