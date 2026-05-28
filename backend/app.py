"""FastAPI application entry point for CodeSuite Diagnostics Demo backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import router

app = FastAPI(
    title="CodeSuite Diagnostics Demo API",
    description="Backend API for intelligent CI/CD failure diagnosis using MCP servers and Bedrock",
    version="0.1.0",
)

# CORS configuration - allow demo UI to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "codesuite-diagnostics-backend"}


app.include_router(router, prefix="/api")
