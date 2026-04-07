import { Injectable } from '@nestjs/common';
import { MapGrpcClient } from './map-grpc.client';
import { MapPayload } from './interfaces/map.interface';

@Injectable()
export class MapService {
  constructor(private readonly mapGrpcClient: MapGrpcClient) {}

  async getMap(): Promise<MapPayload> {
    return this.mapGrpcClient.getMap();
  }
}
