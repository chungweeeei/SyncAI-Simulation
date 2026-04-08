import { Body, Controller, Post } from '@nestjs/common';
import { CommandService } from './command.service';
import { SendCommandDto } from './dto/send-command.dto';

@Controller('commands')
export class CommandController {
  constructor(private readonly commandService: CommandService) {}

  @Post()
  async sendCommand(@Body() dto: SendCommandDto) {
    return this.commandService.sendCommand(dto);
  }
}
