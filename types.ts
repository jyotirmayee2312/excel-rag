export interface Message {
  role: 'user' | 'model';
  text: string;
  isError?: boolean;
}

export interface CsvData {
  headers: string[];
  rows: string[][];
  rawText: string;
}

export enum LoadingState {
  IDLE = 'IDLE',
  PARSING = 'PARSING',
  ANALYZING = 'ANALYZING',
}