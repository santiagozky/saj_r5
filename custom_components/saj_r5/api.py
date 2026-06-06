"""Client and parser for SAJ R5 inverter status data."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from aiohttp import BasicAuth, ClientError, ClientResponseError, ClientSession

from .const import ENDPOINT_PATH

UNAVAILABLE_VALUE = 65535


class SajR5Error(Exception):
    """Base exception for SAJ R5 errors."""


class SajR5CannotConnectError(SajR5Error):
    """Raised when the inverter cannot be reached."""


class SajR5AuthenticationError(SajR5Error):
    """Raised when credentials are rejected by the inverter."""


class SajR5InvalidResponseError(SajR5Error):
    """Raised when the inverter returns unexpected data."""


@dataclass(frozen=True)
class SajR5ValueDescription:
    """Description for one raw inverter value."""

    key: str
    index: int
    converter: Callable[[int], Any] = float


def _scaled(divisor: int | float) -> Callable[[int], float]:
    """Return a converter that scales a raw integer value."""

    return lambda value: value / divisor


def _status(value: int) -> str:
    """Convert the raw online/offline status."""

    return "online" if value == 1 else "offline"


VALUE_DESCRIPTIONS: tuple[SajR5ValueDescription, ...] = (
    SajR5ValueDescription("status", 0, _status),
    SajR5ValueDescription("total_generated_energy", 1, _scaled(100)),
    SajR5ValueDescription("total_running_time", 2, _scaled(10)),
    SajR5ValueDescription("today_generated_energy", 3, _scaled(100)),
    SajR5ValueDescription("today_running_time", 4, _scaled(10)),
    SajR5ValueDescription("pv1_voltage", 5, _scaled(10)),
    SajR5ValueDescription("pv1_current", 6, _scaled(100)),
    SajR5ValueDescription("pv2_voltage", 7, _scaled(10)),
    SajR5ValueDescription("pv2_current", 8, _scaled(100)),
    SajR5ValueDescription("pv3_voltage", 9, _scaled(10)),
    SajR5ValueDescription("pv4_current", 10, _scaled(100)),
    SajR5ValueDescription("pv1_strcurr1", 11, _scaled(100)),
    SajR5ValueDescription("pv1_strcurr2", 12, _scaled(100)),
    SajR5ValueDescription("pv1_strcurr3", 13, _scaled(100)),
    SajR5ValueDescription("pv1_strcurr4", 14, _scaled(100)),
    SajR5ValueDescription("pv2_strcurr1", 15, _scaled(100)),
    SajR5ValueDescription("pv2_strcurr2", 16, _scaled(100)),
    SajR5ValueDescription("pv2_strcurr3", 17, _scaled(100)),
    SajR5ValueDescription("pv2_strcurr4", 18, _scaled(100)),
    SajR5ValueDescription("pv3_strcurr1", 19, _scaled(100)),
    SajR5ValueDescription("pv3_strcurr2", 20, _scaled(100)),
    SajR5ValueDescription("pv3_strcurr3", 21, _scaled(100)),
    SajR5ValueDescription("pv3_strcurr4", 22, _scaled(100)),
    SajR5ValueDescription("grid_connected_power", 23, int),
    SajR5ValueDescription("grid_connected_frequency", 24, _scaled(100)),
    SajR5ValueDescription("line1_voltage", 25, _scaled(10)),
    SajR5ValueDescription("line1_current", 26, _scaled(100)),
    SajR5ValueDescription("line2_voltage", 27, _scaled(10)),
    SajR5ValueDescription("line2_current", 28, _scaled(100)),
    SajR5ValueDescription("line3_voltage", 29, _scaled(10)),
    SajR5ValueDescription("line3_current", 30, _scaled(100)),
    SajR5ValueDescription("bus_voltage", 31, _scaled(10)),
    SajR5ValueDescription("temperature", 32, _scaled(10)),
    SajR5ValueDescription("co2_reduction", 33, _scaled(10)),
    SajR5ValueDescription("running_state", 34, int),
)


def normalize_host(host: str) -> str:
    """Normalize user-provided host input into a host[:port] value."""

    host = host.strip()
    if not host:
        return host

    parsed = urlsplit(host if "://" in host else f"http://{host}")
    normalized = parsed.netloc or parsed.path.split("/", 1)[0]
    return normalized.strip().rstrip("/")


def build_status_url(host: str) -> str:
    """Build the inverter status endpoint URL."""

    return f"http://{normalize_host(host)}{ENDPOINT_PATH}"


def parse_status_payload(payload: str) -> dict[str, Any | None]:
    """Parse the comma-separated SAJ status response."""

    raw_values = [item.strip() for item in payload.strip().split(",")]
    required_length = max(description.index for description in VALUE_DESCRIPTIONS) + 1

    if len(raw_values) < required_length:
        raise SajR5InvalidResponseError(
            f"Expected at least {required_length} values, got {len(raw_values)}"
        )

    values: list[int] = []
    for item in raw_values:
        try:
            values.append(int(item))
        except ValueError as err:
            raise SajR5InvalidResponseError(
                f"Status response contains a non-integer value: {item!r}"
            ) from err

    parsed: dict[str, Any | None] = {}
    for description in VALUE_DESCRIPTIONS:
        raw_value = values[description.index]
        parsed[description.key] = (
            None
            if raw_value == UNAVAILABLE_VALUE
            else description.converter(raw_value)
        )

    return parsed


class SajR5Client:
    """Async client for a SAJ R5 inverter."""

    def __init__(
        self,
        session: ClientSession,
        host: str,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Initialize the client."""

        self._session = session
        self.host = normalize_host(host)
        self._auth = (
            BasicAuth(username, password or "")
            if username
            else None
        )

    async def async_get_status(self) -> dict[str, Any | None]:
        """Fetch and parse the inverter status."""

        try:
            async with self._session.get(
                build_status_url(self.host),
                auth=self._auth,
                timeout=10,
            ) as response:
                if response.status in (401, 403):
                    raise SajR5AuthenticationError("Invalid SAJ R5 credentials")
                response.raise_for_status()
                payload = await response.text()
        except SajR5AuthenticationError:
            raise
        except ClientResponseError as err:
            if err.status in (401, 403):
                raise SajR5AuthenticationError("Invalid SAJ R5 credentials") from err
            raise SajR5CannotConnectError(
                f"Unexpected response from inverter: {err.status}"
            ) from err
        except TimeoutError as err:
            raise SajR5CannotConnectError("Timed out connecting to inverter") from err
        except ClientError as err:
            raise SajR5CannotConnectError("Cannot connect to inverter") from err

        return parse_status_payload(payload)
