import {
  IsString,
  IsNumber,
  IsBoolean,
  IsOptional,
  ValidateNested,
  Min,
} from 'class-validator';
import { Type } from 'class-transformer';

export class ModbusParamsDto {
  @IsString()
  server: string;

  @IsNumber()
  @Min(0)
  unitId: number;

  @IsNumber()
  @Min(0)
  address: number;

  @IsBoolean()
  @IsOptional()
  value?: boolean;
}

export class RestParamsDto {
  @IsString()
  method: string;

  @IsString()
  path: string;

  @IsString()
  @IsOptional()
  body?: string;
}

export class SendCommandDto {
  @IsString()
  deviceId: string;

  @IsString()
  command: string;

  @IsNumber()
  @Min(1)
  timeoutSec: number;

  @IsOptional()
  @ValidateNested()
  @Type(() => ModbusParamsDto)
  modbus?: ModbusParamsDto;

  @IsOptional()
  @ValidateNested()
  @Type(() => RestParamsDto)
  rest?: RestParamsDto;
}
