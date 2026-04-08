import { Injectable, NotFoundException } from '@nestjs/common';
import { CommandGrpcClient } from '../command/command-grpc.client';
import { Task } from './interfaces/task.interface';

@Injectable()
export class TaskService {
  constructor(private readonly commandGrpcClient: CommandGrpcClient) {}

  async listTasks(): Promise<Task[]> {
    const response = await this.commandGrpcClient.sendCommand({
      deviceId: '',
      command: 'list_tasks',
      timeoutSec: 10,
      rest: {
        method: 'GET',
        path: '/api/tasks',
        body: '',
      },
    });

    if (!response.success) {
      throw new Error(`ListTasks failed: ${response.message}`);
    }

    return JSON.parse(response.data) as Task[];
  }

  async getTask(id: string): Promise<Task> {
    const response = await this.commandGrpcClient.sendCommand({
      deviceId: '',
      command: 'get_task',
      timeoutSec: 10,
      rest: {
        method: 'GET',
        path: `/api/tasks/${id}`,
        body: '',
      },
    });

    if (!response.success) {
      throw new NotFoundException(`Task ${id} not found`);
    }

    return JSON.parse(response.data) as Task;
  }
}
