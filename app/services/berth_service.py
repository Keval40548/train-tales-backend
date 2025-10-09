from fastapi import HTTPException
from app.api.trains_routes import get_train_schedule
from app.services.common import *
from app.schemas.berth_schema import *
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


async def get_berths_between_stations_service(
    train_url, coach_url, headers, matched_berths, payload
):
    temp_coach_availability = []

    all_avbl_berths = []

    train_schedule = await get_train_schedule(payload["trainNo"], False)
    station_codes = {
        station["stationCode"]: station["stnSerialNumber"]
        for station in train_schedule["stationList"]
    }

    station_distance_list = {
        station["stationCode"]: int(station["distance"])
        for station in train_schedule["stationList"]
    }

    coach_composition_list = get_berths_by_train_service(
        url=train_url, headers=headers, payload=TrainCompositionSchema(**payload)
    )

    if coach_composition_list["cdd"] is None and coach_composition_list["error"]:
        matched_berths["responseMessage"] = coach_composition_list["error"]
        return matched_berths

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

            temp_coach_availability = get_berths_by_coach_service(
                url=coach_url,
                headers=headers,
                payload=CoachCompositionSchema(**coach_composition_payload),
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
        matched_berths["isDirect"] = False
        for berth in all_avbl_berths:
            berth["distance"] = (
                station_distance_list[berth["to"]]
                - station_distance_list[berth["from"]]
            )
    else:
        matched_berths["avblBerthCount"] = len(matched_berths["berths"])
        matched_berths["isDirect"] = True
        matched_berths["responseMessage"] = (
            "Direct berths found between given pair of statons"
        )
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
            temp_boarding_stn_number
        ):
            break

    if temp_boarding_stn_number <= payload["destinationStationNumber"]:
        matched_berths["avblBerthCount"] = len(matched_berths["berths"])
        matched_berths["responseMessage"] = (
            "Berths could not be found between given pair of stations"
        )
    elif len(matched_berths["berths"]):
        matched_berths["breakJourneyCnt"] = len(matched_berths["berths"])
        matched_berths["responseMessage"] = "Berths found with break journeys"
    else:
        matched_berths["responseMessage"] = "No matching berths found"

    return matched_berths
