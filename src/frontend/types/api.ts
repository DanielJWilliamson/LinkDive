/**
 * TypeScript interfaces for Link Dive AI data models
 */

export interface BacklinkData {
  url_from: string;
  url_to: string;
  anchor: string;
  first_seen: string;
  last_seen: string;
  domain_rating: number;
  url_rating: number;
  ahrefs_rank?: number;
  traffic?: number;
  link_type: string;
  is_content: boolean;
  is_redirect: boolean;
  is_canonical: boolean;
}

export interface DomainMetrics {
  domain: string;
  domain_rating: number;
  ahrefs_rank?: number;
  organic_traffic?: number;
  organic_keywords?: number;
  backlinks_count: number;
  referring_domains: number;
}

export interface BacklinkResponse {
  target: string;
  total_backlinks: number;
  total_referring_domains: number;
  data_sources: string[];
  backlinks: BacklinkData[];
  metadata: {
    analysis_date: string;
    mode: string;
    limit: number;
    offset: number;
    processing_time_ms: number;
    dofollow_percentage?: number;
    domain_authority_avg?: number;
  };
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  version: string;
  uptime: number;
  environment: string;
}

export interface DetailedHealthStatus extends HealthStatus {
  database: {
    status: string;
    response_time_ms: number;
  };
  redis: {
    status: string;
    response_time_ms: number;
  };
  external_apis: {
    ahrefs: {
      status: string;
      response_time_ms: number;
    };
    dataforseo: {
      status: string;
      response_time_ms: number;
    };
  };
  system: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
  };
}

export interface CompetitorAnalysisRequest {
  target_domain: string;
  competitor_domains: string[];
  analysis_depth: 'basic' | 'standard' | 'deep';
}

export interface LinkOpportunity {
  target_url: string;
  source_domain: string;
  competitor_domain: string;
  anchor_suggestion: string;
  priority_score: number;
  opportunity_type: string;
  estimated_effort: string;
}

export interface CompetitorAnalysisResponse {
  target_domain: string;
  competitors: string[];
  analysis_timestamp: string;
  analysis_depth: string;
  total_opportunities: number;
  opportunities: LinkOpportunity[];
  summary: {
    high_priority_opportunities: number;
    medium_priority_opportunities: number;
    low_priority_opportunities: number;
  };
}

export interface RiskAlert {
  risk_type: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
  affected_urls: string[];
  recommendation: string;
  detected_date: string;
}

export interface RiskAssessment {
  domain: string;
  scan_date: string;
  total_risks: number;
  severity_breakdown: {
    high: number;
    medium: number;
    low: number;
  };
  risks: RiskAlert[];
}
