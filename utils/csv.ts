import { CsvData } from '../types';

export const parseCsv = (text: string): CsvData => {
  const lines = text.split(/\r\n|\n/).filter(line => line.trim() !== '');
  if (lines.length === 0) {
    return { headers: [], rows: [], rawText: text };
  }

  // Simple comma splitter that handles basic quotes, but for robustness in a demo
  // without external heavy libs, we'll use a regex for splitting CSV lines.
  const parseLine = (line: string): string[] => {
    const result: string[] = [];
    let start = 0;
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      if (line[i] === '"') {
        inQuotes = !inQuotes;
      } else if (line[i] === ',' && !inQuotes) {
        result.push(line.substring(start, i).replace(/^"|"$/g, '').trim());
        start = i + 1;
      }
    }
    result.push(line.substring(start).replace(/^"|"$/g, '').trim());
    return result;
  };

  const headers = parseLine(lines[0]);
  const rows = lines.slice(1).map(parseLine);

  return {
    headers,
    rows,
    rawText: text,
  };
};