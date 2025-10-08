import redis.asyncio as redis
import os
import json

redis_client = redis.Redis(host="localhost", port=6379, db=0)

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
