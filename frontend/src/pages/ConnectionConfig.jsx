import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Link,
  Save,
  TestTube,
  Loader2,
  CheckCircle2,
  XCircle,
  Eye,
  EyeOff,
  KeyRound,
  Shield,
} from 'lucide-react';
import { apiGet, apiPut, apiPost } from '../api';

const inputClass =
  'w-full px-3 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-600 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition-colors';

const YOLO_OPTIONS = [
  { value: 'off', label: 'Standard (Module)', desc: 'Requires mcp_server module, API key auth, model whitelist' },
  { value: 'read', label: 'YOLO Read-Only', desc: 'All models readable, no module needed, no writes allowed' },
  { value: 'true', label: 'YOLO Full Access', desc: 'All models, full CRUD — extremely dangerous' },
];

export default function ConnectionConfig() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({});
  const [showKey, setShowKey] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: () => apiGet('/config'),
  });

  useEffect(() => {
    if (!config) return;
    setForm({
      odoo_url: config.odoo_url || '',
      odoo_db: config.odoo_db || '',
      odoo_user: config.odoo_user || '',
      odoo_api_key: '',
      odoo_yolo: config.odoo_yolo || 'off',
    });
  }, [config]);

  const saveMutation = useMutation({
    mutationFn: (data) => apiPut('/config/connection', { ...data, restart: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
      queryClient.invalidateQueries({ queryKey: ['health'] });
    },
  });

  const testMutation = useMutation({
    mutationFn: (data) => apiPost('/config/test', data),
    onSuccess: (result) => {
      setTestResult({ success: result.success, message: result.message });
    },
    onError: (err) => {
      setTestResult({ success: false, message: err.message });
    },
  });

  function handleChange(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setTestResult(null);
  }

  const isYolo = form.odoo_yolo && form.odoo_yolo !== 'off';

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-gray-500" size={24} />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-100">Connection Configuration</h2>
        <p className="text-sm text-gray-500 mt-1">
          Configure the connection to the Odoo instance for ivnvxd MCP Server
        </p>
      </div>

      <form className="bg-gray-900 border border-gray-800 rounded-xl p-6 max-w-xl">
        <div className="space-y-4">
          {/* Odoo URL */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1.5">Odoo URL</label>
            <div className="relative">
              <Link size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                type="url"
                value={form.odoo_url || ''}
                onChange={(e) => handleChange('odoo_url', e.target.value)}
                placeholder="http://lyucijyun-odoo-svc:8069"
                className={inputClass + ' pl-10'}
              />
            </div>
          </div>

          {/* Database */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1.5">Database</label>
            <input
              type="text"
              value={form.odoo_db || ''}
              onChange={(e) => handleChange('odoo_db', e.target.value)}
              placeholder="odoo"
              className={inputClass}
            />
          </div>

          {/* Username */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1.5">
              Username
              <span className="text-gray-600 font-normal ml-1">(ODOO_USER)</span>
            </label>
            <input
              type="text"
              value={form.odoo_user || ''}
              onChange={(e) => handleChange('odoo_user', e.target.value)}
              placeholder="admin"
              className={inputClass}
            />
          </div>

          {/* Mode Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1.5">
              <Shield size={14} className="inline mr-1" />
              Operation Mode
              <span className="text-gray-600 font-normal ml-1">(ODOO_YOLO)</span>
            </label>
            <div className="space-y-2">
              {YOLO_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                    form.odoo_yolo === opt.value
                      ? opt.value === 'true'
                        ? 'border-red-500/40 bg-red-500/5'
                        : opt.value === 'read'
                        ? 'border-amber-500/40 bg-amber-500/5'
                        : 'border-brand-500/40 bg-brand-500/5'
                      : 'border-gray-800 hover:border-gray-700'
                  }`}
                >
                  <input
                    type="radio"
                    name="odoo_yolo"
                    value={opt.value}
                    checked={form.odoo_yolo === opt.value}
                    onChange={(e) => handleChange('odoo_yolo', e.target.value)}
                    className="mt-0.5"
                  />
                  <div>
                    <span className={`text-sm font-medium ${
                      opt.value === 'true' ? 'text-red-400' :
                      opt.value === 'read' ? 'text-amber-400' :
                      'text-gray-200'
                    }`}>{opt.label}</span>
                    <p className="text-xs text-gray-500 mt-0.5">{opt.desc}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* API Key (Standard mode) */}
          {!isYolo && (
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1.5">
                <KeyRound size={14} className="inline mr-1" />
                API Key
                <span className="text-gray-600 font-normal ml-1">(ODOO_API_KEY)</span>
              </label>
              <div className="relative">
                <input
                  type={showKey ? 'text' : 'password'}
                  value={form.odoo_api_key || ''}
                  onChange={(e) => handleChange('odoo_api_key', e.target.value)}
                  placeholder={config?.odoo_api_key_masked || 'Paste Odoo API key'}
                  className={inputClass + ' pr-10'}
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <p className="text-xs text-gray-600 mt-1">
                Generate in Odoo: Settings → Users → API Keys tab
              </p>
            </div>
          )}

          {/* Password (YOLO mode only) */}
          {isYolo && (
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1.5">
                Password
                <span className="text-gray-600 font-normal ml-1">(ODOO_PASSWORD, required for YOLO)</span>
              </label>
              <div className="relative">
                <input
                  type={showKey ? 'text' : 'password'}
                  value={form.odoo_password || ''}
                  onChange={(e) => handleChange('odoo_password', e.target.value)}
                  placeholder="Enter Odoo password"
                  className={inputClass + ' pr-10'}
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Test result */}
        {testResult && (
          <div
            className={`mt-4 flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm ${
              testResult.success
                ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                : 'bg-red-500/10 border border-red-500/20 text-red-400'
            }`}
          >
            {testResult.success ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
            <span>{testResult.message}</span>
          </div>
        )}

        {saveMutation.isSuccess && (
          <div className="mt-4 flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <CheckCircle2 size={16} />
            <span>Configuration saved. MCP server restarting.</span>
          </div>
        )}

        {saveMutation.isError && (
          <div className="mt-4 flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm bg-red-500/10 border border-red-500/20 text-red-400">
            <XCircle size={16} />
            <span>{saveMutation.error.message}</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 mt-6">
          <button
            type="button"
            onClick={() => testMutation.mutate(form)}
            disabled={testMutation.isPending || !form.odoo_url}
            className="flex items-center gap-2 px-4 py-2.5 bg-gray-800 hover:bg-gray-700 disabled:bg-gray-800 disabled:text-gray-600 text-gray-300 font-medium rounded-lg transition-colors"
          >
            {testMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : <TestTube size={16} />}
            <span>Test Connection</span>
          </button>

          <button
            type="button"
            onClick={() => saveMutation.mutate(form)}
            disabled={saveMutation.isPending || !form.odoo_url}
            className="flex items-center gap-2 px-4 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium rounded-lg transition-colors"
          >
            {saveMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            <span>Save & Restart</span>
          </button>
        </div>
      </form>
    </div>
  );
}
