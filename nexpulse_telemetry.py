"""Best-effort server-side telemetry reporting to NexPulse."""

import logging
from typing import Any
from urllib.parse import urlparse

import requests
import streamlit as st

logger = logging.getLogger(__name__)
DEFAULT_INGEST_URL = "https://nexplus-nachiket-space.vercel.app/api/v1/telemetry/events"


def _send(resource: str, payload: dict[str, Any]) -> bool:
    """Send one telemetry record without disrupting the study planner."""
    try:
        ingest_url = str(st.secrets.get("NEXPULSE_INGEST_URL", DEFAULT_INGEST_URL)).rstrip("/")
        key = st.secrets["NEXPULSE_INGEST_KEY"]
        service_id = st.secrets["NEXPULSE_SERVICE_ID"]
    except (KeyError, FileNotFoundError):
        logger.info("NexPulse telemetry is not configured; skipping report.")
        return False

    # Accept either the full events URL used in setup instructions or the API base URL.
    parsed_url = urlparse(ingest_url)
    if (
        parsed_url.scheme != "https"
        or parsed_url.netloc != "nexplus-nachiket-space.vercel.app"
        or parsed_url.path not in {"/api/v1/telemetry", "/api/v1/telemetry/events"}
        or parsed_url.query
        or parsed_url.fragment
    ):
        logger.warning("NexPulse telemetry URL is invalid; not sending telemetry.")
        return False
    if ingest_url.endswith("/events"):
        ingest_url = ingest_url[:-len("/events")]
    body = {"service_id": service_id, **payload}
    try:
        response = requests.post(
            f"{ingest_url}/{resource}",
            headers={"X-Ingest-Key": key},
            json=body,
            timeout=5,
        )
        if response.status_code != 202:
            logger.warning("NexPulse rejected %s telemetry with HTTP %s.", resource, response.status_code)
            return False
        return True
    except requests.RequestException as exc:
        logger.warning("NexPulse %s telemetry could not be sent (%s).", resource, type(exc).__name__)
        return False


def report_plan_generation(outcome: str, duration_ms: int, error_type: str | None = None) -> None:
    """Report a plan-generation event, metrics, and a privacy-safe log."""
    success = outcome == "success"
    validation_error = outcome == "validation_error"
    status_code = 200 if success else 400 if validation_error else 500
    duration_ms = max(0, int(duration_ms))

    event: dict[str, Any] = {
        "method": "POST",
        "endpoint": "/generate-study-plan",
        "status_code": status_code,
        "duration_ms": duration_ms,
        "outcome": "success" if success else "error",
    }
    if error_type:
        event["error_type"] = error_type[:160]
    _send("events", event)

    _send("metrics", {
        "metric_name": "study_plan_generation_success",
        "value": 1 if success else 0,
        "window_seconds": 60,
        "labels": {"outcome": "success" if success else "validation_error" if validation_error else "error"},
    })
    _send("metrics", {
        "metric_name": "study_plan_generation_duration_ms",
        "value": duration_ms,
        "window_seconds": 60,
        "labels": {"outcome": "success" if success else "validation_error" if validation_error else "error"},
    })

    _send("logs", {
        "level": "INFO" if success else "WARN" if validation_error else "ERROR",
        "message": "Study plan generation completed." if success else "Study plan generation validation failed." if validation_error else "Study plan generation failed.",
        "metadata": {"error_type": error_type[:160]} if error_type else {},
    })
