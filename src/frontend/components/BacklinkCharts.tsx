/**
 * Charts and data visualization components
 */
'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import type { BacklinkData } from '../types/api';

interface ChartsProps {
  backlinks: BacklinkData[];
  isLoading?: boolean;
}

export function BacklinkCharts({ backlinks, isLoading = false }: ChartsProps) {
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg border border-gray-200 p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-32 mb-4"></div>
              <div className="h-64 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (backlinks.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500">No data available for charts</div>
      </div>
    );
  }

  // Domain Rating Distribution
  const getDomainRatingDistribution = () => {
    const ranges = [
      { range: '0-20', min: 0, max: 20 },
      { range: '21-40', min: 21, max: 40 },
      { range: '41-60', min: 41, max: 60 },
      { range: '61-80', min: 61, max: 80 },
      { range: '81-100', min: 81, max: 100 }
    ];

    return ranges.map(({ range, min, max }) => ({
      range,
      count: backlinks.filter(b => b.domain_rating >= min && b.domain_rating <= max).length
    }));
  };

  // Link Type Distribution
  const getLinkTypeDistribution = () => {
    const types = backlinks.reduce((acc, backlink) => {
      const type = backlink.link_type || 'Unknown';
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(types).map(([type, count]) => ({
      type,
      count,
      percentage: ((count / backlinks.length) * 100).toFixed(1)
    }));
  };

  // Monthly Acquisition Trend (simulated data based on first_seen)
  const getMonthlyTrend = () => {
    const monthlyData = backlinks.reduce((acc, backlink) => {
      try {
        const date = new Date(backlink.first_seen);
        const monthKey = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`;
        acc[monthKey] = (acc[monthKey] || 0) + 1;
      } catch {
        // Skip invalid dates
      }
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(monthlyData)
      .sort(([a], [b]) => a.localeCompare(b))
      .slice(-12) // Last 12 months
      .map(([month, count]) => ({
        month: new Date(month + '-01').toLocaleDateString('en-US', { month: 'short', year: '2-digit' }),
        count
      }));
  };

  // Top Referring Domains
  const getTopReferringDomains = () => {
    const domains = backlinks.reduce((acc, backlink) => {
      try {
        const domain = new URL(backlink.url_from).hostname;
        acc[domain] = (acc[domain] || 0) + 1;
      } catch {
        acc['Unknown'] = (acc['Unknown'] || 0) + 1;
      }
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(domains)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([domain, count]) => ({
        domain: domain.replace('www.', ''),
        count
      }));
  };

  const domainRatingData = getDomainRatingDistribution();
  const linkTypeData = getLinkTypeDistribution();
  const monthlyTrendData = getMonthlyTrend();
  const topDomainsData = getTopReferringDomains();

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Backlink Analysis Charts</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Domain Rating Distribution */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Domain Rating Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={domainRatingData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Link Type Distribution */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Link Type Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={linkTypeData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ type, percentage }) => `${type} (${percentage}%)`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
              >
                {linkTypeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Monthly Acquisition Trend */}
        {monthlyTrendData.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Monthly Link Acquisition</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={monthlyTrendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#3B82F6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Top Referring Domains */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Top Referring Domains</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topDomainsData} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="domain" type="category" width={100} />
              <Tooltip />
              <Bar dataKey="count" fill="#10B981" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Summary Statistics */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Stats</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {backlinks.length}
            </div>
            <div className="text-sm text-gray-500">Total Backlinks</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {new Set(backlinks.map(b => {
                try {
                  return new URL(b.url_from).hostname;
                } catch {
                  return b.url_from;
                }
              })).size}
            </div>
            <div className="text-sm text-gray-500">Unique Domains</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {(backlinks.reduce((sum, b) => sum + (b.domain_rating || 0), 0) / backlinks.length).toFixed(1)}
            </div>
            <div className="text-sm text-gray-500">Avg Domain Rating</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {backlinks.filter(b => b.is_content).length}
            </div>
            <div className="text-sm text-gray-500">Content Links</div>
          </div>
        </div>
      </div>
    </div>
  );
}
