import React, { useState } from 'react';
import { DatabaseConfig } from '../types';
import { Database, Server, User, Lock, ArrowRight, Loader2 } from 'lucide-react';

interface ConnectFormProps {
  onConnect: (config: DatabaseConfig) => void;
  isLoading: boolean;
}

const ConnectForm: React.FC<ConnectFormProps> = ({ onConnect, isLoading }) => {
  const [formData, setFormData] = useState<DatabaseConfig>({
    host: 'database-1.ckj0mw06ow00.us-east-1.rds.amazonaws.com',
    port: '3306',
    user: 'admin',
    password: '',
    database: 'Test',
    type: 'mysql'
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onConnect(formData);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 p-4 font-sans">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-blue-600/10 rounded-full flex items-center justify-center mb-4 text-blue-500 border border-blue-500/20">
            <Database className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Connect Database</h1>
          <p className="text-slate-400 text-sm mt-2 text-center">
            Enter your database endpoint and credentials.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
             <div className="col-span-2 space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">Type</label>
              <div className="relative">
                <select 
                  name="type"
                  value={formData.type}
                  onChange={handleChange}
                  className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent p-2.5 outline-none appearance-none"
                >
                  <option value="mysql">MySQL</option>
                  <option value="postgres">PostgreSQL</option>
                  <option value="sqlite">SQLite</option>
                </select>
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">Port</label>
              <input
                type="text"
                name="port"
                placeholder="3306"
                value={formData.port}
                onChange={handleChange}
                className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent p-2.5 outline-none placeholder-slate-600"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-500 uppercase">Endpoint / Host</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                <Server className="w-4 h-4" />
              </div>
              <input
                type="text"
                name="host"
                placeholder="db.example.com"
                value={formData.host}
                onChange={handleChange}
                className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pl-10 p-2.5 outline-none placeholder-slate-600"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">Username</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  name="user"
                  placeholder="admin"
                  value={formData.user}
                  onChange={handleChange}
                  className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pl-10 p-2.5 outline-none placeholder-slate-600"
                />
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-500 uppercase">Password</label>
              <div className="relative">
                 <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  name="password"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent pl-10 p-2.5 outline-none placeholder-slate-600"
                />
              </div>
            </div>
          </div>

          <div className="space-y-1">
             <label className="text-xs font-semibold text-slate-500 uppercase">Database Name</label>
             <input
                type="text"
                name="database"
                placeholder="analytics_db"
                value={formData.database}
                onChange={handleChange}
                className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent p-2.5 outline-none placeholder-slate-600"
              />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full mt-6 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-lg text-sm px-5 py-3 text-center flex items-center justify-center transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-900/20"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Verifying Connection...
              </>
            ) : (
              <>
                Connect
                <ArrowRight className="w-4 h-4 ml-2" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ConnectForm;