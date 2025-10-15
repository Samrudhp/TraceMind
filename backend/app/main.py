"""Main FastAPI application for TraceMind."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

from app.api.routes import router, init_services
from app.services.compaction import get_compaction_service
from app.services.chroma_client import get_chroma_service
from app.services.embeddings import get_embedding_service

# Scheduler for periodic compaction
scheduler = BackgroundScheduler()


def scheduled_compaction():
    """Run compaction on schedule."""
    print("Running scheduled compaction...")
    try:
        chroma = get_chroma_service()
        embeddings = get_embedding_service()
        compaction = get_compaction_service(chroma, embeddings)
        stats = compaction.run_compaction()
        print(f"Scheduled compaction complete: {stats['before_count']} -> {stats['after_count']}")
    except Exception as e:
        print(f"Error in scheduled compaction: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    print("Starting TraceMind backend...")
    
    # Initialize services
    init_services()
    
    # Start scheduler (run compaction every 30 minutes)
    scheduler.add_job(
        scheduled_compaction,
        'interval',
        minutes=30,
        id='compaction_job'
    )
    scheduler.start()
    print("Scheduler started (compaction runs every 30 minutes)")
    
    yield
    
    # Shutdown
    print("Shutting down TraceMind backend...")
    scheduler.shutdown()


# Create FastAPI app
app = FastAPI(
    title="TraceMind API",
    description="Autonomous Cognitive Vector Memory System",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "TraceMind",
        "version": "0.1.0",
        "description": "Autonomous Cognitive Vector Memory System",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
