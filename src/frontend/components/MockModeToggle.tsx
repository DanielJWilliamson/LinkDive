"use client";
import React from 'react';
import { useRuntimeConfig, useSetMockMode } from '../hooks/useRuntimeConfig';

export const MockModeToggle: React.FC = () => {
  const { data, isLoading } = useRuntimeConfig();
  const setMock = useSetMockMode();

  const mock = data?.mock_mode ?? true;
  const providerErrors = data?.provider_errors || {};

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-medium text-gray-900">Data Source Mode</div>
          <div className="text-xs text-gray-500">Switch between Mock and Live provider calls</div>
        </div>
        <button
          disabled={isLoading || setMock.isPending}
          onClick={() => setMock.mutate(!mock)}
          className={`px-3 py-1.5 text-sm rounded-md border ${mock ? 'bg-gray-100 text-gray-800 border-gray-300' : 'bg-green-50 text-green-700 border-green-300'}`}
          aria-pressed={!mock}
        >
          {mock ? 'Mock' : 'Live'}
        </button>
      </div>

      {Object.keys(providerErrors).length > 0 && (
        <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-3">
          <div className="font-medium mb-1">Live mode errors</div>
          <ul className="list-disc pl-5 space-y-1">
            {Object.entries(providerErrors).map(([k, v]) => (
              <li key={k}><span className="uppercase text-amber-800">{k}:</span> {v}</li>
            ))}
          </ul>
          <div className="mt-2 text-amber-800">Until access is enabled, results will fall back to deterministic mocks.</div>
        </div>
      )}
    </div>
  );
};
