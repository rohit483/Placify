from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from app.config import TEMPLATE_DIR, STATIC_DIR, BASE_DIR

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

#=================================== Frontend APIs ===================================
@router.get("/")
async def read_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"title": "Placify - Home"})

@router.get("/privacy-policy")
async def read_privacy_policy(request: Request):
    return templates.TemplateResponse(request=request, name="privacy-policy.html", context={"title": "Placify - Privacy Policy"})

@router.get("/support")
async def read_support(request: Request):
    return templates.TemplateResponse(request=request, name="support.html", context={"title": "Placify - Support Us"})

@router.get("/terms")
async def read_terms(request: Request):
    return templates.TemplateResponse(request=request, name="terms.html", context={"title": "Placify - Terms & Conditions"})

@router.get("/license")
async def read_license():
    return FileResponse(BASE_DIR / 'LICENSE', media_type='text/plain')

@router.get("/script.js")
async def read_script():
    return FileResponse(STATIC_DIR / 'script.js')
