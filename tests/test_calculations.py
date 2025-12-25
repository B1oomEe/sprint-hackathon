import math

import pytest
from fastapi.testclient import TestClient

from src import api
from src.calculator import (
    CalculationError,
    _calculate_cells_l,
    _calculate_cluster_c,
    _calculate_handover_avg,
    _handover_requires_adjustment,
    _radius,
    calculate,
)
from src.models import CalculationRequest, DistrictInput, HandoverEntry, StationType


PI = 3.141592653589793


def _sample_station_types():
    return [
        StationType(id=1, coverage_area=10.0, handover_min=12, handover_max=18),
        StationType(id=2, coverage_area=15.0, handover_min=10, handover_max=16),
        StationType(id=3, coverage_area=20.0, handover_min=11, handover_max=17),
    ]


def _sample_handovers():
    return [
        HandoverEntry(station_type_id=1, value=14),
        HandoverEntry(station_type_id=2, value=12),
        HandoverEntry(station_type_id=3, value=15),
    ]


def test_radius_district():
    assert _radius(50.0, PI) == pytest.approx(math.sqrt(50.0 / PI))


def test_radius_station():
    assert _radius(10.0, PI) == pytest.approx(math.sqrt(10.0 / PI))


def test_cells_li():
    r0 = _radius(50.0, PI)
    ri = _radius(10.0, PI)
    k = 1.21
    expected = k * (r0 / ri) ** 2
    assert _calculate_cells_l(k, r0, [ri]) == pytest.approx(expected)


def test_cells_l_average_multiple():
    r0 = _radius(50.0, PI)
    radii = [_radius(10.0, PI), _radius(15.0, PI), _radius(20.0, PI)]
    k = 1.15
    expected = sum(k * (r0 / r) ** 2 for r in radii) / len(radii)
    assert _calculate_cells_l(k, r0, radii) == pytest.approx(expected)


def test_cluster_pick_top3_and_sort():
    radii = [1.0, 2.0, 5.0, 4.0]  # top three must be 5,4,2
    c_value = _calculate_cluster_c(radii)
    d1, d2, d3 = 2 * 5.0, 2 * 4.0, 2 * 2.0
    expected = d1 ** (5 / 2) + d2 ** (3 / 2) + d3 ** (1 / 2)
    assert c_value == pytest.approx(expected)


def test_cluster_formula_values():
    radii = [_radius(12.0, PI), _radius(8.0, PI), _radius(6.0, PI)]
    d1, d2, d3 = [2 * r for r in radii]
    expected = d1 ** (5 / 2) + d2 ** (3 / 2) + d3 ** (1 / 2)
    assert _calculate_cluster_c(radii) == pytest.approx(expected)


def test_n_base_formula_without_handover_adjustment():
    station_types = [
        StationType(id=1, coverage_area=12.0, handover_min=5, handover_max=15),
        StationType(id=2, coverage_area=8.0, handover_min=5, handover_max=15),
        StationType(id=3, coverage_area=6.0, handover_min=5, handover_max=15),
    ]
    handovers = [
        HandoverEntry(station_type_id=1, value=10),
        HandoverEntry(station_type_id=2, value=10),
        HandoverEntry(station_type_id=3, value=10),
    ]
    district = DistrictInput(id="demo", area=30.0, k=1.1, stations=[1, 2, 3])

    r0 = _radius(district.area, PI)
    station_radii = [_radius(st.coverage_area, PI) for st in station_types]
    l_value = _calculate_cells_l(district.k, r0, station_radii)
    c_value = _calculate_cluster_c(station_radii)
    expected_n = round(l_value / c_value, 2)

    request = CalculationRequest(
        pi=PI, station_types=station_types, handovers=handovers, districts=[district]
    )
    response = calculate(request)

    assert response.district_results[0].n == pytest.approx(expected_n)
    assert response.district_results[0].handover_adjusted is False


def test_handover_avg():
    handovers = [
        HandoverEntry(station_type_id=1, value=12),
        HandoverEntry(station_type_id=2, value=18),
    ]
    stations = [1, 1, 2]
    expected_avg = (12 + 12 + 18) / 3
    assert _calculate_handover_avg(stations, {1: 12, 2: 18}) == pytest.approx(expected_avg)


def test_handover_adjustment_required():
    station_types = [
        StationType(id=1, coverage_area=10.0, handover_min=15, handover_max=18),
        StationType(id=2, coverage_area=12.0, handover_min=10, handover_max=16),
        StationType(id=3, coverage_area=14.0, handover_min=9, handover_max=16),
    ]
    handovers = [
        HandoverEntry(station_type_id=1, value=10),
        HandoverEntry(station_type_id=2, value=11),
        HandoverEntry(station_type_id=3, value=11),
    ]
    district = DistrictInput(id="h", area=40.0, k=1.0, stations=[1, 2, 3])
    request = CalculationRequest(
        pi=PI, station_types=station_types, handovers=handovers, districts=[district]
    )
    response = calculate(request)
    radii_for_district = [
        _radius(next(st.coverage_area for st in station_types if st.id == station_id), PI)
        for station_id in district.stations
    ]
    base_l = _calculate_cells_l(district.k, _radius(district.area, PI), radii_for_district)
    base_c = _calculate_cluster_c(radii_for_district)
    expected_n = round((base_l / base_c) * 1.4, 2)

    result = response.district_results[0]
    assert result.handover_adjusted is True
    assert result.n == pytest.approx(expected_n)
    assert _handover_requires_adjustment(result.handover_avg, district.stations, {st.id: st for st in station_types})


def test_total_sum_matches_districts():
    station_types = _sample_station_types()
    handovers = _sample_handovers()
    districts = [
        DistrictInput(id="d1", area=50.0, k=1.21, stations=[1, 2, 2, 3]),
        DistrictInput(id="d2", area=45.0, k=1.05, stations=[3, 3, 2]),
    ]
    request = CalculationRequest(
        pi=PI, station_types=station_types, handovers=handovers, districts=districts
    )
    response = calculate(request)
    total_from_districts = round(
        sum(result.n for result in response.district_results),
        2,
    )
    assert response.total_n == total_from_districts


def test_api_validation_missing_handover_returns_400():
    station_types = _sample_station_types()
    payload = {
        "pi": PI,
        "stationTypes": [st.model_dump(by_alias=True) for st in station_types],
        "handovers": [],  # missing handovers intentionally
        "districts": [
            {"id": "d", "area": 50.0, "k": 1.2, "stations": [1, 2, 3]},
        ],
    }
    client = TestClient(api.app)
    response = client.post("/api/v1/calculate", json=payload)
    assert response.status_code == 400
    assert "Missing handover values" in response.json()["detail"]
