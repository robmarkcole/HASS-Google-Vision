"""
Perform image pgoressing with Google Vision
"""
import base64
import json
import logging
import time
from datetime import timedelta

import voluptuous as vol

from homeassistant.core import split_entity_id
import homeassistant.helpers.config_validation as cv
from homeassistant.components.image_processing import (
    PLATFORM_SCHEMA,
    ImageProcessingEntity,
    CONF_SOURCE,
    CONF_ENTITY_ID,
    CONF_NAME,
)


_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(days=365)  # SCAN ONCE THEN NEVER AGAIN.

CONF_SAVE_FILE_FOLDER = "save_file_folder"
CONF_TARGET = "target"
DEFAULT_TARGET = "person"
EVENT_OBJECT_DETECTED = "image_processing.object_detected"
EVENT_FILE_SAVED = "image_processing.file_saved"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_TARGET, default=DEFAULT_TARGET): cv.string,
        vol.Optional(CONF_SAVE_FILE_FOLDER): cv.isdir,
    }
)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up platform."""

    entities = []
    for camera in config[CONF_SOURCE]:
        entities.append(
            Gvision(
                config.get(CONF_TARGET), camera[CONF_ENTITY_ID], camera.get(CONF_NAME)
            )
        )
    add_devices(entities)


class Gvision(ImageProcessingEntity):
    """Perform object recognition."""

    def __init__(self, target, camera_entity, name=None):
        """Init with the client."""
        self._target = target
        if name:  # Since name is optional.
            self._name = name
        else:
            entity_name = split_entity_id(camera_entity)[1]
            self._name = "{} {} {}".format("google_vision", target, entity_name)
        self._camera_entity = camera_entity
        self._state = None  # The number of instances of interest

    def process_image(self, image):
        """Process an image."""
        self._state = None

    @property
    def camera_entity(self):
        """Return camera entity id from process pictures."""
        return self._camera_entity

    @property
    def state(self):
        """Return the state of the entity."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        attr = {}
        attr["target"] = self._target
        return attr

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name
