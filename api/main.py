from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database.database import init_db
from api.routes import auth, earning, tasks, referral, withdrawal, admin

app = FastAPI(title="EarnMoney BD API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for Web App
app.mount("/webapp", StaticFiles(directory="webapp", html=True), name="webapp")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(earning.router, prefix="/api/earning", tags=["earning"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(referral.router, prefix="/api/referral", tags=["referral"])
app.include_router(withdrawal.router, prefix="/api/withdrawal", tags=["withdrawal"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "EarnMoney BD API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
