import re
from urllib.parse import urlparse
import tldextract

class PhishingDetector:
    
    def __init__(self):
        self.suspicious_keywords = [
            'login', 'verify', 'account', 'update', 'secure', 'banking',
            'paypal', 'amazon', 'ebay', 'signin', 'suspended', 'locked'
        ]
        
        self.trusted_domains = [
            'google.com', 'youtube.com', 'facebook.com', 'twitter.com',
            'instagram.com', 'linkedin.com', 'github.com', 'stackoverflow.com'
        ]
    
    def extract_features(self, url: str) -> dict:
        parsed = urlparse(url)
        extracted = tldextract.extract(url)
        
        features = {
            'url_length': len(url),
            'num_dots': url.count('.'),
            'num_hyphens': url.count('-'),
            'num_underscores': url.count('_'),
            'num_slashes': url.count('/'),
            'num_digits': sum(c.isdigit() for c in url),
            'num_params': len(parsed.query.split('&')) if parsed.query else 0,
            'has_ip': bool(re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', parsed.netloc)),
            'has_at_symbol': '@' in url,
            'has_double_slash': '//' in parsed.path,
            'subdomain_count': len(extracted.subdomain.split('.')) if extracted.subdomain else 0,
            'suspicious_keywords': sum(1 for word in self.suspicious_keywords if word in url.lower()),
            'is_https': parsed.scheme == 'https',
            'domain_length': len(extracted.domain)
        }
        
        return features
    
    def calculate_risk_score(self, url: str) -> dict:
        features = self.extract_features(url)
        extracted = tldextract.extract(url)
        domain = f"{extracted.domain}.{extracted.suffix}"
        
        risk_score = 0
        reasons = []
        
        if features['url_length'] > 75:
            risk_score += 20
            reasons.append("Unusually long URL")
        
        if features['has_ip']:
            risk_score += 30
            reasons.append("Uses IP address instead of domain")
        
        if features['num_dots'] > 5:
            risk_score += 15
            reasons.append("Excessive subdomains")
        
        if features['has_at_symbol']:
            risk_score += 25
            reasons.append("Contains @ symbol (possible obfuscation)")
        
        if features['suspicious_keywords'] > 2:
            risk_score += 20
            reasons.append("Multiple suspicious keywords detected")
        
        if not features['is_https']:
            risk_score += 10
            reasons.append("Not using HTTPS")
        
        if features['num_hyphens'] > 3:
            risk_score += 15
            reasons.append("Excessive hyphens in URL")
        
        if features['has_double_slash']:
            risk_score += 20
            reasons.append("Contains double slashes in path")
        
        if domain in self.trusted_domains:
            risk_score = max(0, risk_score - 50)
            reasons = ["Verified trusted domain"]
        
        risk_level = "low"
        if risk_score > 70:
            risk_level = "high"
        elif risk_score > 40:
            risk_level = "medium"
        
        return {
            "risk_score": min(risk_score, 100),
            "risk_level": risk_level,
            "is_suspicious": risk_score > 70,
            "reasons": reasons,
            "features": features
        }

detector = PhishingDetector()