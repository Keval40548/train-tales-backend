from fastapi import APIRouter
from app.core.config import envVariables
from app.schemas.berth_schema import *
from app.services.berth_service import *
from app.services.common import *
from datetime import datetime

berths = APIRouter()

headers = {
    **envVariables["default_headers"],
    "Content-Type": "application/json",
}


@berths.post("/get_berths_by_train", tags=["Berths"])
async def get_berths_by_train(payload: TrainCompositionSchema):
    landing_time = datetime.now()
    url = f"{envVariables['charting_url']}/trainComposition"

    response = get_berths_by_train_service(url, headers, payload)

    print("::::::::::::Response Time: ", calc_elapsed_time(landing_time))
    return response


@berths.post("/get_berths_by_coach", tags=["Berths"])
async def get_berths_by_coach(payload: CoachCompositionSchema):
    landing_time = datetime.now()
    url = f"{envVariables['charting_url']}/coachComposition"

    response = get_berths_by_coach_service(url, headers, payload)

    print("::::::::::::Response Time: ", calc_elapsed_time(landing_time))
    return response


@berths.post("/get_all_avbl_berths", tags=["Berths"])
async def get_all_avbl_berths(payload: VacantBerthSchema):
    url = f"{envVariables['charting_url']}/vacantBerth"

    response = get_all_avbl_berths_service(url, headers, payload)
    return response


@berths.post("/get_berths_between_stations", tags=["Berths"])
async def get_berths_between_stations(payload: BerthBetweenStationsSchema):
    landing_time = datetime.now()

    matched_berths_interface = {
        "avblBerthCount": 0,
        "isDirect": False,
        "breakJourneyCnt": 0,
        "responseTime": "",
        "responseMessage": "",
        "berths": [],
    }

    train_url = f"{envVariables['charting_url']}/trainComposition"

    coach_url = f"{envVariables['charting_url']}/coachComposition"

    matched_berths = await get_berths_between_stations_service(
        train_url=train_url,
        coach_url=coach_url,
        headers=headers,
        matched_berths=matched_berths_interface,
        payload=payload,
    )

    matched_berths["responseTime"] = calc_elapsed_time(landing_time)

    print("::::::::::::Response Time: ", matched_berths["responseTime"])
    return matched_berths
