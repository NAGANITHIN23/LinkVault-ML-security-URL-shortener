import hashlib
import string
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.link import Link
from app.config import settings

class URLShortener:
    CHARSET = string.ascii_letters + string.digits
    
    @staticmethod
    def generate_short_code(url: str, length: int = 7) -> str:
        hash_digest = hashlib.md5(url.encode()).hexdigest()
        base_code = ''.join(random.choices(hash_digest, k=length-2))
        random_suffix = ''.join(random.choices(URLShortener.CHARSET, k=2))
        return base_code + random_suffix
    
    @staticmethod
    def create_short_link(db: Session, original_url: str, custom_code: str = None, expires_in_days: int = None) -> Link:
        if custom_code:
            existing = db.query(Link).filter(Link.short_code == custom_code).first()
            if existing:
                raise ValueError(f"Custom code '{custom_code}' already exists")
            short_code = custom_code
        else:
            for _ in range(10):
                short_code = URLShortener.generate_short_code(original_url)
                existing = db.query(Link).filter(Link.short_code == short_code).first()
                if not existing:
                    break
            else:
                raise RuntimeError("Failed to generate unique short code")
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        link = Link(
            original_url=str(original_url),
            short_code=short_code,
            expires_at=expires_at
        )
        db.add(link)
        db.commit()
        db.refresh(link)
        return link
    
    @staticmethod
    def get_original_url(db: Session, short_code: str) -> str:
        link = db.query(Link).filter(
            Link.short_code == short_code,
            Link.is_active == True
        ).first()
        
        if not link:
            raise ValueError("Link not found")
        
        if link.expires_at and link.expires_at < datetime.utcnow():
            raise ValueError("Link has expired")
        
        link.click_count += 1
        db.commit()
        return link.original_url