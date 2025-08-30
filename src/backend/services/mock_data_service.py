"""
Mock Data Service for Link Dive AI
Provides realistic backlink analysis data sourced from internet research
"""

import json
import os
from typing import Dict, Optional, Any
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class MockDataService:
    """Service for loading and managing realistic mock backlink data"""
    
    def __init__(self, mock_data_dir: str = "mockdata"):
        self.mock_data_dir = mock_data_dir
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_all_mock_data()
    
    def _load_all_mock_data(self) -> None:
        """Load all mock data files into memory cache"""
        try:
            if not os.path.exists(self.mock_data_dir):
                logger.warning(f"Mock data directory not found: {self.mock_data_dir}")
                return
            
            for filename in os.listdir(self.mock_data_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.mock_data_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Extract domain from filename (e.g., "chill_ie.json" -> "chill.ie")
                            domain_key = filename.replace('.json', '').replace('_', '.')
                            self._cache[domain_key] = data
                            logger.info(f"Loaded mock data for {domain_key}")
                    except Exception as e:
                        logger.error(f"Error loading mock data from {filepath}: {e}")
        except Exception as e:
            logger.error(f"Error loading mock data directory: {e}")
    
    def _normalize_domain(self, url_or_domain: str) -> str:
        """Normalize URL or domain to consistent format"""
        if url_or_domain.startswith(('http://', 'https://')):
            parsed = urlparse(url_or_domain)
            domain = parsed.netloc
        else:
            domain = url_or_domain
        
        # Remove www. prefix for consistency
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain.lower()
    
    def get_backlink_data(self, target_url: str) -> Optional[Dict[str, Any]]:
        """Get mock backlink data for a given URL or domain"""
        domain = self._normalize_domain(target_url)
        
        # Check direct match first
        if domain in self._cache:
            return self._cache[domain]
        
        # Check with www prefix
        www_domain = f"www.{domain}"
        for key, data in self._cache.items():
            if data.get('target_domain') == domain or data.get('target_domain') == www_domain:
                return data
        
        logger.info(f"No mock data found for domain: {domain}")
        return None
    
    def get_available_domains(self) -> list[str]:
        """Get list of all domains with available mock data"""
        domains = []
        for data in self._cache.values():
            if 'target_domain' in data:
                domains.append(data['target_domain'])
        return sorted(domains)
    
    def add_mock_data(self, domain: str, data: Dict[str, Any]) -> bool:
        """Add new mock data for a domain"""
        try:
            normalized_domain = self._normalize_domain(domain)
            self._cache[normalized_domain] = data
            
            # Save to file
            filename = normalized_domain.replace('.', '_') + '.json'
            filepath = os.path.join(self.mock_data_dir, filename)
            
            os.makedirs(self.mock_data_dir, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Added mock data for {normalized_domain}")
            return True
        except Exception as e:
            logger.error(f"Error adding mock data for {domain}: {e}")
            return False
    
    def generate_fallback_data(self, target_url: str) -> Dict[str, Any]:
        """Generate realistic fallback data for unknown domains"""
        domain = self._normalize_domain(target_url)
        
        # Generate realistic but varied data based on domain characteristics
        import random
        import datetime
        
        # Base metrics influenced by domain characteristics
        base_score = 50
        if any(keyword in domain for keyword in ['google', 'microsoft', 'apple', 'amazon']):
            base_score = 95
        elif any(keyword in domain for keyword in ['github', 'stackoverflow', 'wikipedia']):
            base_score = 90
        elif domain.endswith(('.edu', '.gov')):
            base_score = 85
        elif domain.endswith('.org'):
            base_score = 75
        elif any(keyword in domain for keyword in ['blog', 'news', 'media']):
            base_score = 70
        
        variation = random.randint(-15, 15)
        domain_rating = max(10, min(100, base_score + variation))
        
        # Generate metrics based on domain rating
        total_backlinks = int(random.uniform(100, 50000) * (domain_rating / 50))
        referring_domains = int(total_backlinks * random.uniform(0.05, 0.25))
        dofollow_ratio = random.uniform(0.6, 0.8)
        dofollow_backlinks = int(total_backlinks * dofollow_ratio)
        nofollow_backlinks = total_backlinks - dofollow_backlinks
        
        return {
            "target_url": target_url,
            "target_domain": domain,
            "total_backlinks": total_backlinks,
            "referring_domains": referring_domains,
            "dofollow_backlinks": dofollow_backlinks,
            "nofollow_backlinks": nofollow_backlinks,
            "average_domain_rating": round(domain_rating, 1),
            "anchor_text_distribution": {
                domain: int(total_backlinks * 0.3),
                f"www.{domain}": int(total_backlinks * 0.2),
                "click here": int(total_backlinks * 0.1),
                "visit site": int(total_backlinks * 0.08),
                "website": int(total_backlinks * 0.05),
                "homepage": int(total_backlinks * 0.04),
                "link": int(total_backlinks * 0.03),
                "more info": int(total_backlinks * 0.02),
                "read more": int(total_backlinks * 0.02),
                "source": int(total_backlinks * 0.16)
            },
            "last_analyzed": datetime.datetime.now().isoformat() + "Z",
            "top_referring_domains": self._generate_referring_domains(referring_domains, domain_rating),
            "link_types": {
                "text": dofollow_backlinks,
                "image": int(total_backlinks * 0.15),
                "redirect": int(total_backlinks * 0.05)
            },
            "new_backlinks_last_30_days": random.randint(5, 200),
            "lost_backlinks_last_30_days": random.randint(1, 50),
            "growth_trend": "positive" if random.random() > 0.3 else "stable",
            "spam_score": round(random.uniform(0.1, 5.0), 1),
            "toxic_backlinks": random.randint(0, int(total_backlinks * 0.02)),
            "broken_backlinks": random.randint(0, int(total_backlinks * 0.05))
        }
    
    def _generate_referring_domains(self, count: int, base_rating: float) -> list[Dict[str, Any]]:
        """Generate realistic referring domains"""
        import random
        
        common_domains = [
            ("github.com", 96.9, 890000000),
            ("stackoverflow.com", 95.1, 1200000000),
            ("wikipedia.org", 96.8, 1800000000),
            ("linkedin.com", 98.2, 890000000),
            ("twitter.com", 99.1, 1800000000),
            ("facebook.com", 100.0, 2500000000),
            ("youtube.com", 99.8, 3400000000),
            ("medium.com", 94.2, 890000000),
            ("reddit.com", 96.4, 1800000000),
            ("techcrunch.com", 92.1, 450000000)
        ]
        
        referring_domains = []
        num_domains = min(count, 15)  # Show top 15 max
        
        for i in range(num_domains):
            if i < len(common_domains) and random.random() > 0.3:
                domain, dr, traffic = common_domains[i]
            else:
                # Generate random domain
                domain = f"example{random.randint(1, 1000)}.com"
                dr = random.uniform(30, 90)
                traffic = random.randint(10000, 1000000)
            
            backlinks = random.randint(1, max(1, int(count / 10)))
            
            referring_domains.append({
                "domain": domain,
                "domain_rating": round(dr, 1),
                "backlinks": backlinks,
                "first_seen": f"202{random.randint(0, 4)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                "last_seen": "2024-12-19",
                "anchor_texts": [domain.split('.')[0], "website", "link"],
                "url_rating": round(dr - random.uniform(2, 8), 1),
                "traffic": traffic,
                "link_type": "dofollow" if random.random() > 0.3 else "nofollow"
            })
        
        return sorted(referring_domains, key=lambda x: x['backlinks'], reverse=True)

# Global instance
mock_data_service = MockDataService()
