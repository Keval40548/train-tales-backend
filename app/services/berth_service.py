from fastapi import HTTPException
from app.api.trains_routes import get_train_schedule
from app.services.common import *
from app.schemas.berth_schema import *
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import logging
import time

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
            "POST", url, headers=headers, json=payload.model_dump(), timeout=60
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_berths_between_stations_service(
    train_url, coach_url, headers, all_matched_berths, payload
):
    temp_coach_availability = []

    all_avbl_berths = []

    coach_composition_payloads = []

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
        all_matched_berths["responseMessage"] = coach_composition_list["error"]
        return all_matched_berths

    for coach in coach_composition_list["cdd"]:
        is_ac_coach = payload["isAC"] and coach["classCode"] not in ["SL", "2S"]

        is_non_ac_coach = payload["isNonAC"] and coach["classCode"] in ["SL", "2S"]

        if is_ac_coach or is_non_ac_coach:
            coach_composition_payloads.append(
                {
                    "trainNo": payload["trainNo"],
                    "jDate": payload["jDate"],
                    "boardingStation": payload["boardingStation"],
                    "remoteStation": train_schedule["stationList"][0]["stationCode"],
                    "trainSourceStation": train_schedule["stationList"][0][
                        "stationCode"
                    ],
                    "coach": coach["coachName"],
                    "cls": coach["classCode"],
                }
            )

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures_to_payload_map = {
            executor.submit(
                get_berths_by_coach_service,
                coach_url,
                headers,
                CoachCompositionSchema(**payload),
            ): payload
            for payload in coach_composition_payloads
        }

        for future in as_completed(futures_to_payload_map):
            current_payload = futures_to_payload_map[future]
            try:
                temp_coach_availability = future.result()
                temp_coach_availability["bdd"] = [
                    {**seat, "coach": current_payload["coach"]}
                    for seat in temp_coach_availability["bdd"]
                ]
                all_avbl_berths.append(temp_coach_availability["bdd"])
            except Exception as e:
                logger.error(f"Skipping {current_payload['coach']} due to error: {e}")

    logger.info("Starting search pattern")

    all_avbl_berths = list(
        {
            "cabinCoupe": berth["cabinCoupe"],
            "coach": berth["coach"],
            "berthCode": berth["berthCode"],
            "berthNo": berth["berthNo"],
            "splitNo": berthSplit["splitNo"],
            "from": berthSplit["from"],
            "to": berthSplit["to"],
            "quota": berthSplit["quota"],
            "occupancy": berthSplit["occupancy"],
            "distance": station_distance_list[berthSplit["to"]]
            - station_distance_list[berthSplit["from"]],
        }
        for coach in all_avbl_berths
        for berth in coach
        for berthSplit in berth["bsd"]
        if not berthSplit["occupancy"]
    )

    if len(all_avbl_berths):
        for berth in all_avbl_berths:
            if (
                int(station_codes[berth["from"]]) <= payload["boardingStationNumber"]
                and int(station_codes[berth["to"]])
                >= payload["destinationStationNumber"]
            ):
                all_matched_berths["berths"].append(berth)

        if len(all_matched_berths.get("berths")):
            all_matched_berths["avblBerthCount"] = len(all_matched_berths["berths"])
            all_matched_berths["isDirect"] = True
            all_matched_berths["responseMessage"] = (
                "Direct berths found between given pair of statons"
            )
        else:
            all_matched_berths["isDirect"] = False

            # Finds seat(s) with break-journeys
            while len(all_matched_berths["berths"]) < payload["numberOfPassengers"]:
                matched_berths = []
                temp_boarding_stn_index = [
                    stationIndex
                    for stationIndex, station in enumerate(
                        train_schedule["stationList"]
                    )
                    if int(station["stnSerialNumber"])
                    == payload["boardingStationNumber"]
                ][0]
                temp_boarding_stn_number = int(
                    train_schedule["stationList"][temp_boarding_stn_index][
                        "stnSerialNumber"
                    ]
                )
                temp_destination_stn_number = int(
                    train_schedule["stationList"][temp_boarding_stn_index + 1][
                        "stnSerialNumber"
                    ]
                )

                while (
                    temp_boarding_stn_number < payload["destinationStationNumber"]
                    and temp_destination_stn_number
                    <= payload["destinationStationNumber"]
                ):
                    temp_matched = []
                    for index, berth in enumerate(all_avbl_berths):
                        if (
                            int(station_codes[berth["from"]])
                            <= temp_boarding_stn_number
                            and int(station_codes[berth["to"]])
                            >= temp_destination_stn_number
                        ):
                            temp_matched.append(
                                {
                                    "index": index,
                                    "berth": berth,
                                    "distance": berth["distance"],
                                }
                            )

                    if len(temp_matched):
                        temp_matched = sorted(
                            temp_matched, key=lambda x: x["distance"], reverse=True
                        )
                        matched_berths.append(temp_matched[0]["berth"])

                        del all_avbl_berths[temp_matched[0]["index"]]

                        temp_boarding_stn_number = int(
                            station_codes[matched_berths[-1]["to"]]
                        )
                        temp_stn_list = [
                            int(station["stnSerialNumber"])
                            for station in train_schedule["stationList"]
                            if int(station["stnSerialNumber"])
                            > temp_boarding_stn_number
                        ]

                        if len(temp_stn_list):
                            temp_destination_stn_number = temp_stn_list[0]
                        else:
                            break

                    elif (
                        int(station_codes[matched_berths[-1]["to"]])
                        >= temp_boarding_stn_number
                    ):
                        break

                all_matched_berths["berths"].append(matched_berths)

            if temp_boarding_stn_number <= payload["destinationStationNumber"]:
                all_matched_berths["avblBerthCount"] = len(matched_berths)
                all_matched_berths["responseMessage"] = (
                    "Berths could not be found between given pair of stations"
                )
            elif len(matched_berths):
                all_matched_berths["breakJourneyCnt"] = len(matched_berths)
                all_matched_berths["responseMessage"] = (
                    "Berths found with break journeys"
                )
            else:
                all_matched_berths["responseMessage"] = "No matching berths found"

    return all_matched_berths
