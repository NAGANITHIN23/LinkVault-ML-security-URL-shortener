from app.services.phishing_detector import detector

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