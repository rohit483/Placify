# Copyright (C) 2026 ROHIT CHAWDA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import STATIC_DIR, COMPANIES_FILE, BASE_DIR
from app.database import init_db, seed_companies_from_json
from app.routes import api, views

app = FastAPI()

# Initialize database tables on startup
@app.on_event("startup")
def on_startup():
    init_db()
    print("Database tables created / verified.")
    seed_companies_from_json(str(COMPANIES_FILE))

# Mount Static Files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Mount Image Files
IMAGE_DIR = BASE_DIR / "image"
if IMAGE_DIR.exists():
    app.mount("/image", StaticFiles(directory=str(IMAGE_DIR)), name="image")

# Include Routers
app.include_router(api.router)
app.include_router(views.router)

# Run the app
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
