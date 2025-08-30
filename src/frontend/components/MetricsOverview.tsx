/**
 * Metrics overview cards displaying key backlink statistics
 */
'use client';

import { TrendingUp, ExternalLink, Shield, Award } from 'lucide-react';

interface MetricsCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  description?: string;
}

function MetricsCard({ title, value, icon, change, changeType = 'neutral', description }: MetricsCardProps) {
  const getChangeColor = () => {
    switch (changeType) {
      case 'positive':
        return 'text-green-600';
      case 'negative':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-50 rounded-lg">
            {icon}
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
          </div>
        </div>
        {change && (
          <div className={`text-sm font-medium ${getChangeColor()}`}>
            {change}
          </div>
        )}
      </div>
      {description && (
        <p className="mt-2 text-sm text-gray-500">{description}</p>
      )}
    </div>
  );
}

interface MetricsOverviewProps {
  data?: {
    totalBacklinks: number;
    uniqueDomains: number;
    domainAuthority: number;
    trustFlow: number;
    newLinksThisMonth?: number;
    lostLinksThisMonth?: number;
  };
  isLoading?: boolean;
}

export function MetricsOverview({ data, isLoading = false }: MetricsOverviewProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg border border-gray-200 p-6 animate-pulse">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
              <div className="space-y-2">
                <div className="h-4 bg-gray-200 rounded w-20"></div>
                <div className="h-6 bg-gray-200 rounded w-16"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-12">
        <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-500">Enter a domain to see backlink metrics</p>
      </div>
    );
  }

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const getChangeString = (current?: number, isPositive = true): string | undefined => {
    if (current === undefined) return undefined;
    const sign = isPositive ? '+' : '-';
    return `${sign}${formatNumber(Math.abs(current))}`;
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Backlink Metrics Overview</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricsCard
          title="Total Backlinks"
          value={formatNumber(data.totalBacklinks)}
          icon={<ExternalLink className="h-5 w-5 text-blue-600" />}
          change={getChangeString(data.newLinksThisMonth, true)}
          changeType="positive"
          description="Total number of incoming links"
        />
        
        <MetricsCard
          title="Unique Domains"
          value={formatNumber(data.uniqueDomains)}
          icon={<Shield className="h-5 w-5 text-green-600" />}
          description="Number of unique referring domains"
        />
        
        <MetricsCard
          title="Domain Authority"
          value={`${data.domainAuthority}/100`}
          icon={<Award className="h-5 w-5 text-purple-600" />}
          description="Moz Domain Authority score"
        />
        
        <MetricsCard
          title="Trust Flow"
          value={`${data.trustFlow}/100`}
          icon={<TrendingUp className="h-5 w-5 text-orange-600" />}
          description="Majestic Trust Flow metric"
        />
      </div>

      {(data.newLinksThisMonth || data.lostLinksThisMonth) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {data.newLinksThisMonth !== undefined && (
            <MetricsCard
              title="New Links This Month"
              value={formatNumber(data.newLinksThisMonth)}
              icon={<TrendingUp className="h-5 w-5 text-green-600" />}
              changeType="positive"
              description="Recently acquired backlinks"
            />
          )}
          
          {data.lostLinksThisMonth !== undefined && (
            <MetricsCard
              title="Lost Links This Month"
              value={formatNumber(data.lostLinksThisMonth)}
              icon={<TrendingUp className="h-5 w-5 text-red-600" />}
              changeType="negative"
              description="Recently lost backlinks"
            />
          )}
        </div>
      )}
    </div>
  );
}
