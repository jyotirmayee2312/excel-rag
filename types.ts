export interface DatabaseConfig {
  host: string;
  port: string;
  user: string;
  password?: string;
  database: string;
  type: 'mysql' | 'postgres' | 'sqlite';
}

export enum MessageRole {
  USER = 'user',
  ASSISTANT = 'assistant',
  SYSTEM = 'system'
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  sql?: string;
  isTyping?: boolean;
  timestamp: number;
}

export interface TableSchema {
  name: string;
  columns: string[];
}
