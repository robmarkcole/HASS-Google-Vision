"""
Perform image pgoressing with Google Vision
"""
import base64
import json
import logging
import time
import io
from datetime import timedelta
from typing import Union, List, Set, Dict

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


def format_confidence(confidence: Union[str, float]) -> float:
    """Takes a confidence from the API like 
       0.55623 and returne 55.6 (%).
    """
    return round(float(confidence) * 100, 1)


def get_objects(objects: List[types.LocalizedObjectAnnotation]) -> List[str]:
    """
    Get a list of the unique objects predicted.
    """
    labels = [obj.name.lower() for obj in objects]
    return list(set(labels))


def get_object_confidences(objects: List[types.LocalizedObjectAnnotation], target: str):
    """
    Return the list of confidences of instances of target label.
    """
    confidences = [
        format_confidence(obj.score) for obj in objects if obj.name.lower() == target
    ]
    return confidences


def get_objects_summary(objects: List[types.LocalizedObjectAnnotation]):
    """
    Get a summary of the objects detected.
    """
    objects_labels = get_objects(objects)
    return {
        target: len(get_object_confidences(objects, target))
        for target in objects_labels
    }


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
    """Perform object recognition with Google Vision."""

    def __init__(self, target, client, camera_entity, name=None):
        """Init with the client."""
        self._target = target
        self._client = client
        if name:  # Since name is optional.
            self._name = name
        else:
            entity_name = split_entity_id(camera_entity)[1]
            self._name = "{} {} {}".format("google vision", target, entity_name)
        self._camera_entity = camera_entity
        self._state = None  # The number of instances of interest
        self._summary = {}

    def process_image(self, image):
        """Process an image."""
        self._state = None
        self._summary = {}

        response = self._client.object_localization(image=types.Image(content=image))
        objects = response.localized_object_annotations

        self._state = len(get_object_confidences(objects, self._target))
        self._summary = get_objects_summary(objects)

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
        attr["summary"] = self._summary
        return attr

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name
