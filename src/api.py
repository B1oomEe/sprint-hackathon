import os
from typing import Optional

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .calculator import CalculationError, HandoverClient, calculate
from .models import CalculationRequest, CalculationResponse

app = FastAPI(title="Base Station Calculator", version="0.1.0")

# Allow browser preflight/requests from dev frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _handover_client_from_env() -> Optional[HandoverClient]:
    base_url = os.getenv("HANDOVER_BASE_URL")
    if not base_url:
        return None
    return HandoverClient(base_url.rstrip("/"))


@app.post("/api/v1/calculate", response_model=CalculationResponse)
def calculate_endpoint(payload: dict = Body(...)) -> CalculationResponse:
    client = _handover_client_from_env()
    try:
        request_model = CalculationRequest.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc

    try:
        return calculate(request_model, handover_client=client)
    except CalculationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
