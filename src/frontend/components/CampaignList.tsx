'use client';

import { useState } from 'react';
import { Plus, Search, Calendar, Globe, PlayCircle, PauseCircle } from 'lucide-react';
import { UserProfile } from './auth/UserProfile';

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

interface CampaignListProps {
  campaigns: Campaign[];
  onCampaignSelect: (campaign: Campaign) => void;
  onNewCampaign: () => void;
  isLoading?: boolean;
}

export function CampaignList({ 
  campaigns, 
  onCampaignSelect, 
  onNewCampaign, 
  isLoading = false 
}: CampaignListProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'live' | 'paused'>('all');

  const filteredCampaigns = campaigns.filter(campaign => {
    // Normalize strings: lowercase and strip non-alphanumeric for punctuation-agnostic matching
    const normalize = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '');
    const term = normalize(searchTerm);

    // Empty term should match all
    const matchesSearch = term === ''
      ? true
      : normalize(campaign.client_name).includes(term) ||
        normalize(campaign.campaign_name).includes(term);

    // Status filter remains combined with search
    const matchesStatus =
      statusFilter === 'all' ||
      campaign.monitoring_status.toLowerCase() === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading campaigns...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Link Dive AI</h1>
              <p className="mt-2 text-gray-600">PR Campaign Monitoring Dashboard</p>
            </div>
            <div className="flex items-center space-x-4">
              <UserProfile />
              <button
                onClick={onNewCampaign}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add New Campaign
              </button>
            </div>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="mb-6 bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search by campaign or client name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  aria-label="Search campaigns"
                  data-testid="campaigns-search-input"
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-700"
                />
              </div>
            </div>
            <div className="sm:w-48">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as 'all' | 'live' | 'paused')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900"
              >
                <option value="all" className="text-gray-900">All Statuses</option>
                <option value="live" className="text-gray-900">Live</option>
                <option value="paused" className="text-gray-900">Paused</option>
              </select>
            </div>
          </div>
        </div>

        {/* Campaign Grid */}
        {filteredCampaigns.length === 0 ? (
          <div className="text-center py-12">
            <Globe className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No campaigns found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {campaigns.length === 0 
                ? "Get started by creating your first campaign." 
                : "Try adjusting your search or filter criteria."
              }
            </p>
            {campaigns.length === 0 && (
              <div className="mt-6">
                <button
                  onClick={onNewCampaign}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Campaign
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCampaigns.map((campaign) => (
              <div
                key={campaign.id}
                onClick={() => onCampaignSelect(campaign)}
                className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
                data-testid="campaign-card"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-medium text-gray-900 truncate">
                      {campaign.campaign_name}
                    </h3>
                    <p className="text-sm text-gray-600 truncate">
                      {campaign.client_name}
                    </p>
                  </div>
                  <div className="flex items-center ml-2">
                    {campaign.monitoring_status === 'Live' ? (
                      <PlayCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <PauseCircle className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </div>

                <div className="mt-4 space-y-2">
                  <div className="flex items-center text-sm text-gray-500">
                    <Globe className="w-4 h-4 mr-2" />
                    {campaign.client_domain}
                  </div>
                  {campaign.launch_date && (
                    <div className="flex items-center text-sm text-gray-500">
                      <Calendar className="w-4 h-4 mr-2" />
                      Launch: {formatDate(campaign.launch_date)}
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>Created: {formatDate(campaign.created_at)}</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      campaign.monitoring_status === 'Live'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {campaign.monitoring_status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Summary Stats */}
        {campaigns.length > 0 && (
          <div className="mt-8 bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Campaign Summary</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{campaigns.length}</div>
                <div className="text-sm text-gray-500">Total Campaigns</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {campaigns.filter(c => c.monitoring_status === 'Live').length}
                </div>
                <div className="text-sm text-gray-500">Live Campaigns</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-600">
                  {campaigns.filter(c => c.monitoring_status === 'Paused').length}
                </div>
                <div className="text-sm text-gray-500">Paused Campaigns</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
