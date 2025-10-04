from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schema import *
from datetime import datetime
import requests
import uvicorn
import os
import time
import json
import redis.asyncio as redis

app = FastAPI()

charting_url = os.environ["CHARTING_URL"]
schedule_url = os.environ["SCHEDULE_URL"]
default_headers = json.loads(os.environ["DEFAULT_HEADERS"])

origins = [
    "http://192.168.1.3:4200",
    "http://100.0.249.18:4200",
    "http://192.168.1.9:4200",
    "http://10.200.55.86:4200",
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_client = redis.Redis(host="localhost", port=6379, db=0)


@app.get("/get_all_trains", tags=["Train Details"])
async def get_all_trains():
    try:
        url = f"{schedule_url}/trainList"
        headers = {
            **default_headers,
            "Content-Type": "application/javascript",
        }
        response = requests.request("GET", url, headers=headers, timeout=60)
        response.raise_for_status()

        trains = response.text.split(",")

        for i in range(len(trains)):
            trains[i] = trains[i][1 : len(trains[i]) - 1]

        return {"trains": trains}

    except Exception as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@app.get("/get_train_schedule/{train_number}", tags=["Train Details"])
async def get_train_schedule(train_number: str):
    try:
        url = f"{schedule_url}/protected/mapps1/trnscheduleenquiry/{train_number}"
        headers = {
            **default_headers,
            "Content-Type": "application/json",
            "greq": str(int(time.time() * 1000)),
            "bmirak": "webbm",
        }
        response = requests.request("GET", url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@app.post("/get_berths_by_train", tags=["Berths"])
async def get_berths_by_train(payload: TrainCompositionSchema):
    try:
        url = f"{charting_url}/trainComposition"
        headers = {
            **default_headers,
            "Content-Type": "application/json",
        }
        response = requests.request(
            "POST", url, headers=headers, json=payload.model_dump(), timeout=60
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@app.post("/get_berths_by_coach", tags=["Berths"])
async def get_berths_by_coach(payload: CoachCompositionSchema):
    try:
        url = f"{charting_url}/coachComposition"
        headers = {
            **default_headers,
            "Content-Type": "application/json",
        }
        response = requests.request(
            "POST", url, headers=headers, json=payload.model_dump(), timeout=60
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@app.post("/get_all_avbl_berths", tags=["Berths"])
async def get_all_avbl_berths(payload: VacantBerthSchema):
    try:
        url = f"{charting_url}/vacantBerth"
        headers = {
            **default_headers,
            "Content-Type": "application/json",
        }
        response = requests.request(
            "POST", url, headers=headers, json=payload.model_dump()
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@app.post("/get_berths_between_stations", tags=["Berths"])
async def get_berths_between_stations(payload: BerthBetweenStationsSchema):
    print("::::::::::::LANDING TIME: ", datetime.now())
    payload = payload.model_dump()
    train_schedule = await get_train_schedule(payload["trainNo"])
    station_codes = {
        station["stationCode"]: station["stnSerialNumber"]
        for station in train_schedule["stationList"]
    }

    station_distance_list = {
        station["stationCode"]: int(station["distance"])
        for station in train_schedule["stationList"]
    }

    coach_composition_list = await get_berths_by_train(
        TrainCompositionSchema(**payload)
    )

    temp_coach_availability = []

    all_avbl_berths = []

    matched_berths = {
        "avbl_berth_count": 0,
        "is_direct": False,
        "berths": [],
        "errorMessage": "",
    }

    for coach in coach_composition_list["cdd"]:
        is_ac_coach = payload["isAC"] and coach["classCode"] not in ["SL", "2S"]

        is_non_ac_coach = payload["isNonAC"] and coach["classCode"] in ["SL", "2S"]

        if is_ac_coach or is_non_ac_coach:
            coach_composition_payload = {
                "trainNo": payload["trainNo"],
                "jDate": payload["jDate"],
                "boardingStation": payload["boardingStation"],
                "remoteStation": train_schedule["stationList"][0]["stationCode"],
                "trainSourceStation": train_schedule["stationList"][0]["stationCode"],
                "coach": coach["coachName"],
                "cls": coach["classCode"],
            }

            temp_coach_availability = await get_berths_by_coach(
                CoachCompositionSchema(**coach_composition_payload)
            )

            temp_coach_availability["bdd"] = [
                {**seat, "coach": coach_composition_payload["coach"]}
                for seat in temp_coach_availability["bdd"]
            ]
            all_avbl_berths.append(temp_coach_availability["bdd"])

    all_avbl_berths = {
        "avbl_berths": [item for sublist in all_avbl_berths for item in sublist]
    }

    all_avbl_berths = [
        {
            "cabinCoupe": element["cabinCoupe"],
            "coach": element["coach"],
            "berthCode": element["berthCode"],
            "berthNo": element["berthNo"],
            "splitNo": berth["splitNo"],
            "from": berth["from"],
            "to": berth["to"],
            "quota": berth["quota"],
            "occupancy": berth["occupancy"],
        }
        for element in all_avbl_berths["avbl_berths"]
        for berth in element["bsd"]
        if not berth["occupancy"]
    ]

    if len(all_avbl_berths):
        for berth in all_avbl_berths:
            if (
                int(station_codes[berth["from"]]) <= payload["boardingStationNumber"]
                and int(station_codes[berth["to"]])
                >= payload["destinationStationNumber"]
            ):
                matched_berths["berths"].append(berth)

    if not len(matched_berths.get("berths")):
        matched_berths["is_direct"] = False
        for berth in all_avbl_berths:
            berth["distance"] = (
                station_distance_list[berth["to"]]
                - station_distance_list[berth["from"]]
            )
    else:
        matched_berths["avbl_berth_count"] = len(matched_berths["berths"])
        matched_berths["is_direct"] = True
        return matched_berths

    # Finds seat(s) with break-journeys
    temp_boarding_stn_index = [
        stationIndex
        for stationIndex, station in enumerate(train_schedule["stationList"])
        if int(station["stnSerialNumber"]) == payload["boardingStationNumber"]
    ][0]
    temp_boarding_stn_number = train_schedule["stationList"][temp_boarding_stn_index][
        "stnSerialNumber"
    ]
    temp_destination_stn_number = train_schedule["stationList"][
        temp_boarding_stn_index + 1
    ]["stnSerialNumber"]

    while (
        int(temp_boarding_stn_number) < payload["destinationStationNumber"]
        and int(temp_destination_stn_number) < payload["destinationStationNumber"]
    ):
        temp_matched = []
        for berth in all_avbl_berths:
            if int(station_codes[berth["from"]]) <= int(
                temp_boarding_stn_number
            ) and int(station_codes[berth["to"]]) >= int(temp_destination_stn_number):
                temp_matched.append(berth)

        if len(temp_matched):
            temp_matched = sorted(
                temp_matched, key=lambda x: x["distance"], reverse=True
            )
            matched_berths["berths"].append(temp_matched[0])
            temp_boarding_stn_number = int(
                station_codes[matched_berths["berths"][-1]["to"]]
            )
            temp_stn_list = [
                int(station["stnSerialNumber"])
                for station in train_schedule["stationList"]
                if int(station["stnSerialNumber"]) > temp_boarding_stn_number
            ]

            if len(temp_stn_list):
                temp_destination_stn_number = temp_stn_list[0]
            else:
                break

        elif int(station_codes[matched_berths["berths"][-1]["to"]]) >= int(
            temp_destination_stn_number
        ):
            break

    if len(matched_berths):
        matched_berths["avbl_berth_count"] = len(matched_berths["berths"])
        matched_berths["errorMessage"] = "Berths found with break journeys"
    else:
        matched_berths["errorMessage"] = "No matching berths found"

    print("::::::::::::RESPONSE TIME: ", datetime.now())
    return matched_berths


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, host="0.0.0.0", reload=True)
