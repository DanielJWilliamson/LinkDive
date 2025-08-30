/**
 * Domain input and search component for Link Dive AI
 */
'use client';

import { useState } from 'react';
import { Search, Globe, TrendingUp } from 'lucide-react';

interface DomainInputProps {
  onSearch: (domain: string) => void;
  isLoading?: boolean;
}

export function DomainInput({ onSearch, isLoading = false }: DomainInputProps) {
  const [domain, setDomain] = useState('');
  const [error, setError] = useState('');

  const validateDomain = (input: string): boolean => {
    // Remove protocol if present
    const cleanDomain = input.replace(/^https?:\/\//, '').replace(/\/.*$/, '');
    
    // Basic domain validation
    const domainRegex = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
    return domainRegex.test(cleanDomain) && cleanDomain.length > 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!domain.trim()) {
      setError('Please enter a domain');
      return;
    }

    if (!validateDomain(domain)) {
      setError('Please enter a valid domain (e.g., example.com)');
      return;
    }

    // Clean domain before sending
    const cleanDomain = domain.replace(/^https?:\/\//, '').replace(/\/.*$/, '');
    onSearch(cleanDomain);
  };

  const handleExampleClick = (exampleDomain: string) => {
    setDomain(exampleDomain);
    setError('');
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center space-x-2">
          <TrendingUp className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">Link Dive AI</h1>
        </div>
        <p className="text-gray-600 text-lg">
          Comprehensive SEO backlink analysis powered by premium data sources
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Globe className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="Enter domain to analyze (e.g., example.com)"
            className={`block w-full pl-10 pr-12 py-3 border rounded-lg text-sm placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              error ? 'border-red-300' : 'border-gray-300'
            }`}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            <Search className={`h-5 w-5 ${isLoading ? 'text-gray-400' : 'text-blue-600 hover:text-blue-700'}`} />
          </button>
        </div>
        
        {error && (
          <p className="text-red-600 text-sm">{error}</p>
        )}

        <button
          type="submit"
          disabled={isLoading || !domain.trim()}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Analyzing...' : 'Analyze Backlinks'}
        </button>
      </form>

      <div className="text-center space-y-3">
        <p className="text-sm text-gray-500">Try these test examples:</p>
        <div className="space-y-3">
          {/* Primary Test Domain */}
          <div className="border rounded-lg p-4 bg-blue-50">
            <p className="text-xs text-blue-600 font-medium mb-2">Primary Test Domain</p>
            <button
              onClick={() => handleExampleClick('www.chill.ie')}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              disabled={isLoading}
            >
              www.chill.ie
            </button>
            <p className="text-xs text-gray-600 mt-1">Ireland&apos;s leading online retailer</p>
          </div>
          
          {/* Additional Test Options */}
          <div>
            <p className="text-xs text-gray-500 mb-2">Additional test domains:</p>
            <div className="flex flex-wrap justify-center gap-2">
              {[
                { domain: 'github.com', desc: 'Development platform' },
                { domain: 'stackoverflow.com', desc: 'Q&A community' },
                { domain: 'techcrunch.com', desc: 'Tech news' },
                { domain: 'example.com', desc: 'Test domain' }
              ].map((example) => (
                <button
                  key={example.domain}
                  onClick={() => handleExampleClick(example.domain)}
                  className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                  disabled={isLoading}
                  title={example.desc}
                >
                  {example.domain}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
