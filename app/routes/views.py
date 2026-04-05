from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.config import TEMPLATE_DIR, STATIC_DIR

router = APIRouter()

#=================================== Frontend APIs ===================================
@router.get("/")
async def read_index():
    return FileResponse(TEMPLATE_DIR / 'index.html')

@router.get("/privacy-policy")
async def read_privacy_policy():
    return FileResponse(TEMPLATE_DIR / 'privacy-policy.html')

@router.get("/terms")
async def read_terms():
    return FileResponse(TEMPLATE_DIR / 'terms.html')

@router.get("/license")
async def read_license():
    return FileResponse(TEMPLATE_DIR / 'license.html')

@router.get("/script.js")
async def read_script():
    return FileResponse(STATIC_DIR / 'script.js')
