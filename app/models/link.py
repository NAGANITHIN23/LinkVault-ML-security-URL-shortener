from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Link(Base):
    __tablename__ = "links"
    
    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, nullable=False, index=True)
    short_code = Column(String(10), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    click_count = Column(Integer, default=0)
    is_phishing = Column(Boolean, default=False)
    ab_test_group = Column(String(50), nullable=True)
    risk_score = Column(Integer, default=0)
    last_checked = Column(DateTime(timezone=True), nullable=True)