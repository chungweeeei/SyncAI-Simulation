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
import { TaskActionType, StepType } from '../enums/task.enum';

export class MoveParamsDto {
  @IsNumber()
  x: number;

  @IsNumber()
  y: number;

  @IsNumber()
  r: number;
}

export class WaitParamsDto {
  @IsNumber()
  durationSec: number;
}

export class DoorParamsDto {
  @IsBoolean()
  open: boolean;
}

export class ChargeParamsDto {
  @IsNumber()
  x: number;

  @IsNumber()
  y: number;

  @IsNumber()
  @IsOptional()
  r?: number;
}

export class NavigateWithAlertParamsDto {
  @IsNumber()
  x: number;

  @IsNumber()
  y: number;

  @IsNumber()
  @IsOptional()
  r?: number;
}

export class StepDto {
  @IsString()
  id: string;

  @IsString()
  name: string;

  @IsEnum(StepType)
  type: StepType;

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
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => StepDto)
  steps: StepDto[];
}

export class CreateTaskDto {
  @IsEnum(TaskActionType)
  action: TaskActionType;

  @IsString()
  id: string;

  @IsNumber()
  timestamp: number;

  @ValidateNested()
  @Type(() => TaskPayloadDto)
  payload: TaskPayloadDto;
}
