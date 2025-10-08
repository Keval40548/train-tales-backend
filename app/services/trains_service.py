from fastapi import HTTPException
import requests
import logging

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


def get_train_schedule_service(url, headers):
    try:
        response = requests.request("GET", url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
