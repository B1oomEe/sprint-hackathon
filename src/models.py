import math
from typing import List

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)


class StationType(CamelModel):
    id: int
    coverage_area: float = Field(..., gt=0)
    handover_min: int
    handover_max: int


class HandoverEntry(CamelModel):
    station_type_id: int
    value: int


class DistrictInput(CamelModel):
    id: str
    area: float = Field(..., gt=0)
    k: float = Field(..., gt=0)
    stations: List[int]

    @field_validator("stations")
    @classmethod
    def validate_stations(cls, value: List[int]) -> List[int]:
        if len(value) < 3:
            raise ValueError("Each district must include at least 3 stations")
        return value


class CalculationRequest(CamelModel):
    pi: float = Field(default=math.pi, gt=0)
    station_types: List[StationType]
    handovers: List[HandoverEntry]
    districts: List[DistrictInput]


class DistrictResult(CamelModel):
    district_id: str
    n: float
    handover_avg: float
    handover_adjusted: bool


class CalculationResponse(CamelModel):
    district_results: List[DistrictResult]
    total_n: float
