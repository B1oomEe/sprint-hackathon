import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set

import httpx

from .models import (
    CalculationRequest,
    CalculationResponse,
    DistrictInput,
    DistrictResult,
    HandoverEntry,
    StationType,
)


class CalculationError(Exception):
    """Raised when input data fails validation for calculation."""


class ExternalHandoverNotFound(CalculationError):
    """Raised when external handover lookup returned 404."""


@dataclass
class HandoverClient:
    base_url: str
    timeout: float = 5.0

    def fetch(self, station_type_id: int) -> int:
        url = f"{self.base_url}/api/basestation/{station_type_id}"
        response = httpx.get(url, timeout=self.timeout)
        if response.status_code == 404:
            raise ExternalHandoverNotFound(
                f"Handover for station type {station_type_id} not found (404)"
            )
        response.raise_for_status()
        return int(response.json())


def calculate(request: CalculationRequest, handover_client: Optional[HandoverClient] = None) -> CalculationResponse:
    station_types = _build_station_type_map(request.station_types)
    handover_map = _build_handover_map(request.handovers)
    _validate_district_inputs(request.districts, station_types, handover_map, handover_client)

    results: List[DistrictResult] = []
    for district in request.districts:
        district_result = _calculate_for_district(
            district=district,
            station_types=station_types,
            handover_map=handover_map,
            pi=request.pi,
        )
        results.append(district_result)

    total_n = round(sum(result.n for result in results), 2)
    return CalculationResponse(district_results=results, total_n=total_n)


def _build_station_type_map(station_types: Sequence[StationType]) -> Dict[int, StationType]:
    station_type_map: Dict[int, StationType] = {}
    for station_type in station_types:
        if station_type.id in station_type_map:
            raise CalculationError(f"Duplicate station type id: {station_type.id}")
        station_type_map[station_type.id] = station_type
    if not station_type_map:
        raise CalculationError("At least one station type is required")
    return station_type_map


def _build_handover_map(handovers: Sequence[HandoverEntry]) -> Dict[int, int]:
    handover_map: Dict[int, int] = {}
    for handover in handovers:
        handover_map[handover.station_type_id] = handover.value
    return handover_map


def _validate_district_inputs(
    districts: Sequence[DistrictInput],
    station_types: Dict[int, StationType],
    handover_map: Dict[int, int],
    handover_client: Optional[HandoverClient],
) -> None:
    if not districts:
        raise CalculationError("No districts provided")

    for district in districts:
        unknown_types = set(district.stations) - set(station_types.keys())
        if unknown_types:
            raise CalculationError(f"Unknown station type ids in district {district.id}: {sorted(unknown_types)}")

        missing_handovers = set(district.stations) - set(handover_map.keys())
        if missing_handovers:
            if handover_client:
                for station_type_id in missing_handovers:
                    handover_map[station_type_id] = handover_client.fetch(station_type_id)
            else:
                raise CalculationError(
                    f"Missing handover values for station types in district {district.id}: {sorted(missing_handovers)}"
                )


def _calculate_for_district(
    district: DistrictInput,
    station_types: Dict[int, StationType],
    handover_map: Dict[int, int],
    pi: float,
) -> DistrictResult:
    r0 = _radius(district.area, pi)
    station_radii = [_radius(station_types[station_id].coverage_area, pi) for station_id in district.stations]

    l_value = _calculate_cells_l(district.k, r0, station_radii)
    cluster_c = _calculate_cluster_c(station_radii)

    n_value = l_value / cluster_c

    handover_avg = _calculate_handover_avg(district.stations, handover_map)
    needs_adjustment = _handover_requires_adjustment(handover_avg, district.stations, station_types)
    if needs_adjustment:
        n_value *= 1.4

    n_value = round(n_value, 2)
    handover_avg = round(handover_avg, 2)

    return DistrictResult(
        district_id=district.id,
        n=n_value,
        handover_avg=handover_avg,
        handover_adjusted=needs_adjustment,
    )


def _radius(area: float, pi: float) -> float:
    return math.sqrt(area / pi)


def _calculate_cells_l(k: float, r0: float, station_radii: Sequence[float]) -> float:
    li_values = [k * (r0 / r_i) ** 2 for r_i in station_radii]
    return sum(li_values) / len(li_values)


def _calculate_cluster_c(station_radii: Sequence[float]) -> float:
    if len(station_radii) < 3:
        raise CalculationError("At least 3 stations are required to compute cluster size")
    top_radii = sorted(station_radii, reverse=True)[:3]
    diameters = [2 * r for r in top_radii]
    d1, d2, d3 = diameters
    return d1 ** (5 / 2) + d2 ** (3 / 2) + d3 ** (1 / 2)


def _calculate_handover_avg(stations: Sequence[int], handover_map: Dict[int, int]) -> float:
    values = [handover_map[station_type] for station_type in stations]
    return sum(values) / len(values)


def _handover_requires_adjustment(
    avg_value: float,
    stations: Sequence[int],
    station_types: Dict[int, StationType],
) -> bool:
    present_types: Set[int] = set(stations)
    return any(avg_value < station_types[type_id].handover_min for type_id in present_types)
