import React, { useCallback } from 'react';
import { UploadCloud, FileText } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  isParsing: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect, isParsing }) => {
  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
          onFileSelect(file);
        } else {
          alert('Please upload a valid CSV file.');
        }
      }
    },
    [onFileSelect]
  );

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelect(e.target.files[0]);
    }
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      className="border-2 border-dashed border-slate-300 rounded-xl p-10 text-center hover:bg-slate-50 hover:border-blue-500 transition-colors cursor-pointer group flex flex-col items-center justify-center h-full min-h-[300px]"
    >
      <input
        type="file"
        accept=".csv"
        className="hidden"
        id="file-upload"
        onChange={handleInputChange}
        disabled={isParsing}
      />
      <label htmlFor="file-upload" className="cursor-pointer w-full h-full flex flex-col items-center justify-center">
        <div className="bg-blue-50 p-4 rounded-full mb-4 group-hover:bg-blue-100 transition-colors">
          <UploadCloud className="w-10 h-10 text-blue-600" />
        </div>
        <h3 className="text-xl font-semibold text-slate-800 mb-2">
          {isParsing ? 'Processing CSV...' : 'Upload your CSV Data'}
        </h3>
        <p className="text-slate-500 max-w-sm mx-auto mb-6">
          Drag and drop your CSV file here, or click to browse. 
          We'll analyze it locally in your browser.
        </p>
        {!isParsing && (
            <span className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors">
                <FileText className="w-4 h-4 mr-2" />
                Select CSV File
            </span>
        )}
      </label>
    </div>
  );
};