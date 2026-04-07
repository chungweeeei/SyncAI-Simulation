import { Injectable, NotFoundException } from '@nestjs/common';
import { Task } from './interfaces/task.interface';

@Injectable()
export class TaskService {
  private readonly tasks = new Map<string, Task>();

  listTasks(): Task[] {
    return Array.from(this.tasks.values());
  }

  getTask(id: string): Task {
    const task = this.tasks.get(id);
    if (!task) {
      throw new NotFoundException(`Task ${id} not found`);
    }
    return task;
  }
}
