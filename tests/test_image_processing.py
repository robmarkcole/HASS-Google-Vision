"""The tests for the Google vision platform."""
from unittest.mock import Mock

import pytest

from homeassistant.core import callback
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_NAME,
    CONF_FRIENDLY_NAME,
    STATE_UNKNOWN,
)
from homeassistant.setup import async_setup_component
import homeassistant.components.image_processing as ip
import homeassistant.components.google_vision.image_processing as gvip


VALID_ENTITY_ID = "image_processing.google_vision_person_demo_camera"
VALID_CONFIG = {
    ip.DOMAIN: {
        "platform": "google_vision",
        gvip.CONF_API_KEY_FILE: "dummy_api_key.json",
        ip.CONF_SOURCE: {ip.CONF_ENTITY_ID: "camera.demo_camera"},
    },
    "camera": {"platform": "demo"},
}


async def test_setup_platform(hass):
    """Set up platform with one entity."""
    await async_setup_component(hass, ip.DOMAIN, VALID_CONFIG)
    assert hass.states.get(VALID_ENTITY_ID)
