import {
  Injectable,
  Logger,
  OnModuleDestroy,
  OnModuleInit,
} from '@nestjs/common';
import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';
import { join } from 'path';

export interface CommandRequestParams {
  deviceId: string;
  command: string;
  timeoutSec: number;
  rest?: { method: string; path: string; body: string };
  modbus?: { unitId: number; address: number };
}

export interface CommandResponsePayload {
  success: boolean;
  message: string;
  data: string;
}

interface CommandServiceClient extends grpc.Client {
  sendCommand(
    request: CommandRequestParams,
    callback: (
      error: grpc.ServiceError | null,
      response: CommandResponsePayload,
    ) => void,
  ): void;
}

interface CommandProtoDefinition {
  bridge: {
    CommandService: new (
      address: string,
      credentials: grpc.ChannelCredentials,
    ) => CommandServiceClient;
  };
}

@Injectable()
export class CommandGrpcClient implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(CommandGrpcClient.name);
  private client: CommandServiceClient | null = null;

  onModuleInit(): void {
    this.initClient();
  }

  onModuleDestroy(): void {
    if (this.client) {
      this.client.close();
    }
  }

  private initClient(): void {
    const protoPath = join(process.cwd(), 'proto', 'command.proto');
    const packageDefinition = protoLoader.loadSync(protoPath, {
      keepCase: false,
      longs: Number,
      enums: String,
      defaults: true,
      oneofs: true,
    });
    const proto = grpc.loadPackageDefinition(
      packageDefinition,
    ) as unknown as CommandProtoDefinition;

    const bridgeAddress = process.env.BRIDGE_GRPC_ADDRESS ?? 'localhost:50051';

    this.client = new proto.bridge.CommandService(
      bridgeAddress,
      grpc.credentials.createInsecure(),
    );

    this.logger.log(
      `CommandService gRPC client initialized, target: ${bridgeAddress}`,
    );
  }

  sendCommand(params: CommandRequestParams): Promise<CommandResponsePayload> {
    return new Promise((resolve, reject) => {
      if (!this.client) {
        reject(new Error('CommandService gRPC client not initialized'));
        return;
      }

      this.client.sendCommand(params, (error, response) => {
        if (error) {
          this.logger.error(`SendCommand gRPC call failed: ${error.message}`);
          reject(error);
          return;
        }

        resolve(response);
      });
    });
  }
}
