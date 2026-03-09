from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import input_router, extraction_router

app = FastAPI(title="AI Architecture Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(input_router.router)
app.include_router(extraction_router.router)

@app.get("/")
def health():
    return {"status": "AI Engine Running"}