from fastapi import APIRouter
from app.core.config import envVariables
from app.services.trains_service import *
from app.services.common import *
from datetime import datetime
import time

trains = APIRouter()


@trains.get("/get_all_trains", tags=["Train Details"])
async def get_all_trains():
    landing_time = datetime.now()
    url = f"{envVariables['schedule_url']}/trainList"
    headers = {
        **envVariables["default_headers"],
        "Content-Type": "application/javascript",
    }
    response = get_all_trains_service(url, headers)

    print("::::::::::::Response Time: ", calc_elapsed_time(landing_time))
    return response


@trains.get("/get_train_schedule/{train_number}", tags=["Train Details"])
async def get_train_schedule(train_number: str):
    landing_time = datetime.now()
    url = f"{envVariables['schedule_url']}/protected/mapps1/trnscheduleenquiry/{train_number}"
    headers = {
        **envVariables["default_headers"],
        "Content-Type": "application/json",
        "greq": str(int(time.time() * 1000)),
        "bmirak": "webbm",
    }

    response = get_train_schedule_service(url, headers)

    print("::::::::::::Response Time: ", calc_elapsed_time(landing_time))
    return response
