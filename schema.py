from pydantic import BaseModel, Field
from typing import Optional

class TrainCompositionSchema(BaseModel):
    trainNo: str
    jDate: str
    boardingStation: str

class CoachCompositionSchema(BaseModel):
    trainNo: str
    boardingStation: str
    remoteStation: str
    trainSourceStation: str
    jDate: str
    coach: str
    cls: str

class VacantBerthSchema(BaseModel):
    boardingStation: str
    chartType: Optional[int] = Field(default=1)
    cls: str
    jDate: str
    remoteStation: str
    trainNo: str
    trainSourceStation: str