import { TaskStatus } from '../enums/task.enum';

export interface TaskResponse {
  id: string;
  status: TaskStatus;
  message: string;
}
