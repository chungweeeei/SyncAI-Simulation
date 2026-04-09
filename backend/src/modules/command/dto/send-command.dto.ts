import {
  IsString,
  IsNumber,
  IsBoolean,
  IsOptional,
  ValidateNested,
  Min,
} from 'class-validator';
import { Type } from 'class-transformer';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class ModbusParamsDto {
  @ApiProperty({ description: 'Modbus server address' })
  @IsString()
  server: string;

  @ApiProperty({ description: 'Unit ID', minimum: 0 })
  @IsNumber()
  @Min(0)
  unitId: number;

  @ApiProperty({ description: 'Register address', minimum: 0 })
  @IsNumber()
  @Min(0)
  address: number;

  @ApiPropertyOptional({ description: 'Coil value' })
  @IsBoolean()
  @IsOptional()
  value?: boolean;
}

export class RestParamsDto {
  @ApiProperty({ description: 'HTTP method' })
  @IsString()
  method: string;

  @ApiProperty({ description: 'Request path' })
  @IsString()
  path: string;

  @ApiPropertyOptional({ description: 'Request body' })
  @IsString()
  @IsOptional()
  body?: string;
}

export class SendCommandDto {
  @ApiProperty({ description: 'Target device ID' })
  @IsString()
  deviceId: string;

  @ApiProperty({ description: 'Command name' })
  @IsString()
  command: string;

  @ApiProperty({ description: 'Timeout in seconds', minimum: 1 })
  @IsNumber()
  @Min(1)
  timeoutSec: number;

  @ApiPropertyOptional({ type: ModbusParamsDto, description: 'Modbus parameters' })
  @IsOptional()
  @ValidateNested()
  @Type(() => ModbusParamsDto)
  modbus?: ModbusParamsDto;

  @ApiPropertyOptional({ type: RestParamsDto, description: 'REST parameters' })
  @IsOptional()
  @ValidateNested()
  @Type(() => RestParamsDto)
  rest?: RestParamsDto;
}
