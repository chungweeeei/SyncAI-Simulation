import {
  Injectable,
  Logger,
  OnModuleDestroy,
  OnModuleInit,
} from '@nestjs/common';
import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';
import { join } from 'path';
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

interface MapServiceClient extends grpc.Client {
  getMap(
    request: Record<string, never>,
    callback: (
      error: grpc.ServiceError | null,
      response: MapPayloadRaw,
    ) => void,
  ): void;
}

interface MapProtoDefinition {
  bridge: {
    MapService: new (
      address: string,
      credentials: grpc.ChannelCredentials,
    ) => MapServiceClient;
  };
}

@Injectable()
export class MapGrpcClient implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(MapGrpcClient.name);
  private client: MapServiceClient | null = null;

  onModuleInit(): void {
    this.initClient();
  }

  onModuleDestroy(): void {
    if (this.client) {
      this.client.close();
    }
  }

  private initClient(): void {
    const protoPath = join(process.cwd(), 'proto', 'map.proto');
    const packageDefinition = protoLoader.loadSync(protoPath, {
      keepCase: false,
      longs: Number,
      enums: String,
      defaults: true,
      oneofs: true,
    });
    const proto = grpc.loadPackageDefinition(
      packageDefinition,
    ) as unknown as MapProtoDefinition;

    const bridgeAddress = process.env.BRIDGE_GRPC_ADDRESS ?? 'localhost:50051';

    this.client = new proto.bridge.MapService(
      bridgeAddress,
      grpc.credentials.createInsecure(),
    );

    this.logger.log(
      `MapService gRPC client initialized, target: ${bridgeAddress}`,
    );
  }

  getMap(): Promise<MapPayload> {
    return new Promise((resolve, reject) => {
      if (!this.client) {
        reject(new Error('MapService gRPC client not initialized'));
        return;
      }

      this.client.getMap({} as Record<string, never>, (error, response) => {
        if (error) {
          this.logger.error(`GetMap gRPC call failed: ${error.message}`);
          reject(error);
          return;
        }

        const mapPayload: MapPayload = {
          mapMetadata: {
            ...response.mapMetadata,
            origin: {
              x: response.mapMetadata.origin.x,
              y: response.mapMetadata.origin.y,
              theta: response.mapMetadata.origin.yaw,
            },
          },
          vertexes: response.vertexes.map((v) => ({
            name: v.name,
            pose: { x: v.pose.x, y: v.pose.y, theta: v.pose.yaw },
          })),
        };

        resolve(mapPayload);
      });
    });
  }
}
