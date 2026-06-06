"""Data update coordinator for the SAJ R5 integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    SajR5AuthenticationError,
    SajR5CannotConnectError,
    SajR5Client,
    SajR5InvalidResponseError,
)
from .const import CONF_POLLING_TIME, DEFAULT_POLLING_TIME, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SajR5Coordinator(DataUpdateCoordinator[dict[str, Any | None]]):
    """Coordinate SAJ R5 inverter polling."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: SajR5Client,
    ) -> None:
        """Initialize the coordinator."""

        self.client = client
        polling_time = entry.data.get(CONF_POLLING_TIME, DEFAULT_POLLING_TIME)

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=polling_time),
            always_update=False,
        )

    async def _async_update_data(self) -> dict[str, Any | None]:
        """Fetch data from the inverter."""

        try:
            return await self.client.async_get_status()
        except SajR5AuthenticationError as err:
            raise ConfigEntryAuthFailed("Invalid SAJ R5 credentials") from err
        except (SajR5CannotConnectError, SajR5InvalidResponseError) as err:
            raise UpdateFailed(str(err)) from err
