import React from 'react';
import { useAggregateCoverage } from '../hooks/useCoverage';
import { apiClient } from '../lib/api';

export const CoverageSummary: React.FC = () => {
  const { data, isLoading, error } = useAggregateCoverage();

  if (isLoading) return <div className="bg-white p-6 rounded-lg border border-gray-200">Loading coverage metrics...</div>;
  if (error || !data) return <div className="bg-white p-6 rounded-lg border border-gray-200 text-red-600">Failed to load coverage metrics</div>;

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Coverage Overview</h2>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-500 hidden sm:block">Across {data.total_campaigns} campaigns</div>
          <a
            href={`${apiClient.defaults.baseURL?.replace(/\/$/, '') || ''}/api/v1/campaigns/${data.campaigns[0]?.campaign_id || 1}/coverage/export?status=all`}
            className="text-sm text-blue-600 hover:underline"
          >Export First Campaign CSV</a>
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <MetricCard label="Total Backlinks" value={data.total_backlinks} />
        <MetricCard label="Verified" value={data.total_verified} accent="green" />
        <MetricCard label="Potential" value={data.total_potential} accent="blue" />
        <MetricCard label="Verification Rate" value={`${data.overall_verification_rate.toFixed(1)}%`} accent="indigo" />
        <MetricCard label="Avg DR" value={data.average_dr ? data.average_dr.toFixed(1) : '—'} accent="purple" />
      </div>
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-3">Destination Breakdown (Aggregated)</h3>
        <div className="flex flex-wrap gap-3">
          {aggregateDestination(data.campaigns).map(item => (
            <span key={item.destination} className="px-3 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
              {item.destination}: {item.count} ({item.percentage.toFixed(1)}%)
            </span>
          ))}
        </div>
      </div>
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">Per-Campaign Snapshot</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <Th>Campaign</Th>
                <Th>Total</Th>
                <Th>Verified</Th>
                <Th>Potential</Th>
                <Th>Verification %</Th>
                <Th>Avg DR</Th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {data.campaigns.map(c => (
                <tr key={c.campaign_id} className="hover:bg-gray-50">
                  <Td>{c.campaign_name}</Td>
                  <Td>{c.total_backlinks}</Td>
                  <Td className="text-green-600 font-medium">{c.verified_coverage}</Td>
                  <Td className="text-blue-600">{c.potential_coverage}</Td>
                  <Td>{c.verification_rate.toFixed(1)}%</Td>
                  <Td>{c.avg_domain_rating ? c.avg_domain_rating.toFixed(1) : '—'}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const MetricCard: React.FC<{ label: string; value: number | string; accent?: string }> = ({ label, value, accent }) => {
  const color = accent ? `text-${accent}-600` : 'text-gray-900';
  return (
    <div className="p-4 rounded-lg bg-gray-50">
      <div className={`text-xl font-semibold ${color}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-1 uppercase tracking-wide">{label}</div>
    </div>
  );
};

const Th: React.FC<React.PropsWithChildren> = ({ children }) => (
  <th className="px-4 py-2 text-left font-medium text-gray-600 uppercase tracking-wider text-xs">{children}</th>
);
interface TdProps { children: React.ReactNode; className?: string }
const Td: React.FC<TdProps> = ({ children, className }) => (
  <td className={`px-4 py-2 whitespace-nowrap text-gray-800 ${className || ''}`}>{children}</td>
);

import type { CampaignCoverageSummary, CoverageDestinationBreakdown } from '../types/api';

function aggregateDestination(campaigns: CampaignCoverageSummary[]) {
  const counts: Record<string, number> = {};
  let total = 0;
  campaigns.forEach(c => {
    (c.destination_breakdown || []).forEach((d: CoverageDestinationBreakdown) => {
      counts[d.destination] = (counts[d.destination] || 0) + d.count;
      total += d.count;
    });
  });
  return Object.entries(counts).map(([destination, count]) => ({
    destination,
    count,
    percentage: total ? (count / total) * 100 : 0
  }));
}
