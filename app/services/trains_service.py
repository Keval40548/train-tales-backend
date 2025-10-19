from fastapi import HTTPException
from app.core.config import get_redis_hash, set_redis_hash
import requests
import logging
import json

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

logger = logging.getLogger("train-tales_trains")


def get_all_trains_service(url, headers):
    try:
        response = requests.request("GET", url, headers=headers, timeout=60)
        response.raise_for_status()

        trains = response.text.split(",")

        for i in range(len(trains)):
            trains[i] = trains[i][1 : len(trains[i]) - 1]

        return {"trains": trains}

    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_train_schedule_service(url, headers, train_number):
    response = await get_redis_hash("train_schedules", train_number)

    if response is None:
        try:
            response = requests.request("GET", url, headers=headers, timeout=60)
            response.raise_for_status()
            response = response.json()
            try:
                await set_redis_hash(
                    "train_schedules", train_number, json.dumps(response), 43200
                )
            except Exception as e:
                print(
                    f"Unable to set schedule of {train_number} to Redis due to error: {e}"
                )

        except requests.exceptions.HTTPError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return response
