export interface TaskStepParams {
  x?: number;
  y?: number;
  r?: number;
  cell_id?: string;
  durationSec?: number;
  open?: boolean;
  conveyor_id?: string;
  zone_id?: string;
}

export interface TaskStep {
  id: string;
  name: string;
  type: string;
  params: TaskStepParams;
  status?: string;
  error_msg?: string;
}

export interface TaskPayload {
  steps: TaskStep[];
}

export interface Task {
  action: string;
  id: string;
  timestamp: number;
  payload: TaskPayload;
  status: string;
  current_step_index: number;
  error_msg: string;
  workflow_id: string;
  completed_at: number;
}
