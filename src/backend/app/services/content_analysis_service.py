"""
Content Analysis Service for Link Dive AI
Handles HTML scraping, keyword verification, and content relevance analysis
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from app.utils.datetime_utils import utc_now
import logging
import re
import asyncio
from urllib.parse import urlparse, urljoin
import aiohttp
from bs4 import BeautifulSoup

class ContentAnalysisService:
    """Service for analyzing webpage content and verifying coverage"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def verify_campaign_coverage(
        self, 
        backlink_urls: List[str], 
        verification_keywords: List[str],
        campaign_details: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Verify campaign coverage by analyzing content of backlink pages
        
        Args:
            backlink_urls: List of URLs to analyze
            verification_keywords: Keywords to look for in content
            campaign_details: Campaign information for context
        
        Returns:
            List of verification results with coverage status
        """
        results = []
        
        if not self.session:
            async with self:
                return await self._process_urls(backlink_urls, verification_keywords, campaign_details)
        else:
            return await self._process_urls(backlink_urls, verification_keywords, campaign_details)
    
    async def _process_urls(
        self, 
        urls: List[str], 
        keywords: List[str],
        campaign_details: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process multiple URLs concurrently"""
        
        # Limit concurrent requests to avoid overwhelming servers
        semaphore = asyncio.Semaphore(5)
        
        async def analyze_single_url(url: str) -> Dict[str, Any]:
            async with semaphore:
                return await self._analyze_page_content(url, keywords, campaign_details)
        
        # Process URLs concurrently
        tasks = [analyze_single_url(url) for url in urls[:50]]  # Limit to 50 URLs
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error processing URL {urls[i]}: {str(result)}")
                # Add error result
                valid_results.append({
                    "url": urls[i] if i < len(urls) else "unknown",
                    "coverage_verified": False,
                    "verification_status": "error",
                    "error": str(result),
                    "content_analysis": {}
                })
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def _analyze_page_content(
        self, 
        url: str, 
        keywords: List[str],
        campaign_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a single page for campaign coverage verification
        
        Returns:
            Dictionary with verification results and content analysis
        """
        result = {
            "url": url,
            "coverage_verified": False,
            "verification_status": "not_verified",
            "content_analysis": {
                "page_title": None,
                "meta_description": None,
                "keyword_matches": [],
                "campaign_mentions": [],
                "content_score": 0.0,
                "scraped_at": utc_now().isoformat()
            }
        }
        
        try:
            # Fetch and parse page content
            content_data = await self._fetch_page_content(url)
            
            if not content_data:
                result["verification_status"] = "fetch_failed"
                return result
            
            # Extract structured content
            result["content_analysis"].update(content_data)
            
            # Perform keyword analysis
            keyword_results = self._analyze_keywords(content_data, keywords)
            result["content_analysis"]["keyword_matches"] = keyword_results
            
            # Look for campaign-specific mentions
            campaign_mentions = self._find_campaign_mentions(content_data, campaign_details)
            result["content_analysis"]["campaign_mentions"] = campaign_mentions
            
            # Calculate content relevance score
            content_score = self._calculate_content_score(
                keyword_results, 
                campaign_mentions, 
                content_data
            )
            result["content_analysis"]["content_score"] = content_score
            
            # Determine verification status
            result["coverage_verified"] = content_score >= 0.6  # 60% threshold
            result["verification_status"] = "verified" if result["coverage_verified"] else "not_verified"
            
            self.logger.info(f"Analyzed {url}: score={content_score:.2f}, verified={result['coverage_verified']}")
            
        except Exception as e:
            self.logger.error(f"Content analysis failed for {url}: {str(e)}")
            result["verification_status"] = "error"
            result["error"] = str(e)
        
        return result
    
    async def _fetch_page_content(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch and parse HTML content from a URL
        
        Returns:
            Dictionary with extracted content or None if failed
        """
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    self.logger.warning(f"HTTP {response.status} for {url}")
                    return None
                
                # Get content type
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    self.logger.warning(f"Non-HTML content for {url}: {content_type}")
                    return None
                
                # Parse HTML
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract structured data
                return {
                    "page_title": self._extract_title(soup),
                    "meta_description": self._extract_meta_description(soup),
                    "headings": self._extract_headings(soup),
                    "body_text": self._extract_body_text(soup),
                    "links": self._extract_links(soup, url),
                    "images": self._extract_images(soup),
                    "word_count": len(self._extract_body_text(soup).split())
                }
                
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout fetching {url}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else ""
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        return meta_desc.get('content', '').strip() if meta_desc else ""
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[str]:
        """Extract all headings (h1-h6)"""
        headings = []
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                text = heading.get_text().strip()
                if text:
                    headings.append(text)
        return headings
    
    def _extract_body_text(self, soup: BeautifulSoup) -> str:
        """Extract main body text content"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text from main content areas
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        if main_content:
            return main_content.get_text().strip()
        
        return soup.get_text().strip()
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract all links with anchor text"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text().strip()
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = urljoin(base_url, href)
            
            if text and href:
                links.append({
                    "url": href,
                    "anchor_text": text
                })
        
        return links
    
    def _extract_images(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract image information"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            alt = img.get('alt', '').strip()
            
            if src:
                images.append({
                    "src": src,
                    "alt_text": alt
                })
        
        return images
    
    def _analyze_keywords(self, content_data: Dict[str, Any], keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze content for keyword matches
        
        Returns:
            List of keyword match results
        """
        if not keywords:
            return []
        
        # Combine all text content for analysis
        all_text = f"{content_data.get('page_title', '')} {content_data.get('meta_description', '')} {content_data.get('body_text', '')} {' '.join(content_data.get('headings', []))}"
        all_text_lower = all_text.lower()
        
        results = []
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Count occurrences
            count = all_text_lower.count(keyword_lower)
            
            # Find context snippets
            contexts = []
            if count > 0:
                # Use regex to find keyword with surrounding context
                pattern = rf'.{{0,50}}{re.escape(keyword_lower)}.{{0,50}}'
                matches = re.finditer(pattern, all_text_lower, re.IGNORECASE)
                contexts = [match.group().strip() for match in matches]
            
            results.append({
                "keyword": keyword,
                "matches": count,
                "contexts": contexts[:3],  # Limit to first 3 contexts
                "found_in_title": keyword_lower in content_data.get('page_title', '').lower(),
                "found_in_headings": any(keyword_lower in h.lower() for h in content_data.get('headings', [])),
                "found_in_meta": keyword_lower in content_data.get('meta_description', '').lower()
            })
        
        return results
    
    def _find_campaign_mentions(self, content_data: Dict[str, Any], campaign_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Look for specific campaign or client mentions
        
        Returns:
            List of campaign mention results
        """
        mentions = []
        
        # Extract campaign identifiers
        campaign_name = campaign_details.get("campaign_name", "")
        client_name = campaign_details.get("client_name", "")
        client_domain = campaign_details.get("client_domain", "")
        
        # Combine text for analysis
        all_text = f"{content_data.get('page_title', '')} {content_data.get('body_text', '')}"
        all_text_lower = all_text.lower()
        
        # Check for campaign name mentions
        if campaign_name:
            count = all_text_lower.count(campaign_name.lower())
            if count > 0:
                mentions.append({
                    "type": "campaign_name",
                    "text": campaign_name,
                    "matches": count
                })
        
        # Check for client name mentions
        if client_name:
            count = all_text_lower.count(client_name.lower())
            if count > 0:
                mentions.append({
                    "type": "client_name",
                    "text": client_name,
                    "matches": count
                })
        
        # Check for domain mentions
        if client_domain:
            count = all_text_lower.count(client_domain.lower())
            if count > 0:
                mentions.append({
                    "type": "client_domain",
                    "text": client_domain,
                    "matches": count
                })
        
        return mentions
    
    def _calculate_content_score(
        self, 
        keyword_results: List[Dict[str, Any]], 
        campaign_mentions: List[Dict[str, Any]],
        content_data: Dict[str, Any]
    ) -> float:
        """
        Calculate overall content relevance score (0.0 to 1.0)
        
        Scoring factors:
        - Keyword matches (40%)
        - Campaign mentions (30%)
        - Content quality indicators (30%)
        """
        score = 0.0
        
        # Keyword score (40% weight)
        if keyword_results:
            keyword_score = 0
            total_keywords = len(keyword_results)
            
            for result in keyword_results:
                kw_score = 0
                
                # Base score for any matches
                if result["matches"] > 0:
                    kw_score += 0.3
                
                # Bonus for title placement
                if result["found_in_title"]:
                    kw_score += 0.3
                
                # Bonus for heading placement
                if result["found_in_headings"]:
                    kw_score += 0.2
                
                # Bonus for meta description
                if result["found_in_meta"]:
                    kw_score += 0.2
                
                keyword_score += min(1.0, kw_score)
            
            score += (keyword_score / total_keywords) * 0.4
        
        # Campaign mention score (30% weight)
        if campaign_mentions:
            mention_score = min(1.0, len(campaign_mentions) * 0.5)
            score += mention_score * 0.3
        
        # Content quality score (30% weight)
        quality_score = 0
        
        # Check for substantial content
        word_count = content_data.get("word_count", 0)
        if word_count > 500:
            quality_score += 0.3
        elif word_count > 100:
            quality_score += 0.1
        
        # Check for structured content
        if content_data.get("page_title"):
            quality_score += 0.2
        
        if content_data.get("meta_description"):
            quality_score += 0.1
        
        if content_data.get("headings"):
            quality_score += 0.2
        
        # Check for links (indicates it's a real article/page)
        if len(content_data.get("links", [])) > 3:
            quality_score += 0.2
        
        score += min(1.0, quality_score) * 0.3
        
        return min(1.0, score)
    
    async def analyze_batch_urls(
        self, 
        urls_with_metadata: List[Dict[str, Any]], 
        campaign_details: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Analyze a batch of URLs with their metadata for campaign verification
        
        Args:
            urls_with_metadata: List of dicts with 'url' and other metadata
            campaign_details: Campaign information
        
        Returns:
            Enhanced list with content verification results
        """
        verification_keywords = campaign_details.get("verification_keywords", [])
        
        # Extract just the URLs for content analysis
        urls = [item["url"] for item in urls_with_metadata]
        
        # Perform content analysis
        content_results = await self.verify_campaign_coverage(
            backlink_urls=urls,
            verification_keywords=verification_keywords,
            campaign_details=campaign_details
        )
        
        # Merge content results back with original metadata
        enhanced_results = []
        for i, original_item in enumerate(urls_with_metadata):
            enhanced_item = original_item.copy()
            
            if i < len(content_results):
                enhanced_item.update(content_results[i])
            else:
                # Fallback if content analysis failed
                enhanced_item.update({
                    "coverage_verified": False,
                    "verification_status": "not_analyzed",
                    "content_analysis": {}
                })
            
            enhanced_results.append(enhanced_item)
        
        return enhanced_results

# Global service instance
content_analysis_service = ContentAnalysisService()
