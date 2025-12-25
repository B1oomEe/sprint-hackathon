# Расчет количества базовых станций (FastAPI)

Сервис и библиотека для расчета требуемого количества базовых станций по ТЗ «Расчет количества базовых станций» (25.12.2025). Реализация разделяет слой расчетов и веб-API.

## Требования окружения
- Python 3.11+
- pip

Установка зависимостей:
```bash
pip install -r requirements.txt
```

## Запуск API
```bash
uvicorn src.api:app --reload
```
Базовый путь: `/api/v1`.

## Формат запроса/ответа
`POST /api/v1/calculate`

Пример запроса:
```bash
curl -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "pi": 3.141592653589793,
    "stationTypes": [
      { "id": 1, "coverageArea": 10.0, "handoverMin": 12, "handoverMax": 18 },
      { "id": 2, "coverageArea": 15.0, "handoverMin": 10, "handoverMax": 16 },
      { "id": 3, "coverageArea": 20.0, "handoverMin": 11, "handoverMax": 17 }
    ],
    "handovers": [
      { "stationTypeId": 1, "value": 14 },
      { "stationTypeId": 2, "value": 12 },
      { "stationTypeId": 3, "value": 15 }
    ],
    "districts": [
      { "id": "admir", "area": 50.0, "k": 1.21, "stations": [1, 2, 2, 3] }
    ]
  }'
```

Ответ:
```json
{
  "districtResults": [
    { "districtId": "admir", "n": 12.37, "handoverAvg": 13.25, "handoverAdjusted": false }
  ],
  "totalN": 12.37
}
```
Значения `n` и `totalN` округляются до двух знаков для вывода.

## Правила валидации
- `districts[].area > 0`, `districts[].k > 0`
- `stationTypes[].coverageArea > 0`
- В каждом районе минимум 3 станции.
- Каждый id в `districts[].stations` должен присутствовать в `stationTypes` и `handovers` (или быть получен из внешнего источника, см. ниже).
- Дубликаты id типов станций запрещены.
- При некорректных данных возвращается `400 Bad Request` с описанием ошибки. Непредвиденные ошибки — `500 Internal Error` (обрабатываются FastAPI по умолчанию).

## Расчеты
- Радиусы: `R0 = sqrt(s/pi)`, `R = sqrt(S/pi)`
- Число сот: `Li = K * (R0 / Ri)^2`, `L = среднее(Li)`
- Кластер: взять 3 максимальных `R`, посчитать `D = 2R` и `C = D1^(5/2)+D2^(3/2)+D3^(1/2)`
- `n = L / C`
- Handover: `Havg = среднее(handovers)`. Если `Havg < Hmin` хотя бы одного типа в районе — итоговое `n` умножается на `1.4`.

## Внешний источник handover
- Опциональный клиент GET `http://192.168.0.100:100/api/basestation/{id}`.
- Включение: задать `HANDOVER_BASE_URL` (например, `http://192.168.0.100:100`). Для id, отсутствующих в `handovers`, сервис попытается получить значения из внешнего источника.
- Если внешний сервис возвращает 404 — трактуется как ошибка валидации (400) и расчет прекращается.

## Тесты
```bash
pytest
```
Реализовано 11 unit-тестов, включая обязательный тест на корректировку handover.

## Использование библиотеки расчета
```python
from src.calculator import calculate
from src.models import CalculationRequest, StationType, HandoverEntry, DistrictInput

request = CalculationRequest(
    station_types=[StationType(id=1, coverage_area=10, handover_min=12, handover_max=18)],
    handovers=[HandoverEntry(station_type_id=1, value=14)],
    districts=[DistrictInput(id="demo", area=50, k=1.1, stations=[1, 1, 1])],
)
response = calculate(request)
print(response.district_results[0].n, response.total_n)
```

## Frontend (React + Vite)
UI-клиент для API расположен в `front/`.
```bash
cd front
npm install
npm run dev
```
По умолчанию запросы идут на текущий хост (`/api/v1/calculate`). Можно переопределить базовый URL через `.env`:
```
VITE_API_BASE=http://localhost:8000
```
После запуска откройте dev-сервер Vite (по умолчанию http://localhost:5173) и заполните формы типов станций, handover и районов, затем нажмите «Выполнить расчет».

Для настройки адреса бэкенда используйте `front/.env` (пример — `front/.env.example`): задайте `VITE_BACKEND_URL` или `VITE_API_BASE`.
