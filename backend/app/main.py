from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.routers.api import router

app = FastAPI(
    title="TA System Backend API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/docs/openapi.json",
    redoc_url=None
)

# origins = [
#     "http://localhost:5173",
#     "http://localhost:8080",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(router, prefix="/api", tags=["API"])

@app.get("/")
def read_root():
    return {"message": "TA System Backend API"}
