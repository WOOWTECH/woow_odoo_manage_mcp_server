import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Loader2, Wrench, ToggleLeft, ToggleRight, RefreshCw, ShieldAlert, BookOpen } from 'lucide-react';
import { apiGet, apiPut } from '../api';

export default function ToolManager() {
  const queryClient = useQueryClient();

  const { data: toolsData, isLoading, error, refetch } = useQuery({
    queryKey: ['tools'],
    queryFn: () => apiGet('/tools'),
  });

  const mutation = useMutation({
    mutationFn: (tools) => apiPut('/tools', { tools }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tools'] }),
  });

  const tools = toolsData?.tools || [];
  const enabledCount = tools.filter((t) => t.enabled).length;
  const allEnabled = enabledCount === tools.length;

  function handleToggleAll() {
    const newState = !allEnabled;
    const updates = {};
    for (const t of tools) {
      updates[t.name] = newState;
    }
    mutation.mutate(updates);
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="animate-spin text-gray-500" size={24} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6 text-center">
        <p className="text-red-400 font-medium">Failed to load tools</p>
        <p className="text-red-400/70 text-sm mt-1">{error.message}</p>
        <button
          onClick={() => refetch()}
          className="mt-4 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  const readTools = tools.filter((t) => t.category === 'Read & Discover');
  const writeTools = tools.filter((t) => t.category === 'Write & Operate');

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-100">Tool Manager</h2>
          <p className="text-sm text-gray-500 mt-1">
            {enabledCount} of {tools.length} tools enabled
          </p>
        </div>
        {mutation.isPending && (
          <div className="flex items-center gap-2 px-3 py-2 bg-brand-600/20 border border-brand-600/30 rounded-lg text-sm text-brand-400">
            <Loader2 size={14} className="animate-spin" />
            <span>Applying...</span>
          </div>
        )}
      </div>

      {/* Master Toggle */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Wrench size={20} className="text-brand-400" />
            <div>
              <p className="text-gray-200 font-medium">All MCP Tools</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {allEnabled ? 'All 9 tools are enabled' : `${enabledCount} of ${tools.length} enabled`}
              </p>
            </div>
          </div>
          <button
            onClick={handleToggleAll}
            disabled={mutation.isPending}
            className="shrink-0 disabled:opacity-50 transition-all hover:scale-105"
            title={allEnabled ? 'Disable all tools' : 'Enable all tools'}
          >
            {mutation.isPending ? (
              <Loader2 size={32} className="animate-spin text-gray-500" />
            ) : allEnabled ? (
              <ToggleRight size={36} className="text-brand-500" />
            ) : (
              <ToggleLeft size={36} className="text-gray-600" />
            )}
          </button>
        </div>
      </div>

      {/* Tool List (read-only display) */}
      <div className="space-y-4">
        {/* Read & Discover */}
        <div>
          <div className="flex items-center gap-2 mb-2 px-1">
            <BookOpen size={14} className="text-blue-400" />
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
              Read & Discover
            </h3>
            <span className="text-xs text-gray-600">({readTools.length})</span>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl divide-y divide-gray-800">
            {readTools.map((tool) => (
              <div key={tool.name} className="flex items-center gap-3 px-4 py-3">
                <div className={`w-2 h-2 rounded-full ${tool.enabled ? 'bg-brand-500' : 'bg-gray-700'}`} />
                <div className="flex-1 min-w-0">
                  <span className="text-sm font-medium text-gray-200 font-mono">{tool.name}</span>
                  {tool.description && (
                    <p className="text-xs text-gray-500 mt-0.5 truncate">{tool.description}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Write & Operate */}
        <div>
          <div className="flex items-center gap-2 mb-2 px-1">
            <ShieldAlert size={14} className="text-amber-400" />
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
              Write & Operate
            </h3>
            <span className="text-xs text-gray-600">({writeTools.length})</span>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl divide-y divide-gray-800">
            {writeTools.map((tool) => (
              <div key={tool.name} className="flex items-center gap-3 px-4 py-3">
                <div className={`w-2 h-2 rounded-full ${tool.enabled ? 'bg-amber-500' : 'bg-gray-700'}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-200 font-mono">{tool.name}</span>
                    <span className="text-[10px] px-1.5 py-0.5 bg-amber-500/10 text-amber-400 rounded border border-amber-500/20">
                      dangerous
                    </span>
                  </div>
                  {tool.description && (
                    <p className="text-xs text-gray-500 mt-0.5 truncate">{tool.description}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
