"""
Perform image pgoressing with Google Vision
"""
import base64
import json
import logging
import time
import io
from datetime import timedelta

import voluptuous as vol

from google.cloud import vision
from google.cloud.vision import types
from google.oauth2 import service_account

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

CONF_API_KEY_FILE = "api_key_file"
CONF_SAVE_FILE_FOLDER = "save_file_folder"
CONF_TARGET = "target"
DEFAULT_TARGET = "person"
EVENT_OBJECT_DETECTED = "image_processing.object_detected"
EVENT_FILE_SAVED = "image_processing.file_saved"

IMG_FILE = "/Users/robin/.homeassistant/www/images/test-image3.jpg"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY_FILE): cv.string,
        vol.Optional(CONF_TARGET, default=DEFAULT_TARGET): cv.string,
        vol.Optional(CONF_SAVE_FILE_FOLDER): cv.isdir,
    }
)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up platform."""

    # Instantiates a client
    credentials = service_account.Credentials.from_service_account_file(
        config.get(CONF_API_KEY_FILE)
    )
    scoped_credentials = credentials.with_scopes(
        ["https://www.googleapis.com/auth/cloud-platform"]
    )
    client = vision.ImageAnnotatorClient(credentials=scoped_credentials)

    entities = []
    for camera in config[CONF_SOURCE]:
        entities.append(
            Gvision(
                config.get(CONF_TARGET),
                client,
                camera[CONF_ENTITY_ID],
                camera.get(CONF_NAME),
            )
        )
    add_devices(entities)


class Gvision(ImageProcessingEntity):
    """Perform object recognition."""

    def __init__(self, target, client, camera_entity, name=None):
        """Init with the client."""
        self._target = target
        self._client = client
        if name:  # Since name is optional.
            self._name = name
        else:
            entity_name = split_entity_id(camera_entity)[1]
            self._name = "{} {} {}".format("google_vision", target, entity_name)
        self._camera_entity = camera_entity
        self._state = None  # The number of instances of interest

    def process_image(self, image):
        """Process an image."""
        # Loads the image into memory
        with io.open(IMG_FILE, "rb") as image_file:
            content = image_file.read()
        image = types.Image(content=content)
        response = self._client.object_localization(image=image)
        objects = response.localized_object_annotations
        _LOGGER.error("Gvision : %s", objects)
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
