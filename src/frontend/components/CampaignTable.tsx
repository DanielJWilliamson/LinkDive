'use client';

import { useMemo, useState } from 'react';

interface Campaign {
  id: number;
  client_name: string;
  campaign_name: string;
  client_domain: string;
  campaign_url?: string;
  launch_date?: string;
  monitoring_status: string;
  created_at: string;
  updated_at: string;
}

type SortField = 'client_name' | 'campaign_name' | 'launch_date' | 'monitoring_status';
type SortDir = 'asc' | 'desc';

interface CampaignTableProps {
  campaigns: Campaign[];
  isLoading?: boolean;
  onRowClick?: (campaign: Campaign) => void;
}

export function CampaignTable({ campaigns, isLoading = false, onRowClick }: CampaignTableProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'live' | 'paused'>('all');
  const [sortField, setSortField] = useState<SortField>('launch_date');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  const toggleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDir(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir(field === 'launch_date' ? 'desc' : 'asc');
    }
  };

  const normalize = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '');

  const filtered = useMemo(() => {
    const term = normalize(searchTerm);
    return campaigns.filter(c => {
      const matchesSearch = term === ''
        ? true
        : normalize(c.client_name).includes(term) || normalize(c.campaign_name).includes(term);
      const matchesStatus =
        statusFilter === 'all' || c.monitoring_status.toLowerCase() === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [campaigns, searchTerm, statusFilter]);

  const sorted = useMemo(() => {
    const arr = [...filtered];
    arr.sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1;
      switch (sortField) {
        case 'client_name':
          return a.client_name.localeCompare(b.client_name) * dir;
        case 'campaign_name':
          return a.campaign_name.localeCompare(b.campaign_name) * dir;
        case 'monitoring_status':
          return a.monitoring_status.localeCompare(b.monitoring_status) * dir;
        case 'launch_date':
        default: {
          const ad = a.launch_date ? new Date(a.launch_date).getTime() : 0;
          const bd = b.launch_date ? new Date(b.launch_date).getTime() : 0;
          return (ad - bd) * dir;
        }
      }
    });
    return arr;
  }, [filtered, sortField, sortDir]);

  const formatDate = (s?: string) => (s ? new Date(s).toLocaleDateString() : '—');
  const headerClass = (field: SortField) =>
    `px-6 py-3 text-left text-xs font-medium uppercase tracking-wider cursor-pointer select-none ${
      sortField === field ? 'text-blue-700' : 'text-gray-500'
    }`;

  return (
    <div className="bg-white rounded-lg border border-gray-200" data-testid="campaigns-table" aria-label="Campaigns table" aria-busy={isLoading || undefined}>
      {/* Controls */}
      <div className="p-4 border-b border-gray-200 flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
        <div className="text-lg font-medium text-gray-900" id="campaigns-table-heading">Campaigns</div>
        <div className="flex items-center gap-2">
          <input
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            placeholder="Search campaign or client…"
            className="px-3 py-2 text-sm border border-gray-300 rounded-md w-64"
            aria-label="Search campaigns"
            role="searchbox"
          />
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value as 'all'|'live'|'paused')}
            className="px-3 py-2 text-sm border border-gray-300 rounded-md bg-white"
            aria-label="Filter by status"
            aria-controls="campaigns-table"
          >
            <option value="all">All</option>
            <option value="live">Live</option>
            <option value="paused">Paused</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200" role="table" aria-labelledby="campaigns-table-heading" id="campaigns-table">
          <caption className="sr-only">List of campaigns with columns for Client Name, Campaign Name, Start Date, and Monitoring Status.</caption>
          <thead className="bg-gray-50" role="rowgroup">
            <tr role="row">
              <th
                role="columnheader"
                aria-sort={sortField === 'client_name' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
                tabIndex={0}
                scope="col"
                className={headerClass('client_name')}
                data-testid="header-client-name"
                onClick={() => toggleSort('client_name')}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleSort('client_name'); }
                }}
              >
                Client Name {sortField === 'client_name' && (<span aria-hidden="true">{sortDir === 'asc' ? '▲' : '▼'}</span>)}
              </th>
              <th
                role="columnheader"
                aria-sort={sortField === 'campaign_name' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
                tabIndex={0}
                scope="col"
                className={headerClass('campaign_name')}
                data-testid="header-campaign-name"
                onClick={() => toggleSort('campaign_name')}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleSort('campaign_name'); }
                }}
              >
                Campaign Name {sortField === 'campaign_name' && (<span aria-hidden="true">{sortDir === 'asc' ? '▲' : '▼'}</span>)}
              </th>
              <th
                role="columnheader"
                aria-sort={sortField === 'launch_date' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
                tabIndex={0}
                scope="col"
                className={headerClass('launch_date')}
                data-testid="header-start-date"
                onClick={() => toggleSort('launch_date')}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleSort('launch_date'); }
                }}
              >
                Start Date {sortField === 'launch_date' && (<span aria-hidden="true">{sortDir === 'asc' ? '▲' : '▼'}</span>)}
              </th>
              <th
                role="columnheader"
                aria-sort={sortField === 'monitoring_status' ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
                tabIndex={0}
                scope="col"
                className={headerClass('monitoring_status')}
                data-testid="header-monitoring-status"
                onClick={() => toggleSort('monitoring_status')}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleSort('monitoring_status'); }
                }}
              >
                Monitoring Status {sortField === 'monitoring_status' && (<span aria-hidden="true">{sortDir === 'asc' ? '▲' : '▼'}</span>)}
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {isLoading ? (
              [...Array(5)].map((_, i) => (
                <tr key={i}>
                  <td className="px-6 py-4"><div className="h-4 w-40 bg-gray-100 animate-pulse rounded" /></td>
                  <td className="px-6 py-4"><div className="h-4 w-56 bg-gray-100 animate-pulse rounded" /></td>
                  <td className="px-6 py-4"><div className="h-4 w-24 bg-gray-100 animate-pulse rounded" /></td>
                  <td className="px-6 py-4"><div className="h-6 w-20 bg-gray-100 animate-pulse rounded" /></td>
                </tr>
              ))
            ) : sorted.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-gray-500">No campaigns found.</td>
              </tr>
            ) : (
              sorted.map(c => (
                <tr
                  key={c.id}
                  className="hover:bg-gray-50 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
                  data-testid="campaigns-table-row"
                  onClick={() => onRowClick && onRowClick(c)}
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if ((e.key === 'Enter' || e.key === ' ') && onRowClick) {
                      e.preventDefault();
                      onRowClick(c);
                    }
                  }}
                  aria-label={`Open campaign ${c.campaign_name} for ${c.client_name}`}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{c.client_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{c.campaign_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatDate(c.launch_date)}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      c.monitoring_status === 'Live' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {c.monitoring_status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default CampaignTable;
