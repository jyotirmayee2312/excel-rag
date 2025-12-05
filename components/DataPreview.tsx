import React from 'react';
import { CsvData } from '../types';

interface DataPreviewProps {
  data: CsvData | null;
}

export const DataPreview: React.FC<DataPreviewProps> = ({ data }) => {
  if (!data) return null;

  return (
    <div className="overflow-auto border border-slate-200 rounded-lg bg-white shadow-sm h-full">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50 sticky top-0 z-10">
          <tr>
            {data.headers.map((header, idx) => (
              <th
                key={idx}
                className="px-4 py-3 text-left font-semibold text-slate-600 tracking-wider whitespace-nowrap"
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-slate-200">
          {data.rows.slice(0, 50).map((row, rowIdx) => (
            <tr key={rowIdx} className="hover:bg-slate-50">
              {row.map((cell, cellIdx) => (
                <td key={cellIdx} className="px-4 py-2 whitespace-nowrap text-slate-700">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.rows.length > 50 && (
        <div className="p-3 text-center text-xs text-slate-500 bg-slate-50 border-t border-slate-200">
          Showing first 50 of {data.rows.length} rows
        </div>
      )}
    </div>
  );
};