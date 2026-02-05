from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db, Base, engine
from app.api.routes import links
from app.services.cache import cache
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LinkVault Pro",
    description="Intelligent URL Shortener",
    version="1.0.0"
)

templates = Jinja2Templates(directory="app/templates")
app.include_router(links.router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard")
def dashboard():
    return FileResponse("app/static/dashboard.html")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/{short_code}")
async def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    from app.models.link import Link
    
    cached_url = cache.get_url(short_code)
    
    if cached_url:
        cache.increment_clicks(short_code)
        return RedirectResponse(url=cached_url, status_code=307)
    
    link = db.query(Link).filter(
        Link.short_code == short_code,
        Link.is_active == True
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if link.expires_at and link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Link has expired")
    
    link.click_count += 1
    db.commit()
    
    cache.set_url(short_code, link.original_url)
    cache.increment_clicks(short_code)
    
    return RedirectResponse(url=link.original_url, status_code=307)