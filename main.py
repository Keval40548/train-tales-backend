from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.trains_routes import trains
from app.api.berth_routes import berths
from app.core.config import origins, redis_client
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        redis_startup_state = await redis_client.ping()
        if redis_startup_state:
            print("Redis Server is up and running!")
        app.state.redis = redis_client
        yield

    except Exception as e:
        print(f"Unable to connect to the Redis server due to Error(s): {e}")

    finally:
        await app.state.redis.close()


app = FastAPI(lifespan=lifespan, title="Train Tales")

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
