/**
 * Backlinks data table with sorting and filtering capabilities
 */
'use client';

import { useState, useMemo } from 'react';
import { ExternalLink, ArrowUpDown, ArrowUp, ArrowDown, Eye, Filter } from 'lucide-react';
import type { BacklinkData } from '../types/api';

interface BacklinksTableProps {
  backlinks: BacklinkData[];
  isLoading?: boolean;
}

type SortField = 'domain_rating' | 'url_rating' | 'anchor' | 'url_from' | 'confidence';
type SortDirection = 'asc' | 'desc';

export function BacklinksTable({ backlinks, isLoading = false }: BacklinksTableProps) {
  const [sortField, setSortField] = useState<SortField>('domain_rating');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [filterText, setFilterText] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-4 w-4 text-gray-400" />;
    }
    return sortDirection === 'asc' 
      ? <ArrowUp className="h-4 w-4 text-blue-600" />
      : <ArrowDown className="h-4 w-4 text-blue-600" />;
  };

  const filteredAndSortedBacklinks = useMemo(() => {
    let filtered = backlinks;

    // Apply text filter
    if (filterText) {
      const search = filterText.toLowerCase();
      filtered = backlinks.filter(
        (backlink) =>
          backlink.url_from.toLowerCase().includes(search) ||
          backlink.anchor.toLowerCase().includes(search) ||
          backlink.url_to.toLowerCase().includes(search)
      );
    }

    // Apply sorting
    return [...filtered].sort((a, b) => {
      let aValue: string | number;
      let bValue: string | number;

      switch (sortField) {
        case 'domain_rating':
          aValue = a.domain_rating || 0;
          bValue = b.domain_rating || 0;
          break;
        case 'url_rating':
          aValue = a.url_rating || 0;
          bValue = b.url_rating || 0;
          break;
        case 'anchor':
          aValue = a.anchor.toLowerCase();
          bValue = b.anchor.toLowerCase();
          break;
        case 'url_from':
          aValue = a.url_from.toLowerCase();
          bValue = b.url_from.toLowerCase();
          break;
        case 'confidence':
          aValue = a.confidence_score ?? a.content_relevance_score ?? 0;
          bValue = b.confidence_score ?? b.content_relevance_score ?? 0;
          break;
        default:
          aValue = 0;
          bValue = 0;
      }

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      return sortDirection === 'asc' 
        ? (aValue as number) - (bValue as number)
        : (bValue as number) - (aValue as number);
    });
  }, [backlinks, sortField, sortDirection, filterText]);

  const formatUrl = (url: string): string => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname;
    } catch {
      return url;
    }
  };

  const getScoreColor = (score: number | null): string => {
    if (!score) return 'text-gray-400';
    if (score >= 70) return 'text-green-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <div className="h-6 bg-gray-200 rounded w-48 animate-pulse"></div>
        </div>
        <div className="p-6 space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex space-x-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded flex-1"></div>
              <div className="h-4 bg-gray-200 rounded w-20"></div>
              <div className="h-4 bg-gray-200 rounded w-20"></div>
              <div className="h-4 bg-gray-200 rounded w-20"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">
          Backlinks ({filteredAndSortedBacklinks.length})
        </h2>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center space-x-2 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          <Filter className="h-4 w-4" />
          <span>Filters</span>
        </button>
      </div>

      {showFilters && (
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Search backlinks
            </label>
            <input
              type="text"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              placeholder="Search by URL, anchor text..."
              className="block w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('url_from')}
                    className="flex items-center space-x-1 hover:text-gray-900"
                  >
                    <span>Source</span>
                    {getSortIcon('url_from')}
                  </button>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Coverage</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Destination</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('anchor')}
                    className="flex items-center space-x-1 hover:text-gray-900"
                  >
                    <span>Anchor Text</span>
                    {getSortIcon('anchor')}
                  </button>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('domain_rating')}
                    className="flex items-center space-x-1 hover:text-gray-900"
                  >
                    <span>DR</span>
                    {getSortIcon('domain_rating')}
                  </button>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('url_rating')}
                    className="flex items-center space-x-1 hover:text-gray-900"
                  >
                    <span>UR</span>
                    {getSortIcon('url_rating')}
                  </button>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Link Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button onClick={() => handleSort('confidence')} className="flex items-center space-x-1 hover:text-gray-900">
                    <span>Confidence</span>
                    {getSortIcon('confidence')}
                  </button>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAndSortedBacklinks.map((backlink, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {formatUrl(backlink.url_from)}
                        </div>
                        <div className="text-sm text-gray-500 truncate max-w-xs">
                          {backlink.url_from}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${ backlink.coverage_status === 'verified' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800' }`}>
                      {backlink.coverage_status || '—'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {backlink.link_destination || '—'}
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900 max-w-xs truncate">
                      {backlink.anchor || 'N/A'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`text-sm font-medium ${getScoreColor(backlink.domain_rating)}`}>
                      {backlink.domain_rating || 'N/A'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`text-sm font-medium ${getScoreColor(backlink.url_rating)}`}>
                      {backlink.url_rating || 'N/A'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-900">{backlink.link_type}</span>
                      {backlink.is_content && (
                        <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                          Content
                        </span>
                      )}
                      {backlink.is_redirect && (
                        <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">
                          Redirect
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {backlink.confidence_score ?? backlink.content_relevance_score ?? '—'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex space-x-2">
                      <a
                        href={backlink.url_from}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-900"
                        title="View source page"
                      >
                        <Eye className="h-4 w-4" />
                      </a>
                      <a
                        href={backlink.url_to}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-900"
                        title="View target page"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {filteredAndSortedBacklinks.length === 0 && (
            <div className="text-center py-12">
              <ExternalLink className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">
                {filterText ? 'No backlinks match your search' : 'No backlinks found'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
