import { Module } from '@nestjs/common';
import { MapController } from './map.controller';
import { MapService } from './map.service';
import { MapGrpcClient } from './map-grpc.client';

@Module({
  controllers: [MapController],
  providers: [MapService, MapGrpcClient],
  exports: [MapService],
})
export class MapModule {}
