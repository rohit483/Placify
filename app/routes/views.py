from fastapi import APIRouter
from fastapi.responses import FileResponse
from app.config import TEMPLATE_DIR, STATIC_DIR

router = APIRouter()

#=================================== Frontend APIs ===================================
@router.get("/")
async def read_index():
    return FileResponse(TEMPLATE_DIR / 'index.html')

@router.get("/script.js")
async def read_script():
    return FileResponse(STATIC_DIR / 'script.js')
