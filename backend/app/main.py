from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import init_db
from app.config import settings
from app.routers import moodle_router
from app.routers import ai_router
from app.routers import course_router
from app.routers import media_testing_router

app = FastAPI(
    title="Kometa - IA API + Moddle",
    description="Backend para la generación y publicación automática de cursos de Moodle usando IA",
    version="1.0.0"
)

# Permitimos el CORS para conectar con nuestro fronted local más adelante 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(moodle_router.router)
app.include_router(ai_router.router)
app.include_router(course_router.router)
app.include_router(media_testing_router.router)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "moodle_url_configured": settings.MOODLE_API_URL is not None
    }
