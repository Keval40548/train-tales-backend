from fastapi import FastAPI
from app.api.trains_routes import trains
from app.api.berth_routes import berths
from app.core.config import origins
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Train Tales")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trains, prefix="/trains")
app.include_router(berths, prefix="/berths")


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, host="0.0.0.0", reload=True)
