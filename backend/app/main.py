from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.research import router as research_router
from backend.app.models.database import engine
from backend.app.models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RetailAI Research Agent API",
    description="Backend API for the RetailAI Enterprise Research Agent",
    version="1.0.0"
)

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev; restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(research_router, prefix="/api/research", tags=["research"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the RetailAI Research Agent API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
