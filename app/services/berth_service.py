from fastapi import HTTPException
from app.api.trains_routes import get_train_schedule
import requests
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

logger = logging.getLogger("train-tales_berths")


def get_berths_by_train_service(url, headers, payload):
    try:
        response = requests.request(
            "POST", url, headers=headers, json=payload.model_dump()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_berths_by_coach_service(url, headers, payload):
    try:
        response = requests.request(
            "POST", url, headers=headers, json=payload.model_dump()
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_all_avbl_berths_service(url, headers, payload):
    try:
        response = requests.request(
            "POST", url, headers=headers, json=payload.model_dump()
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
