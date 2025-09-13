'use client';

import { useEffect, useMemo, useState } from 'react';
import { CheckCircle, Search as SearchIcon } from 'lucide-react';
import type { BacklinkResult } from '../hooks/useCampaigns';
import { CampaignList } from '../components/CampaignList';
import CampaignTable from '../components/CampaignTable';
import { CoverageSummary } from '../components/CoverageSummary';
import Link from 'next/link';
import { CreateCampaignModal } from '../components/CreateCampaignModal';
import { apiClient, DEV_USER_EMAIL } from '../lib/api';
import { BacklinkCharts } from '../components/BacklinkCharts';
import BackgroundTaskMonitor from '../src/components/BackgroundTaskMonitor';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { UserProfile } from '../components/auth/UserProfile';
import { MockModeToggle } from '../components/MockModeToggle';
import { 
  useCampaigns, 
  useCreateCampaign, 
  useCampaignResults,
  useAnalyzeCampaign,
  useCoverageDetails,
  type CampaignFormData 
} from '../hooks/useCampaigns';
import { useStartCampaignAnalysis } from '../src/hooks/useBackgroundTasks';

// Local campaign interface (simplified for component use)
interface LocalCampaign {
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

type ViewMode = 'campaigns' | 'campaign-details';

export default function Dashboard() {
  const [viewMode, setViewMode] = useState<ViewMode>('campaigns');
  const [homeView, setHomeView] = useState<'cards' | 'table'>(() => {
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      const v = (url.searchParams.get('view') || localStorage.getItem('homeView') || 'cards') as 'cards' | 'table';
      return v === 'table' ? 'table' : 'cards';
    }
    return 'cards';
  });
  const [selectedCampaign, setSelectedCampaign] = useState<LocalCampaign | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'table' | 'charts' | 'tasks'>('table');
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [copyState, setCopyState] = useState<'idle' | 'copying' | 'copied' | 'error'>('idle');
  const [statusFilter, setStatusFilter] = useState<'all' | 'verified' | 'potential'>('all');
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [sortField, setSortField] = useState<'first_seen' | 'page_title' | 'url' | 'coverage_status' | 'link_destination'>('first_seen');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);
  const pageSize = 25;

  // API hooks
  const { data: campaigns = [], isLoading: campaignsLoading, error: campaignsError } = useCampaigns();
  const createCampaignMutation = useCreateCampaign();
  const analyzeCampaignMutation = useAnalyzeCampaign();
  const startCampaignAnalysisMutation = useStartCampaignAnalysis();
  const { 
    data: campaignResults, 
    isLoading: resultsLoading 
  } = useCampaignResults(selectedCampaign?.id || null);

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => clearTimeout(t);
  }, [search]);

  // Coverage details for table
  const { data: coverageRows = [], isLoading: coverageLoading } = useCoverageDetails(
    selectedCampaign?.id || null,
    { status: statusFilter, search: debouncedSearch }
  );

  // Sort + paginate coverage rows
  const sortedCoverage = useMemo<BacklinkResult[]>(() => {
    const arr: BacklinkResult[] = [...coverageRows];
    const asc = sortDir === 'asc';
    arr.sort((a, b) => {
      let cmp = 0;
      if (sortField === 'first_seen') {
        const ad = a.first_seen ? new Date(a.first_seen).getTime() : 0;
        const bd = b.first_seen ? new Date(b.first_seen).getTime() : 0;
        cmp = ad - bd;
      } else if (sortField === 'page_title') {
        cmp = (a.page_title || '').localeCompare(b.page_title || '', undefined, { sensitivity: 'base' });
      } else if (sortField === 'url') {
        cmp = (a.url || '').localeCompare(b.url || '', undefined, { sensitivity: 'base' });
      } else if (sortField === 'coverage_status') {
        cmp = (a.coverage_status || '').localeCompare(b.coverage_status || '', undefined, { sensitivity: 'base' });
      } else if (sortField === 'link_destination') {
        cmp = (a.link_destination || '').localeCompare(b.link_destination || '', undefined, { sensitivity: 'base' });
      }
      return asc ? cmp : -cmp;
    });
    return arr;
  }, [coverageRows, sortField, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sortedCoverage.length / pageSize));
  useEffect(() => { setPage(1); }, [statusFilter, debouncedSearch, sortField, sortDir, selectedCampaign?.id]);
  const pagedCoverage = useMemo(() => sortedCoverage.slice((page - 1) * pageSize, page * pageSize), [sortedCoverage, page]);

  // Clear selection when switching campaigns or refreshing results
  useEffect(() => {
    setSelectedIds([]);
    setCopyState('idle');
  }, [selectedCampaign?.id, campaignResults?.results?.length]);

  const allResultIds = useMemo(() => (sortedCoverage || []).map(r => r.id), [sortedCoverage]);
  const allSelected = useMemo(() => allResultIds.length > 0 && selectedIds.length === allResultIds.length, [allResultIds, selectedIds]);
  const someSelected = useMemo(() => selectedIds.length > 0 && selectedIds.length < (allResultIds.length || 0), [allResultIds.length, selectedIds.length]);

  const toggleSelectAll = () => {
    if (allSelected) setSelectedIds([]);
    else setSelectedIds(allResultIds);
  };

  const toggleRow = (id: number) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const copySelectedUrls = async () => {
    try {
      setCopyState('copying');
  const rows = sortedCoverage || [];
      let toCopy = rows.filter(r => selectedIds.includes(r.id));
      // Fallback: if nothing selected, copy verified coverage (common workflow)
      if (toCopy.length === 0) {
        toCopy = rows.filter(r => r.coverage_status === 'verified');
      }
      const uniqueUrls = Array.from(new Set(toCopy.map(r => r.url)));
      if (uniqueUrls.length === 0) {
        setCopyState('idle');
        return;
      }
      await navigator.clipboard.writeText(uniqueUrls.join('\n'));
      setCopyState('copied');
      setTimeout(() => setCopyState('idle'), 2000);
    } catch (e) {
      console.error('Copy failed', e);
      setCopyState('error');
      setTimeout(() => setCopyState('idle'), 2000);
    }
  };

  const handleCampaignSelect = (campaign: LocalCampaign) => {
    setSelectedCampaign(campaign);
    setViewMode('campaign-details');
    
    // Trigger analysis for the selected campaign
    analyzeCampaignMutation.mutate(campaign.id);
  };

  const handleCreateCampaign = async (data: CampaignFormData) => {
    try {
      await createCampaignMutation.mutateAsync(data);
      setShowCreateModal(false);
    } catch (error) {
      console.error('Failed to create campaign:', error);
      throw error;
    }
  };

  const handleEnhancedAnalysis = async () => {
    if (!selectedCampaign) return;
    
    try {
      await startCampaignAnalysisMutation.mutateAsync({
        campaignId: selectedCampaign.id,
        userEmail: DEV_USER_EMAIL, // Fallback dev identity until auth is wired
        analysisDepth: 'standard',
        includeContentVerification: true
      });
    } catch (error) {
      console.error('Failed to start enhanced analysis:', error);
    }
  };

  const handleBackToCampaigns = () => {
    setViewMode('campaigns');
    setSelectedCampaign(null);
  };

  // Error state
  if (campaignsError) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Connection Error</h1>
          <p className="text-gray-600 mb-4">
            Unable to connect to the Link Dive AI backend. Please ensure the server is running.
          </p>
          <p className="text-sm text-gray-500">
            Expected backend at: {apiClient.defaults.baseURL}
          </p>
        </div>
      </div>
    );
  }

  return (
    <ProtectedRoute>
      {viewMode === 'campaigns' ? (
        <div className="space-y-8">
          {/* Home view toggle */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-1 bg-white border border-gray-200 rounded-md p-1" role="tablist" aria-label="Home view">
                <button
                  role="tab"
                  aria-selected={homeView === 'cards'}
                  data-testid="view-toggle-cards"
                  onClick={() => {
                    setHomeView('cards');
                    if (typeof window !== 'undefined') {
                      const url = new URL(window.location.href);
                      url.searchParams.set('view', 'cards');
                      window.history.replaceState({}, '', url.toString());
                      localStorage.setItem('homeView', 'cards');
                    }
                  }}
                  className={`px-3 py-1.5 text-sm rounded ${homeView === 'cards' ? 'bg-blue-600 text-white' : 'text-gray-700 hover:bg-gray-50'}`}
                >
                  Cards
                </button>
                <button
                  role="tab"
                  aria-selected={homeView === 'table'}
                  data-testid="view-toggle-table"
                  onClick={() => {
                    setHomeView('table');
                    if (typeof window !== 'undefined') {
                      const url = new URL(window.location.href);
                      url.searchParams.set('view', 'table');
                      window.history.replaceState({}, '', url.toString());
                      localStorage.setItem('homeView', 'table');
                    }
                  }}
                  className={`px-3 py-1.5 text-sm rounded ${homeView === 'table' ? 'bg-blue-600 text-white' : 'text-gray-700 hover:bg-gray-50'}`}
                >
                  Table
                </button>
              </div>
            </div>
          </div>

          {homeView === 'cards' ? (
            <CampaignList
              campaigns={campaigns}
              onCampaignSelect={handleCampaignSelect}
              onNewCampaign={() => setShowCreateModal(true)}
              isLoading={campaignsLoading}
            />
          ) : (
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <CampaignTable
                campaigns={campaigns}
                isLoading={campaignsLoading}
                onRowClick={(c) => handleCampaignSelect({
                  id: c.id,
                  client_name: c.client_name,
                  campaign_name: c.campaign_name,
                  client_domain: c.client_domain,
                  campaign_url: c.campaign_url,
                  launch_date: c.launch_date,
                  monitoring_status: c.monitoring_status,
                  created_at: c.created_at,
                  updated_at: c.updated_at,
                })}
              />
            </div>
          )}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900">Coverage Overview</h2>
              <Link href="/coverage" className="text-sm text-blue-600 hover:underline">Open Full Coverage Dashboard →</Link>
            </div>
            <div className="mb-4">
              <MockModeToggle />
            </div>
            <CoverageSummary />
          </div>
        </div>
      ) : (
        <div className="min-h-screen bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header with User Profile */}
            <div className="mb-8 flex justify-between items-center">
              <div>
                <button
                  onClick={handleBackToCampaigns}
                  className="text-blue-600 hover:text-blue-800 mb-4 flex items-center"
                >
                  ← Back to Campaigns
                </button>
              </div>
              <UserProfile />
            </div>
              
            {/* Campaign Header */}
            {selectedCampaign && (
              <div className="mb-8 bg-white rounded-lg border border-gray-200 p-6" aria-labelledby="campaign-details-heading">
                <div className="flex justify-between items-start">
                  <div>
                    <h1 id="campaign-details-heading" className="text-2xl font-bold text-gray-900">
                      Campaign View
                    </h1>
                    {selectedCampaign.campaign_url && (
                      <p className="text-sm text-gray-500 mt-1">
                        Target: {selectedCampaign.campaign_url}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={handleEnhancedAnalysis}
                      disabled={startCampaignAnalysisMutation.isPending}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                    >
                      {startCampaignAnalysisMutation.isPending ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Starting Analysis...
                        </>
                      ) : (
                        'Enhanced Analysis'
                      )}
                    </button>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      selectedCampaign.monitoring_status === 'Live'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`} data-testid="campaign-status-pill">
                      {selectedCampaign.monitoring_status}
                    </span>
                  </div>
                </div>
                {/* Labeled details grid per spec */}
                <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="campaign-details-grid">
                  <div className="flex">
                    <div className="w-48 text-sm text-gray-600">Client Name</div>
                    <div className="text-sm text-gray-900" data-testid="campaign-client-name">{selectedCampaign.client_name}</div>
                  </div>
                  <div className="flex">
                    <div className="w-48 text-sm text-gray-600">Campaign Name</div>
                    <div className="text-sm text-gray-900" data-testid="campaign-name">{selectedCampaign.campaign_name}</div>
                  </div>
                  <div className="flex">
                    <div className="w-48 text-sm text-gray-600">Start Date</div>
                    <div className="text-sm text-gray-900" data-testid="campaign-start-date">{selectedCampaign.launch_date ? new Date(selectedCampaign.launch_date).toLocaleDateString() : '—'}</div>
                  </div>
                  <div className="flex">
                    <div className="w-48 text-sm text-gray-600">Monitoring Status</div>
                    <div className="text-sm text-gray-900" data-testid="campaign-monitoring-status">{selectedCampaign.monitoring_status}</div>
                  </div>
                  <div className="flex">
                    <div className="w-48 text-sm text-gray-600">Client Domain</div>
                    <div className="text-sm text-gray-900" data-testid="campaign-client-domain">{selectedCampaign.client_domain}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Results Summary */}
            {campaignResults && (
              <div className="mb-8 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <div className="text-2xl font-bold text-gray-900">
                    {campaignResults.total_results}
                  </div>
                  <div className="text-sm text-gray-500">Total Results</div>
                </div>
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <div className="text-2xl font-bold text-green-600">
                    {campaignResults.verified_coverage}
                  </div>
                  <div className="text-sm text-gray-500">Verified Coverage</div>
                </div>
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <div className="text-2xl font-bold text-blue-600">
                    {campaignResults.potential_coverage}
                  </div>
                  <div className="text-sm text-gray-500">Potential Coverage</div>
                </div>
              </div>
            )}

            {/* Analysis Status */}
            {(analyzeCampaignMutation.isPending || resultsLoading) && (
              <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-3"></div>
                  <span className="text-blue-800">
                    Analyzing campaign backlinks...
                  </span>
                </div>
              </div>
            )}

            {/* Tab Navigation */}
            {campaignResults && (
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <div className="border-b border-gray-200">
                  <nav className="-mb-px flex space-x-8 px-6">
                    <button
                      onClick={() => setActiveTab('table')}
                      className={`py-4 px-1 border-b-2 font-medium text-sm ${
                        activeTab === 'table'
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      Campaign Results
                    </button>
                    <button
                      onClick={() => setActiveTab('charts')}
                      className={`py-4 px-1 border-b-2 font-medium text-sm ${
                        activeTab === 'charts'
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      Analytics
                    </button>
                    <button
                      onClick={() => setActiveTab('tasks')}
                      className={`py-4 px-1 border-b-2 font-medium text-sm ${
                        activeTab === 'tasks'
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      Background Tasks
                    </button>
                  </nav>
                </div>
                
                <div className="p-6">
                  {activeTab === 'table' && (
                    <div>
                      {coverageRows.length > 0 ? (
                        <div className="space-y-4">
                          {/* Copy to Clipboard Button */}
                          <div className="sticky top-0 z-10 bg-white flex flex-col md:flex-row md:items-center md:justify-between gap-3 py-1">
                            <h3 className="text-lg font-medium text-gray-900">
                              Campaign Coverage Results
                            </h3>
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-600" aria-live="polite">{selectedIds.length} selected</span>
                              <select
                                value={statusFilter}
                                onChange={e => setStatusFilter((e.target.value as 'all'|'verified'|'potential'))}
                                className="px-2 py-2 text-sm border border-gray-300 rounded-md bg-white"
                                aria-label="Filter by coverage status"
                              >
                                <option value="all">All</option>
                                <option value="verified">Verified</option>
                                <option value="potential">Potential</option>
                              </select>
                              <input
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                                placeholder="Search URL or title…"
                                className="px-3 py-2 text-sm border border-gray-300 rounded-md w-56"
                                aria-label="Search coverage"
                              />
                              <button
                                onClick={copySelectedUrls}
                                disabled={copyState === 'copying'}
                                className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 disabled:opacity-50"
                                data-testid="copy-selected-button"
                                title={selectedIds.length ? `${selectedIds.length} selected` : 'No selection — copies verified by default'}
                              >
                                {copyState === 'copying' ? 'Copying…' : copyState === 'copied' ? 'Copied!' : 'Copy Selected URLs'}
                              </button>
                            </div>
                          </div>
                          
                          {/* Results Table */}
                          <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                              <thead className="bg-gray-50">
                                <tr>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    <input
                                      type="checkbox"
                                      className="rounded"
                                      checked={allSelected}
                                      ref={el => {
                                        if (el) el.indeterminate = Boolean(someSelected);
                                      }}
                                      onChange={toggleSelectAll}
                                        aria-label="Select all coverage rows"
                                        aria-checked={someSelected ? 'mixed' : allSelected}
                                    />
                                  </th>
                                  {[
                                    { key: 'first_seen', label: 'First Seen' },
                                    { key: 'page_title', label: 'Page Title' },
                                    { key: 'url', label: 'URL' },
                                    { key: 'coverage_status', label: 'Coverage Status' },
                                    { key: 'link_destination', label: 'Destination' },
                                  ].map(col => (
                                    <th
                                      key={col.key}
                                        role="columnheader"
                                      aria-sort={sortField === col.key ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
                                      onClick={() => {
                                        const key = col.key as 'first_seen' | 'page_title' | 'url' | 'coverage_status' | 'link_destination';
                                        if (sortField === key) setSortDir(prev => (prev === 'asc' ? 'desc' : 'asc'));
                                        else { setSortField(key); setSortDir(key === 'first_seen' ? 'desc' : 'asc'); }
                                      }}
                                        onKeyDown={(e) => {
                                          if (e.key === 'Enter' || e.key === ' ') {
                                            e.preventDefault();
                                            const key = col.key as 'first_seen' | 'page_title' | 'url' | 'coverage_status' | 'link_destination';
                                            if (sortField === key) setSortDir(prev => (prev === 'asc' ? 'desc' : 'asc'));
                                            else { setSortField(key); setSortDir(key === 'first_seen' ? 'desc' : 'asc'); }
                                          }
                                        }}
                                        tabIndex={0}
                                        scope="col"
                                        className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider cursor-pointer select-none focus:outline-none focus:ring-2 focus:ring-blue-500 rounded ${sortField === col.key ? 'text-blue-700' : 'text-gray-500'}`}
                                    >
                                      <span className="inline-flex items-center gap-1">
                                        {col.label}
                                        {sortField === col.key && (<span>{sortDir === 'asc' ? '▲' : '▼'}</span>)}
                                      </span>
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody className="bg-white divide-y divide-gray-200">
                                {coverageLoading && (
                                  <tr>
                                    <td colSpan={6} className="px-6 py-4 text-sm text-gray-500">
                                      Loading…
                                    </td>
                                  </tr>
                                )}
                                {!coverageLoading && pagedCoverage.map((result) => (
                                  <tr key={result.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                      <input
                                        type="checkbox"
                                        className="rounded"
                                        checked={selectedIds.includes(result.id)}
                                        onChange={() => toggleRow(result.id)}
                                          aria-label={`Select row for ${result.page_title || result.url}`}
                                      />
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                      {result.first_seen ? new Date(result.first_seen).toLocaleDateString() : 'Unknown'}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                                      {result.page_title || 'Untitled'}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-blue-600 max-w-sm truncate">
                                      <a 
                                        href={result.url} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="hover:underline"
                                      >
                                        {result.url}
                                      </a>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                      <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${
                                        result.coverage_status === 'verified'
                                          ? 'bg-green-100 text-green-800'
                                          : 'bg-blue-100 text-blue-800'
                                      }`}>
                                        {result.coverage_status === 'verified' ? (
                                          <>
                                            <CheckCircle className="w-3 h-3" /> Verified Coverage
                                          </>
                                        ) : (
                                          <>
                                            <SearchIcon className="w-3 h-3" /> Potential Coverage
                                          </>
                                        )}
                                      </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                        result.link_destination === 'blog_page' ? 'bg-indigo-100 text-indigo-800' :
                                        result.link_destination === 'homepage' ? 'bg-slate-100 text-slate-800' :
                                        result.link_destination === 'product' ? 'bg-amber-100 text-amber-800' : 'bg-gray-100 text-gray-800'
                                      }`}>
                                        {result.link_destination ? result.link_destination.split('_').map((s: string) => s[0]?.toUpperCase() + s.slice(1)).join(' ') : 'N/A'}
                                      </span>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>

                          {/* Pagination */}
                          {sortedCoverage.length > pageSize && (
                            <div className="flex items-center justify-between pt-2">
                              <div className="text-sm text-gray-600">
                                Page {page} of {totalPages} • {sortedCoverage.length} items
                              </div>
                              <div className="flex items-center gap-2">
                                <button
                                  className="px-3 py-1 text-sm border rounded disabled:opacity-50"
                                  disabled={page <= 1}
                                  onClick={() => setPage(p => Math.max(1, p - 1))}
                                >
                                  Previous
                                </button>
                                <button
                                  className="px-3 py-1 text-sm border rounded disabled:opacity-50"
                                  disabled={page >= totalPages}
                                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                >
                                  Next
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-center py-12">
                          <p className="text-gray-500">No backlink results found for this campaign.</p>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {activeTab === 'charts' && (
                    <BacklinkCharts 
                      backlinks={campaignResults ? campaignResults.results.map(r => ({
                        url_from: r.url,
                        url_to: selectedCampaign?.campaign_url || selectedCampaign?.client_domain || '',
                        title: r.page_title || 'Untitled',
                        first_seen: r.first_seen || new Date().toISOString().split('T')[0],
                        domain_rating: r.domain_rating || 0,
                        url_rating: 0,
                        ahrefs_rank: 0,
                        traffic: 0,
                        anchor: '',
                        last_seen: r.first_seen || new Date().toISOString().split('T')[0],
                        link_type: 'follow',
                        is_content: true,
                        platforms: [],
                        encoding: 'UTF-8',
                        is_redirect: false,
                        is_canonical: false
                      })) : []}
                      isLoading={resultsLoading}
                    />
                  )}

                  {activeTab === 'tasks' && (
                    <BackgroundTaskMonitor
                      userEmail={DEV_USER_EMAIL}
                      campaignId={selectedCampaign?.id}
                      className="border-0 shadow-none"
                    />
                  )}
                </div>
              </div>
            )}

            {/* Empty State */}
            {!campaignResults && !analyzeCampaignMutation.isPending && !resultsLoading && (
              <div className="text-center py-12">
                <div className="text-gray-500 text-lg">
                  Click &ldquo;Analyze Campaign&rdquo; to start backlink analysis
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create Campaign Modal */}
      <CreateCampaignModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateCampaign}
        isLoading={createCampaignMutation.isPending}
      />
    </ProtectedRoute>
  );
}
