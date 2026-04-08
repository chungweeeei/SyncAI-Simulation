import { Controller, Get, Param } from '@nestjs/common';
import { TaskService } from './task.service';

@Controller('tasks')
export class TaskController {
  constructor(private readonly taskService: TaskService) {}

  @Get()
  async listTasks() {
    return this.taskService.listTasks();
  }

  @Get(':id')
  async getTask(@Param('id') id: string) {
    return this.taskService.getTask(id);
  }
}
