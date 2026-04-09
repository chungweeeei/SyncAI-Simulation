import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class CommandResponseDto {
  @ApiProperty({ description: 'Whether the command executed successfully' })
  success: boolean;

  @ApiProperty({ description: 'Response message' })
  message: string;

  @ApiPropertyOptional({
    description: 'Response data (parsed from JSON if applicable)',
  })
  data: Record<string, any> | null;
}
