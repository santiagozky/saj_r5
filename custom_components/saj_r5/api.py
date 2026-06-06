"""Client and parser for SAJ R5 inverter status data."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import re
from typing import Any
from urllib.parse import urlsplit

from aiohttp import BasicAuth, ClientError, ClientResponseError, ClientSession

from .const import INFO_ENDPOINT_PATH, STATUS_ENDPOINT_PATH, WIFI_ENDPOINT_PATH

UNAVAILABLE_VALUE = 65535
INFO_SERIAL_NUMBER_INDEX = 0
WIFI_IP_ADDRESS_INDEX = 7
WIFI_MAC_ADDRESS_INDEX = 13

RUNNING_STATES = {
    0: "not_connected",
    1: "waiting",
    2: "normal",
    3: "error",
    4: "upgrading",
}


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


@dataclass(frozen=True)
class SajR5DeviceDetails:
    """Device details returned by the inverter metadata endpoints."""

    serial_number: str | None = None
    ip_address: str | None = None
    mac_address: str | None = None

    @property
    def is_complete(self) -> bool:
        """Return true if all expected device details are present."""

        return bool(self.serial_number and self.ip_address and self.mac_address)

    @property
    def has_any_value(self) -> bool:
        """Return true if any device detail is present."""

        return bool(self.serial_number or self.ip_address or self.mac_address)

    def merged(self, other: SajR5DeviceDetails) -> SajR5DeviceDetails:
        """Return a copy with non-empty values from another details object."""

        return SajR5DeviceDetails(
            serial_number=other.serial_number or self.serial_number,
            ip_address=other.ip_address or self.ip_address,
            mac_address=other.mac_address or self.mac_address,
        )


def _scaled(divisor: int | float) -> Callable[[int], float]:
    """Return a converter that scales a raw integer value."""

    return lambda value: value / divisor


def _status(value: int) -> str:
    """Convert the raw online/offline status."""

    return "online" if value == 1 else "offline"


def _running_state(value: int) -> str:
    """Convert the raw running state value."""

    return RUNNING_STATES.get(value, f"unknown_{value}")


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
    SajR5ValueDescription("output_power", 23, int),
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
    SajR5ValueDescription("running_state", 34, _running_state),
)


def normalize_host(host: str) -> str:
    """Normalize user-provided host input into a host[:port] value."""

    host = host.strip()
    if not host:
        return host

    parsed = urlsplit(host if "://" in host else f"http://{host}")
    normalized = parsed.netloc or parsed.path.split("/", 1)[0]
    return normalized.strip().rstrip("/")


def build_endpoint_url(host: str, path: str) -> str:
    """Build an inverter endpoint URL."""

    return f"http://{normalize_host(host)}{path}"


def build_status_url(host: str) -> str:
    """Build the inverter status endpoint URL."""

    return build_endpoint_url(host, STATUS_ENDPOINT_PATH)


def _parse_csv_payload(
    payload: str,
    required_length: int,
    source: str,
) -> list[str]:
    """Parse a comma-separated inverter response."""

    raw_values = [item.strip() for item in payload.strip().split(",")]

    if len(raw_values) < required_length:
        raise SajR5InvalidResponseError(
            f"{source} response expected at least {required_length} values, "
            f"got {len(raw_values)}"
        )

    return raw_values


def parse_status_payload(payload: str) -> dict[str, Any | None]:
    """Parse the comma-separated SAJ status response."""

    required_length = max(description.index for description in VALUE_DESCRIPTIONS) + 1
    raw_values = _parse_csv_payload(payload, required_length, "Status")

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


def _clean_optional_value(value: str) -> str | None:
    """Return a stripped string value, or None if it is blank."""

    value = value.strip().strip("'\"")
    return value or None


def _normalize_mac_address(mac_address: str | None) -> str | None:
    """Normalize a MAC address for the Home Assistant device registry."""

    if mac_address is None:
        return None

    mac_address = mac_address.strip().lower().replace("-", ":")
    compact_mac = mac_address.replace(":", "")
    if re.fullmatch(r"[0-9a-f]{12}", compact_mac):
        return ":".join(
            compact_mac[index : index + 2] for index in range(0, 12, 2)
        )

    return mac_address or None


def parse_wifi_payload(payload: str) -> SajR5DeviceDetails:
    """Parse device network details from wifi.php."""

    raw_values = _parse_csv_payload(
        payload,
        WIFI_MAC_ADDRESS_INDEX + 1,
        "Wi-Fi",
    )
    return SajR5DeviceDetails(
        ip_address=_clean_optional_value(raw_values[WIFI_IP_ADDRESS_INDEX]),
        mac_address=_normalize_mac_address(
            _clean_optional_value(raw_values[WIFI_MAC_ADDRESS_INDEX])
        ),
    )


def parse_info_payload(payload: str) -> SajR5DeviceDetails:
    """Parse device details from info.php."""

    raw_values = _parse_csv_payload(
        payload,
        INFO_SERIAL_NUMBER_INDEX + 1,
        "Info",
    )
    return SajR5DeviceDetails(
        serial_number=_clean_optional_value(raw_values[INFO_SERIAL_NUMBER_INDEX]),
    )


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
        self._auth = BasicAuth(username, password or "") if username else None

    async def _async_get_endpoint(self, path: str) -> str:
        """Fetch an inverter endpoint."""

        try:
            async with self._session.get(
                build_endpoint_url(self.host, path),
                auth=self._auth,
                timeout=10,
            ) as response:
                if response.status in (401, 403):
                    raise SajR5AuthenticationError("Invalid SAJ R5 credentials")
                response.raise_for_status()
                return await response.text()
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

    async def async_get_status(self) -> dict[str, Any | None]:
        """Fetch and parse the inverter status."""

        try:
            payload = await self._async_get_endpoint(STATUS_ENDPOINT_PATH)
        except SajR5Error:
            raise

        return parse_status_payload(payload)

    async def async_get_device_details(self) -> SajR5DeviceDetails:
        """Fetch and parse inverter device details."""

        details = SajR5DeviceDetails()
        errors: list[SajR5Error] = []

        try:
            info_payload = await self._async_get_endpoint(INFO_ENDPOINT_PATH)
        except SajR5Error as err:
            errors.append(err)
        else:
            details = details.merged(parse_info_payload(info_payload))

        try:
            wifi_payload = await self._async_get_endpoint(WIFI_ENDPOINT_PATH)
        except SajR5Error as err:
            errors.append(err)
        else:
            details = details.merged(parse_wifi_payload(wifi_payload))

        if not details.has_any_value and errors:
            raise errors[0]

        return details
