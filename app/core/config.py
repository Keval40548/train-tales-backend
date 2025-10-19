import redis.asyncio as redis
from fastapi import HTTPException
from typing import Optional
import os
import json

envVariables = {
    "charting_url": os.environ["CHARTING_URL"],
    "schedule_url": os.environ["SCHEDULE_URL"],
    "default_headers": json.loads(os.environ["DEFAULT_HEADERS"]),
}

origins = [
    "http://192.168.1.3:4200",
    "http://100.0.249.18:4200",
    "http://192.168.1.9:4200",
    "http://10.200.55.86:4200",
    "http://localhost:4200",
]

redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


async def set_redis_hash(hash_name, key, value, expiry: Optional[int]):
    try:
        key_entry_status = await redis_client.hset(name=hash_name, key=key, value=value)
        if key_entry_status and expiry:
            has_expiry_updated = await redis_client.hexpire(
                hash_name, expiry, key, nx=True
            )
            if has_expiry_updated == 0:
                print(f"Something went wrong! Expiry not set for {key} in {hash_name}.")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to write the data to Redis due to Error: {e}",
        )


async def get_redis_hash(hash_name, key):
    try:
        fetched_key = await redis_client.hget(name=hash_name, key=key)
        try:
            response = json.loads(fetched_key)
        except (json.JSONDecodeError, TypeError):
            response = fetched_key

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to fetch the data from Redis due to Error: {e}",
        )
