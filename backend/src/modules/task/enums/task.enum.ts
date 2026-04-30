export enum TaskActionType {
  COMMAND = 'COMMAND',
  TASK = 'TASK',
}

export enum StepType {
  MOVE = 'MOVE',
  WAIT = 'WAIT',
  DOOR = 'DOOR',
  CHARGE = 'CHARGE',
  PICKUP = 'PICKUP',
  DROPOFF = 'DROPOFF',
}

export enum TaskStatus {
  PENDING = 'PENDING',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
}

export enum StepStatus {
  PENDING = 'PENDING',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
}
