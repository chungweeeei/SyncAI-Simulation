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
  @ApiProperty({ description: 'X coordinate', example: -3.5 })
  @IsNumber()
  x: number;

  @ApiProperty({ description: 'Y coordinate', example: 4.5 })
  @IsNumber()
  y: number;

  @ApiProperty({ description: 'Rotation angle', example: 90.0 })
  @IsNumber()
  r: number;

  @ApiPropertyOptional({
    description:
      'WMS Cell uuid; if provided, robot reports occupancy on arrival',
    example: '4386af1d-ffb9-42bc-89f5-9ccd41f887ed',
  })
  @IsString()
  @IsOptional()
  cell_id?: string;
}

export class WaitParamsDto {
  @ApiProperty({ description: 'Wait duration in seconds', example: 5.0 })
  @IsNumber()
  durationSec: number;
}

export class DoorParamsDto {
  @ApiProperty({ description: 'Whether to open the door', example: true })
  @IsBoolean()
  open: boolean;
}

export class ChargeParamsDto {
  @ApiProperty({ description: 'X coordinate', example: -2.0 })
  @IsNumber()
  x: number;

  @ApiProperty({ description: 'Y coordinate', example: 5.0 })
  @IsNumber()
  y: number;

  @ApiPropertyOptional({ description: 'Rotation angle', example: 0.0 })
  @IsNumber()
  @IsOptional()
  r?: number;
}

export class PickupParamsDto {
  @ApiProperty({ description: 'Conveyor device id', example: 'conveyor_01' })
  @IsString()
  conveyor_id: string;
}

export class DropoffParamsDto {
  @ApiProperty({ description: 'Dropoff zone id', example: 'dropoff_a' })
  @IsString()
  zone_id: string;
}

export class StepDto {
  @ApiProperty({ description: 'Step identifier', example: 'step1' })
  @IsString()
  id: string;

  @ApiProperty({ description: 'Step name', example: 'Move to conveyor_01' })
  @IsString()
  name: string;

  @ApiProperty({
    enum: StepType,
    description: 'Step type',
    example: StepType.MOVE,
  })
  @IsEnum(StepType)
  type: StepType;

  @ApiProperty({
    description: 'Step parameters (varies by type)',
    oneOf: [
      { type: 'object', title: 'MoveParamsDto' },
      { type: 'object', title: 'WaitParamsDto' },
      { type: 'object', title: 'DoorParamsDto' },
      { type: 'object', title: 'ChargeParamsDto' },
      { type: 'object', title: 'PickupParamsDto' },
      { type: 'object', title: 'DropoffParamsDto' },
    ],
  })
  @ValidateNested()
  @Transform(({ value, obj }) => {
    const typeMap: Record<string, new () => object> = {
      [StepType.MOVE]: MoveParamsDto,
      [StepType.WAIT]: WaitParamsDto,
      [StepType.DOOR]: DoorParamsDto,
      [StepType.CHARGE]: ChargeParamsDto,
      [StepType.PICKUP]: PickupParamsDto,
      [StepType.DROPOFF]: DropoffParamsDto,
    };
    const cls = typeMap[obj.type];
    return cls ? plainToInstance(cls, value) : value;
  })
  params:
    | MoveParamsDto
    | WaitParamsDto
    | DoorParamsDto
    | ChargeParamsDto
    | PickupParamsDto
    | DropoffParamsDto;
}

export class TaskPayloadDto {
  @ApiProperty({ type: [StepDto], description: 'List of task steps' })
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => StepDto)
  steps: StepDto[];
}

export class CreateTaskDto {
  @ApiProperty({
    enum: TaskActionType,
    description: 'Action type',
    example: TaskActionType.TASK,
  })
  @IsEnum(TaskActionType)
  action: TaskActionType;

  @ApiProperty({
    description: 'Task identifier',
    example: 'robot01-pickup-dropoff-001',
  })
  @IsString()
  id: string;

  @ApiProperty({ description: 'Unix timestamp', example: 1746662400 })
  @IsNumber()
  timestamp: number;

  @ApiProperty({
    type: TaskPayloadDto,
    description: 'Task payload',
    example: {
      steps: [
        {
          id: 'step1',
          name: 'Move to conveyor_01',
          type: StepType.MOVE,
          params: {
            x: -3.5,
            y: 4.5,
            r: 90.0,
            cell_id: '4386af1d-ffb9-42bc-89f5-9ccd41f887ed',
          },
        },
        {
          id: 'step2',
          name: 'Pickup box from conveyor_01',
          type: StepType.PICKUP,
          params: { conveyor_id: 'conveyor_01' },
        },
        {
          id: 'step3',
          name: 'Dropoff at dropoff_a',
          type: StepType.DROPOFF,
          params: { zone_id: 'dropoff_a' },
        },
      ],
    },
  })
  @ValidateNested()
  @Type(() => TaskPayloadDto)
  payload: TaskPayloadDto;
}
