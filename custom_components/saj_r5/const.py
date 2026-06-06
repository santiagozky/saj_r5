"""Constants for the SAJ R5 integration."""

from __future__ import annotations

DOMAIN = "saj_r5"

DEFAULT_NAME = "SAJ R5 Inverter"
DEFAULT_POLLING_TIME = 30
MIN_POLLING_TIME = 5
MAX_POLLING_TIME = 3600

CONF_POLLING_TIME = "polling_time"

ENDPOINT_PATH = "/status/status.php"
