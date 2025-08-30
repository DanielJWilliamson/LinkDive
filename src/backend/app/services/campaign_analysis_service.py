"""
Enhanced Campaign Analysis Service for Link Dive AI
Implements campaign-specific backlink analysis with coverage classification
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
import logging
from urllib.parse import urlparse
import re

from .link_analysis_service import LinkAnalysisService
from app.models.campaign import (
    CampaignResponse,
    BacklinkResultResponse
)

class CampaignAnalysisService:
    """Enhanced service for campaign-specific backlink analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.link_analyzer = LinkAnalysisService()
    
    async def analyze_campaign_comprehensive(
        self, 
        campaign: Dict[str, Any],
        analysis_depth: str = "standard"
    ) -> Dict[str, Any]:
        """
        Comprehensive campaign analysis following the specification requirements
        
        Args:
            campaign: Campaign data dictionary
            analysis_depth: "quick", "standard", or "deep"
        
        Returns:
            Dictionary with campaign analysis results
        """
        try:
            self.logger.info(f"Starting comprehensive analysis for campaign {campaign.get('id')}")
            
            results = {
                "campaign_id": campaign.get("id"),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "analysis_depth": analysis_depth,
                "verified_coverage": [],
                "potential_coverage": [],
                "excluded_results": [],
                "summary": {
                    "total_results": 0,
                    "verified_count": 0,
                    "potential_count": 0,
                    "excluded_count": 0
                },
                "analysis_steps": []
            }
            
            # Step 1: Campaign URL Analysis (if provided)
            if campaign.get("campaign_url"):
                self.logger.info("Step 1: Analyzing campaign URL backlinks")
                campaign_url_results = await self._analyze_campaign_url(campaign)
                results["verified_coverage"].extend(campaign_url_results)
                results["analysis_steps"].append("campaign_url_analysis")
            
            # Step 2: Domain-wide Discovery
            self.logger.info("Step 2: Analyzing domain-wide backlinks")
            domain_results = await self._analyze_domain_wide(campaign)
            
            # Classify domain results
            for result in domain_results:
                classification = self._classify_coverage(result, campaign)
                
                if classification == "verified":
                    results["verified_coverage"].append(result)
                elif classification == "potential":
                    results["potential_coverage"].append(result)
                else:  # excluded
                    results["excluded_results"].append(result)
            
            results["analysis_steps"].append("domain_wide_analysis")
            
            # Step 3: Enhanced filtering based on campaign criteria
            self.logger.info("Step 3: Applying campaign-specific filters")
            results = self._apply_campaign_filters(results, campaign)
            results["analysis_steps"].append("campaign_filtering")
            
            # Step 4: Content analysis simulation (placeholder for future HTML scraping)
            if analysis_depth in ["standard", "deep"]:
                self.logger.info("Step 4: Content relevance analysis")
                results = await self._analyze_content_relevance(results, campaign)
                results["analysis_steps"].append("content_analysis")
            
            # Update summary
            results["summary"]["total_results"] = (
                len(results["verified_coverage"]) + 
                len(results["potential_coverage"])
            )
            results["summary"]["verified_count"] = len(results["verified_coverage"])
            results["summary"]["potential_count"] = len(results["potential_coverage"])
            results["summary"]["excluded_count"] = len(results["excluded_results"])
            
            self.logger.info(f"Campaign analysis completed: {results['summary']}")
            return results
            
        except Exception as e:
            self.logger.error(f"Campaign analysis failed: {str(e)}")
            return {
                "campaign_id": campaign.get("id"),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "verified_coverage": [],
                "potential_coverage": [],
                "summary": {"total_results": 0, "verified_count": 0, "potential_count": 0}
            }
    
    async def _analyze_campaign_url(self, campaign: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Step 1: Analyze backlinks pointing directly to the campaign URL
        These are classified as "Verified Coverage" if they meet criteria
        """
        results = []
        campaign_url = campaign.get("campaign_url", "")
        
        if not campaign_url:
            return results
        
        try:
            # Use existing link analysis service to get backlinks to campaign URL
            domain = urlparse(campaign_url).netloc
            backlink_profile = await self.link_analyzer.get_backlink_profile(domain)
            
            # Filter for backlinks that point to the specific campaign URL
            for backlink in backlink_profile.backlinks:
                if campaign_url in backlink.url_to or self._urls_match(backlink.url_to, campaign_url):
                    result = {
                        "id": len(results) + 1,
                        "url": backlink.url_from,
                        "page_title": self._extract_title_from_url(backlink.url_from),
                        "first_seen": backlink.first_seen.date() if backlink.first_seen else None,
                        "last_seen": backlink.last_seen.date() if backlink.last_seen else None,
                        "coverage_status": "verified",  # Direct links to campaign URL
                        "source_api": "ahrefs",
                        "domain_rating": backlink.domain_rating,
                        "confidence_score": "0.95",  # High confidence for direct links
                        "classification_reason": "direct_campaign_url_link",
                        "anchor_text": backlink.anchor_text,
                        "link_type": backlink.link_type
                    }
                    results.append(result)
            
            self.logger.info(f"Found {len(results)} direct campaign URL backlinks")
            return results
            
        except Exception as e:
            self.logger.error(f"Campaign URL analysis failed: {str(e)}")
            return []
    
    async def _analyze_domain_wide(self, campaign: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Step 2: Analyze backlinks to the entire domain
        These need further classification based on campaign criteria
        """
        results = []
        client_domain = campaign.get("client_domain", "")
        
        if not client_domain:
            return results
        
        try:
            # Get comprehensive domain backlinks
            backlink_profile = await self.link_analyzer.get_backlink_profile(client_domain)
            
            # Convert to results format
            for backlink in backlink_profile.backlinks:
                # Skip if this is already covered in campaign URL analysis
                campaign_url = campaign.get("campaign_url", "")
                if campaign_url and (campaign_url in backlink.url_to or self._urls_match(backlink.url_to, campaign_url)):
                    continue
                
                result = {
                    "id": len(results) + 1,
                    "url": backlink.url_from,
                    "page_title": self._extract_title_from_url(backlink.url_from),
                    "first_seen": backlink.first_seen.date() if backlink.first_seen else None,
                    "last_seen": backlink.last_seen.date() if backlink.last_seen else None,
                    "coverage_status": "potential",  # Will be reclassified
                    "source_api": "ahrefs",
                    "domain_rating": backlink.domain_rating,
                    "confidence_score": "0.75",  # Medium confidence for domain links
                    "classification_reason": "domain_wide_link",
                    "anchor_text": backlink.anchor_text,
                    "link_type": backlink.link_type,
                    "target_url": backlink.url_to
                }
                results.append(result)
            
            self.logger.info(f"Found {len(results)} domain-wide backlinks")
            return results
            
        except Exception as e:
            self.logger.error(f"Domain-wide analysis failed: {str(e)}")
            return []
    
    def _classify_coverage(self, result: Dict[str, Any], campaign: Dict[str, Any]) -> str:
        """
        Classify a backlink result as 'verified', 'potential', or 'excluded'
        Based on specification requirements
        """
        try:
            # Check blacklist first
            blacklist_domains = campaign.get("blacklist_domains", [])
            source_domain = urlparse(result["url"]).netloc
            
            for blacklisted in blacklist_domains:
                if blacklisted.lower() in source_domain.lower():
                    return "excluded"
            
            # Verified Coverage criteria (per specification):
            verified_criteria = 0
            max_criteria = 4
            
            # 1. Domain Rating >= 8 (specification requirement)
            if result.get("domain_rating", 0) >= 8:
                verified_criteria += 1
            
            # 2. First seen before campaign launch date
            launch_date = campaign.get("launch_date")
            if launch_date and result.get("first_seen"):
                if isinstance(launch_date, str):
                    launch_date = datetime.fromisoformat(launch_date).date()
                elif isinstance(launch_date, datetime):
                    launch_date = launch_date.date()
                
                if result["first_seen"] <= launch_date:
                    verified_criteria += 1
            
            # 3. Direct link to campaign URL (handled in campaign URL analysis)
            campaign_url = campaign.get("campaign_url", "")
            target_url = result.get("target_url", "")
            if campaign_url and target_url and self._urls_match(target_url, campaign_url):
                verified_criteria += 2  # Higher weight for direct links
            
            # 4. High-quality anchor text match
            anchor_text = result.get("anchor_text", "").lower()
            campaign_name = campaign.get("campaign_name", "").lower()
            client_name = campaign.get("client_name", "").lower()
            
            if campaign_name in anchor_text or client_name in anchor_text:
                verified_criteria += 1
            
            # Classification decision
            verification_threshold = 2  # Need at least 2 criteria for verified
            if verified_criteria >= verification_threshold:
                return "verified"
            else:
                return "potential"
                
        except Exception as e:
            self.logger.error(f"Coverage classification failed: {str(e)}")
            return "potential"  # Default to potential on error
    
    def _apply_campaign_filters(self, results: Dict[str, Any], campaign: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply campaign-specific filters to refine results
        """
        try:
            # Apply minimum domain rating filter (configurable, default 5)
            min_domain_rating = 5
            
            def meets_quality_threshold(result_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
                return [
                    result for result in result_list 
                    if result.get("domain_rating", 0) >= min_domain_rating
                ]
            
            # Filter all result categories
            results["verified_coverage"] = meets_quality_threshold(results["verified_coverage"])
            results["potential_coverage"] = meets_quality_threshold(results["potential_coverage"])
            
            # Sort by quality (domain rating + first seen date)
            def quality_score(result: Dict[str, Any]) -> float:
                dr_score = result.get("domain_rating", 0) / 100  # Normalize DR
                date_score = 0
                if result.get("first_seen"):
                    # More recent = higher score
                    days_ago = (date.today() - result["first_seen"]).days
                    date_score = max(0, 1 - (days_ago / 365))  # Decay over a year
                
                return dr_score + date_score
            
            results["verified_coverage"].sort(key=quality_score, reverse=True)
            results["potential_coverage"].sort(key=quality_score, reverse=True)
            
            # Limit results to prevent overwhelming users
            max_results_per_category = 100
            results["verified_coverage"] = results["verified_coverage"][:max_results_per_category]
            results["potential_coverage"] = results["potential_coverage"][:max_results_per_category]
            
            return results
            
        except Exception as e:
            self.logger.error(f"Campaign filtering failed: {str(e)}")
            return results
    
    async def _analyze_content_relevance(self, results: Dict[str, Any], campaign: Dict[str, Any]) -> Dict[str, Any]:
        """
        Placeholder for content relevance analysis
        In production, this would scrape HTML and analyze content for verification keywords
        """
        try:
            verification_keywords = campaign.get("verification_keywords", [])
            if not verification_keywords:
                return results
            
            # Simulate content analysis by checking anchor text and URL patterns
            for result_list in [results["verified_coverage"], results["potential_coverage"]]:
                for result in result_list:
                    relevance_score = self._calculate_relevance_score(result, verification_keywords)
                    result["content_relevance_score"] = relevance_score
                    
                    # Adjust confidence based on relevance
                    current_confidence = float(result.get("confidence_score", "0.5"))
                    adjusted_confidence = min(1.0, current_confidence + (relevance_score * 0.2))
                    result["confidence_score"] = f"{adjusted_confidence:.2f}"
            
            return results
            
        except Exception as e:
            self.logger.error(f"Content relevance analysis failed: {str(e)}")
            return results
    
    def _calculate_relevance_score(self, result: Dict[str, Any], keywords: List[str]) -> float:
        """
        Calculate content relevance score based on keywords
        In production, this would analyze scraped HTML content
        """
        if not keywords:
            return 0.5
        
        # Analyze anchor text and URL for keyword matches
        text_to_analyze = f"{result.get('anchor_text', '')} {result.get('url', '')}".lower()
        
        matches = 0
        for keyword in keywords:
            if keyword.lower() in text_to_analyze:
                matches += 1
        
        return min(1.0, matches / len(keywords))
    
    def _urls_match(self, url1: str, url2: str) -> bool:
        """Check if two URLs refer to the same resource"""
        try:
            parsed1 = urlparse(url1.lower())
            parsed2 = urlparse(url2.lower())
            
            # Compare domain and path
            return (parsed1.netloc == parsed2.netloc and 
                    parsed1.path.rstrip('/') == parsed2.path.rstrip('/'))
        except:
            return False
    
    def _extract_title_from_url(self, url: str) -> str:
        """
        Extract a readable title from URL
        In production, this would scrape the actual page title
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            path = parsed.path.strip('/')
            
            if path:
                # Try to create a readable title from path
                title_parts = path.split('/')[-1].replace('-', ' ').replace('_', ' ')
                return f"{title_parts.title()} - {domain}"
            else:
                return f"Homepage - {domain}"
        except:
            return "Unknown Page"
    
    def convert_to_api_response(self, analysis_results: Dict[str, Any], campaign: CampaignResponse) -> Dict[str, Any]:
        """
        Convert analysis results to API response format
        """
        try:
            # Combine verified and potential coverage
            all_results = []
            
            for result in analysis_results.get("verified_coverage", []):
                backlink_result = BacklinkResultResponse(
                    id=result["id"],
                    url=result["url"],
                    page_title=result.get("page_title"),
                    first_seen=result.get("first_seen"),
                    coverage_status="verified",
                    source_api=result.get("source_api", "ahrefs"),
                    domain_rating=result.get("domain_rating"),
                    confidence_score=result.get("confidence_score")
                )
                all_results.append(backlink_result)
            
            for result in analysis_results.get("potential_coverage", []):
                backlink_result = BacklinkResultResponse(
                    id=result["id"] + 1000,  # Offset to avoid ID conflicts
                    url=result["url"],
                    page_title=result.get("page_title"),
                    first_seen=result.get("first_seen"),
                    coverage_status="potential",
                    source_api=result.get("source_api", "ahrefs"),
                    domain_rating=result.get("domain_rating"),
                    confidence_score=result.get("confidence_score")
                )
                all_results.append(backlink_result)
            
            return {
                "campaign": campaign,
                "results": all_results,
                "total_results": len(all_results),
                "verified_coverage": len(analysis_results.get("verified_coverage", [])),
                "potential_coverage": len(analysis_results.get("potential_coverage", [])),
                "analysis_metadata": {
                    "analysis_timestamp": analysis_results.get("analysis_timestamp"),
                    "analysis_steps": analysis_results.get("analysis_steps", []),
                    "excluded_count": len(analysis_results.get("excluded_results", []))
                }
            }
            
        except Exception as e:
            self.logger.error(f"API response conversion failed: {str(e)}")
            return {
                "campaign": campaign,
                "results": [],
                "total_results": 0,
                "verified_coverage": 0,
                "potential_coverage": 0,
                "error": str(e)
            }

# Global service instance
campaign_analysis_service = CampaignAnalysisService()
