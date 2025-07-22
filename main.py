from fastapi import FastAPI, HTTPException
import requests
from schema import *
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import time
import json

app = FastAPI()

charting_url = os.environ['CHARTING_URL']
schedule_url = os.environ['SCHEDULE_URL']
default_headers = json.loads(os.environ['DEFAULT_HEADERS'])



@app.get("/get_all_trains", tags=["Train Details"])
async def get_all_trains():
    try:
        url = f"{schedule_url}/trainList"
        headers = {
            **default_headers,
            'Content-Type': 'application/javascript',
        }
        response = requests.request("GET", url, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))



@app.get("/get_train_schedule/{train_number}", tags=["Train Details"])
async def get_train_schedule(train_number: str):
    try:
        url = f"{schedule_url}/protected/mapps1/trnscheduleenquiry/{train_number}"
        headers = {
            **default_headers,
            'Content-Type': 'application/json',
            'greq': str(int(time.time() * 1000)),
            'bmirak': 'webbm',
        }
        response = requests.request("GET", url, headers=headers)
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
            'Content-Type': 'application/json',
        }
        response = requests.request("POST", url, headers=headers, json=payload.model_dump())
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
            'Content-Type': 'application/json',
        }
        response = requests.request("POST", url, headers=headers, json=payload.model_dump())
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
            'Content-Type': 'application/json',
        }
        response = requests.request("POST", url, headers=headers, json=payload.model_dump())
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))



if __name__ == '__main__':
    uvicorn.run('main:app', port = 8000, host = '0.0.0.0', reload=True)