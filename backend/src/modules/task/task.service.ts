import { Injectable, NotFoundException } from '@nestjs/common';
import { CommandGrpcClient } from '../command/command-grpc.client';
import { Task } from './interfaces/task.interface';
import { CreateTaskDto } from './dto/create-task.dto';
import { TaskResponse } from './dto/task-response.dto';

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
        path: '/api/v1/tasks',
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
        path: `/api/v1/tasks/${id}`,
        body: '',
      },
    });

    if (!response.success) {
      throw new NotFoundException(`Task ${id} not found`);
    }

    return JSON.parse(response.data) as Task;
  }

  async createTask(dto: CreateTaskDto): Promise<TaskResponse> {
    const response = await this.commandGrpcClient.sendCommand({
      deviceId: '',
      command: 'create_task',
      timeoutSec: 10,
      rest: {
        method: 'POST',
        path: '/api/v1/tasks/',
        body: JSON.stringify(dto),
      },
    });

    if (!response.success) {
      throw new Error(`CreateTask failed: ${response.message}`);
    }

    return JSON.parse(response.data) as TaskResponse;
  }

  async deleteTask(id: string): Promise<TaskResponse> {
    const response = await this.commandGrpcClient.sendCommand({
      deviceId: '',
      command: 'delete_task',
      timeoutSec: 10,
      rest: {
        method: 'DELETE',
        path: `/api/v1/tasks/${id}`,
        body: '',
      },
    });

    if (!response.success) {
      throw new NotFoundException(`Task ${id} not found`);
    }

    return JSON.parse(response.data) as TaskResponse;
  }
}
