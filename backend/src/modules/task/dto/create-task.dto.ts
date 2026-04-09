import {
  IsString,
  IsNumber,
  IsBoolean,
  IsEnum,
  IsOptional,
  IsArray,
  ValidateNested,
} from 'class-validator';
import { Transform, Type, plainToInstance } from 'class-transformer';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { TaskActionType, StepType } from '../enums/task.enum';

export class MoveParamsDto {
  @ApiProperty({ description: 'X coordinate' })
  @IsNumber()
  x: number;

  @ApiProperty({ description: 'Y coordinate' })
  @IsNumber()
  y: number;

  @ApiProperty({ description: 'Rotation angle' })
  @IsNumber()
  r: number;
}

export class WaitParamsDto {
  @ApiProperty({ description: 'Wait duration in seconds' })
  @IsNumber()
  durationSec: number;
}

export class DoorParamsDto {
  @ApiProperty({ description: 'Whether to open the door' })
  @IsBoolean()
  open: boolean;
}

export class ChargeParamsDto {
  @ApiProperty({ description: 'X coordinate' })
  @IsNumber()
  x: number;

  @ApiProperty({ description: 'Y coordinate' })
  @IsNumber()
  y: number;

  @ApiPropertyOptional({ description: 'Rotation angle' })
  @IsNumber()
  @IsOptional()
  r?: number;
}

export class NavigateWithAlertParamsDto {
  @ApiProperty({ description: 'X coordinate' })
  @IsNumber()
  x: number;

  @ApiProperty({ description: 'Y coordinate' })
  @IsNumber()
  y: number;

  @ApiPropertyOptional({ description: 'Rotation angle' })
  @IsNumber()
  @IsOptional()
  r?: number;
}

export class StepDto {
  @ApiProperty({ description: 'Step identifier' })
  @IsString()
  id: string;

  @ApiProperty({ description: 'Step name' })
  @IsString()
  name: string;

  @ApiProperty({ enum: StepType, description: 'Step type' })
  @IsEnum(StepType)
  type: StepType;

  @ApiProperty({
    description: 'Step parameters (varies by type)',
    oneOf: [
      { type: 'object', title: 'MoveParamsDto' },
      { type: 'object', title: 'WaitParamsDto' },
      { type: 'object', title: 'DoorParamsDto' },
      { type: 'object', title: 'ChargeParamsDto' },
      { type: 'object', title: 'NavigateWithAlertParamsDto' },
    ],
  })
  @ValidateNested()
  @Transform(({ value, obj }) => {
    const typeMap: Record<string, new () => object> = {
      [StepType.MOVE]: MoveParamsDto,
      [StepType.WAIT]: WaitParamsDto,
      [StepType.DOOR]: DoorParamsDto,
      [StepType.CHARGE]: ChargeParamsDto,
      [StepType.NAVIGATE_WITH_ALERT]: NavigateWithAlertParamsDto,
    };
    const cls = typeMap[obj.type];
    return cls ? plainToInstance(cls, value) : value;
  })
  params:
    | MoveParamsDto
    | WaitParamsDto
    | DoorParamsDto
    | ChargeParamsDto
    | NavigateWithAlertParamsDto;
}

export class TaskPayloadDto {
  @ApiProperty({ type: [StepDto], description: 'List of task steps' })
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => StepDto)
  steps: StepDto[];
}

export class CreateTaskDto {
  @ApiProperty({ enum: TaskActionType, description: 'Action type' })
  @IsEnum(TaskActionType)
  action: TaskActionType;

  @ApiProperty({ description: 'Task identifier' })
  @IsString()
  id: string;

  @ApiProperty({ description: 'Unix timestamp' })
  @IsNumber()
  timestamp: number;

  @ApiProperty({ type: TaskPayloadDto, description: 'Task payload' })
  @ValidateNested()
  @Type(() => TaskPayloadDto)
  payload: TaskPayloadDto;
}
