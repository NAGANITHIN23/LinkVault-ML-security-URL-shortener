from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.database import get_db
from app.schemas.link import LinkCreate, LinkResponse
from app.services.shortener import URLShortener
from app.services.cache import cache
from app.services.phishing_detector import detector
from app.services.qr_generator import qr_generator
from app.config import settings

router = APIRouter(prefix="/api/links", tags=["links"])

@router.post("/shorten", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
def create_short_link(link_data: LinkCreate, db: Session = Depends(get_db)):
    
    phishing_result = detector.calculate_risk_score(str(link_data.original_url))
    
    if phishing_result['is_suspicious']:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "URL flagged as potentially malicious",
                "risk_score": phishing_result['risk_score'],
                "risk_level": phishing_result['risk_level'],
                "reasons": phishing_result['reasons']
            }
        )
    
    try:
        link = URLShortener.create_short_link(
            db=db,
            original_url=str(link_data.original_url),
            custom_code=link_data.custom_code,
            expires_in_days=link_data.expires_in_days
        )
        
        cache.set_url(link.short_code, link.original_url)
        
        return LinkResponse(
            short_code=link.short_code,
            original_url=link.original_url,
            short_url=f"{settings.BASE_URL}/{link.short_code}",
            created_at=link.created_at,
            expires_at=link.expires_at,
            click_count=link.click_count
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/analyze")
def analyze_url(url: str):
    return detector.calculate_risk_score(url)

class BulkLinkCreate(BaseModel):
    urls: List[str]

class BulkLinkResponse(BaseModel):
    successful: List[LinkResponse]
    failed: List[dict]

@router.post("/bulk", response_model=BulkLinkResponse)
def create_bulk_links(bulk_data: BulkLinkCreate, db: Session = Depends(get_db)):
    successful = []
    failed = []
    
    for url in bulk_data.urls:
        try:
            phishing_result = detector.calculate_risk_score(url)
            
            if phishing_result['is_suspicious']:
                failed.append({
                    "url": url,
                    "reason": "Flagged as suspicious",
                    "risk_score": phishing_result['risk_score']
                })
                continue
            
            link = URLShortener.create_short_link(db=db, original_url=url)
            cache.set_url(link.short_code, link.original_url)
            
            successful.append(LinkResponse(
                short_code=link.short_code,
                original_url=link.original_url,
                short_url=f"{settings.BASE_URL}/{link.short_code}",
                created_at=link.created_at,
                expires_at=link.expires_at,
                click_count=link.click_count
            ))
        except Exception as e:
            failed.append({"url": url, "reason": str(e)})
    
    return {"successful": successful, "failed": failed}

@router.get("/all", response_model=list[LinkResponse])
def get_all_links(db: Session = Depends(get_db)):
    from app.models.link import Link
    links = db.query(Link).filter(Link.is_active == True).order_by(Link.created_at.desc()).all()
    
    return [
        LinkResponse(
            short_code=link.short_code,
            original_url=link.original_url,
            short_url=f"{settings.BASE_URL}/{link.short_code}",
            created_at=link.created_at,
            expires_at=link.expires_at,
            click_count=link.click_count
        )
        for link in links
    ]

@router.get("/stats/summary")
def get_stats_summary(db: Session = Depends(get_db)):
    from app.models.link import Link
    from sqlalchemy import func
    
    total_links = db.query(func.count(Link.id)).filter(Link.is_active == True).scalar()
    total_clicks = db.query(func.sum(Link.click_count)).filter(Link.is_active == True).scalar() or 0
    
    top_links = db.query(Link).filter(Link.is_active == True).order_by(Link.click_count.desc()).limit(10).all()
    
    return {
        "total_links": total_links,
        "total_clicks": total_clicks,
        "top_links": [
            {
                "short_code": link.short_code,
                "original_url": link.original_url,
                "click_count": link.click_count
            }
            for link in top_links
        ]
    }

@router.get("/{short_code}/qr")
def get_qr_code(short_code: str, size: int = 300, db: Session = Depends(get_db)):
    from app.models.link import Link
    
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    short_url = f"{settings.BASE_URL}/{link.short_code}"
    qr_data = qr_generator.generate_qr_code(short_url, size)
    
    return {"qr_code": qr_data, "short_url": short_url}

@router.get("/{short_code}", response_model=LinkResponse)
def get_link_info(short_code: str, db: Session = Depends(get_db)):
    from app.models.link import Link
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return LinkResponse(
        short_code=link.short_code,
        original_url=link.original_url,
        short_url=f"{settings.BASE_URL}/{link.short_code}",
        created_at=link.created_at,
        expires_at=link.expires_at,
        click_count=link.click_count
    )