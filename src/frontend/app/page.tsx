'use client';

import { useState } from 'react';
import { CampaignList } from '../components/CampaignList';
import { CoverageSummary } from '../components/CoverageSummary';
import Link from 'next/link';
import { CreateCampaignModal } from '../components/CreateCampaignModal';
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
  const [selectedCampaign, setSelectedCampaign] = useState<LocalCampaign | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'table' | 'charts' | 'tasks'>('table');

  // API hooks
  const { data: campaigns = [], isLoading: campaignsLoading, error: campaignsError } = useCampaigns();
  const createCampaignMutation = useCreateCampaign();
  const analyzeCampaignMutation = useAnalyzeCampaign();
  const startCampaignAnalysisMutation = useStartCampaignAnalysis();
  const { 
    data: campaignResults, 
    isLoading: resultsLoading 
  } = useCampaignResults(selectedCampaign?.id || null);

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
        userEmail: 'user@example.com', // TODO: Get from auth context
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
            Expected backend at: http://127.0.0.1:8000
          </p>
        </div>
      </div>
    );
  }

  return (
    <ProtectedRoute>
      {viewMode === 'campaigns' ? (
        <div className="space-y-8">
          <CampaignList
            campaigns={campaigns}
            onCampaignSelect={handleCampaignSelect}
            onNewCampaign={() => setShowCreateModal(true)}
            isLoading={campaignsLoading}
          />
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
              <div className="mb-8 bg-white rounded-lg border border-gray-200 p-6">
                <div className="flex justify-between items-start">
                  <div>
                    <h1 className="text-2xl font-bold text-gray-900">
                      {selectedCampaign.campaign_name}
                    </h1>
                    <p className="text-gray-600">
                      {selectedCampaign.client_name} • {selectedCampaign.client_domain}
                    </p>
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
                    }`}>
                      {selectedCampaign.monitoring_status}
                    </span>
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
                      {campaignResults.results.length > 0 ? (
                        <div className="space-y-4">
                          {/* Copy to Clipboard Button */}
                          <div className="flex justify-between items-center">
                            <h3 className="text-lg font-medium text-gray-900">
                              Campaign Coverage Results
                            </h3>
                            <button className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100">
                              Copy Selected URLs to Clipboard
                            </button>
                          </div>
                          
                          {/* Results Table */}
                          <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                              <thead className="bg-gray-50">
                                <tr>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    <input type="checkbox" className="rounded" />
                                  </th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    First Seen
                                  </th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Page Title
                                  </th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    URL
                                  </th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Coverage Status
                                  </th>
                                </tr>
                              </thead>
                              <tbody className="bg-white divide-y divide-gray-200">
                                {campaignResults.results.map((result) => (
                                  <tr key={result.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                      <input type="checkbox" className="rounded" />
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
                                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                        result.coverage_status === 'verified'
                                          ? 'bg-green-100 text-green-800'
                                          : 'bg-blue-100 text-blue-800'
                                      }`}>
                                        {result.coverage_status === 'verified' ? 'Verified Coverage' : 'Potential Coverage'}
                                      </span>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
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
                      userEmail="user@example.com" // TODO: Get from auth context
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
