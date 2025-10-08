from pydantic import BaseModel, Field
from typing import Optional


class TrainCompositionSchema(BaseModel):
    trainNo: str
    jDate: str
    boardingStation: str


class CoachCompositionSchema(BaseModel):
    boardingStation: str
    trainNo: str
    remoteStation: str
    trainSourceStation: str
    jDate: str
    coach: str
    cls: str

    model_config = {"extra": "ignore"}


class VacantBerthSchema(BaseModel):
    chartType: Optional[int] = Field(default=1)
    cls: str
    jDate: str
    remoteStation: str
    trainNo: str
    trainSourceStation: str
    boardingStation: str

    model_config = {"extra": "ignore"}


class BerthBetweenStationsSchema(BaseModel):
    trainNo: str
    jDate: str
    boardingStation: str
    boardingStationNumber: int
    destinationStation: str
    destinationStationNumber: int
    isAC: bool = Field(default=True)
    isNonAC: bool = Field(default=True)
