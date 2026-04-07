import {
  Injectable,
  Logger,
  OnModuleDestroy,
  OnModuleInit,
} from '@nestjs/common';
import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';
import { join } from 'path';
import { RobotService } from './robot.service';
import { RobotState } from './interfaces/robot-state.interface';

interface BridgeServiceClient extends grpc.Client {
  subscribeRobotState(
    request: Record<string, never>,
  ): grpc.ClientReadableStream<RobotState>;
}

interface BridgeProtoDefinition {
  bridge: {
    BridgeService: new (
      address: string,
      credentials: grpc.ChannelCredentials,
    ) => BridgeServiceClient;
  };
}

@Injectable()
export class RobotGrpcClient implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(RobotGrpcClient.name);
  private client: BridgeServiceClient | null = null;
  private stream: grpc.ClientReadableStream<RobotState> | null = null;
  private isShuttingDown = false;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

  constructor(private readonly robotService: RobotService) {}

  onModuleInit(): void {
    this.connect();
  }

  onModuleDestroy(): void {
    this.isShuttingDown = true;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    if (this.stream) {
      this.stream.cancel();
    }
    if (this.client) {
      this.client.close();
    }
  }

  private initClient(): void {
    const protoPath = join(process.cwd(), 'proto', 'bridge.proto');
    const packageDefinition = protoLoader.loadSync(protoPath, {
      keepCase: false, // Convert field names to camelCase
      longs: Number,
      enums: String,
      defaults: true,
      oneofs: true,
    });
    const proto = grpc.loadPackageDefinition(
      packageDefinition,
    ) as unknown as BridgeProtoDefinition;

    // default to localhost:50051 if not set in environment variables
    const bridgeAddress = process.env.BRIDGE_GRPC_ADDRESS ?? 'syncai-robot01:50051';

    this.client = new proto.bridge.BridgeService(
      bridgeAddress,
      grpc.credentials.createInsecure(),
    );

    this.logger.log(`gRPC client initialized, target: ${bridgeAddress}`);
  }

  private connect(): void {
    if (this.isShuttingDown) return;

    this.cleanup();

    try {
      this.initClient();
    } catch (err) {
      this.logger.error(
        `Failed to initialize gRPC client: ${err instanceof Error ? err.message : err}`,
      );
      this.scheduleReconnect();
      return;
    }

    this.subscribe();
  }

  private cleanup(): void {
    if (this.stream) {
      this.stream.removeAllListeners();
      this.stream.cancel();
      this.stream = null;
    }
    if (this.client) {
      this.client.close();
      this.client = null;
    }
  }

  private subscribe(): void {
    if (this.isShuttingDown || !this.client) return;

    this.logger.log('Subscribing to BridgeService.SubscribeRobotState...');

    this.stream = this.client.subscribeRobotState({});

    this.stream.on('data', (data: RobotState) => {
      console.log('Received robot state update:', data);
      this.robotService.updateState(data);
    });

    this.stream.on('error', (err: grpc.ServiceError) => {
      if (this.isShuttingDown) return;
      if (err.code === grpc.status.UNAVAILABLE) {
        this.logger.warn('Bridge unreachable, will retry...');
      } else {
        this.logger.error(
          `gRPC stream error: ${err.message} (code: ${err.code})`,
        );
      }
      this.scheduleReconnect();
    });

    this.stream.on('end', () => {
      if (this.isShuttingDown) return;
      this.logger.warn('gRPC stream ended, reconnecting...');
      this.scheduleReconnect();
    });
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimeout) return;
    this.logger.log('Reconnecting in 5000ms...');
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectTimeout = null;
      this.connect();
    }, 5000);
  }
}
