from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tmba.api.routes import router

app = FastAPI(
    title="TMBA-OS",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "project": "TMBA-OS",
        "version": "0.1.0",
    }