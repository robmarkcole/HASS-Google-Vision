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
    PLATFORM_SCHEMA, ImageProcessingEntity, CONF_SOURCE, CONF_ENTITY_ID,
    CONF_NAME)


_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(days=365)  # SCAN ONCE THEN NEVER AGAIN.

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_REGION, default=DEFAULT_REGION):
        vol.In(SUPPORTED_REGIONS),
    vol.Required(CONF_ACCESS_KEY_ID): cv.string,
    vol.Required(CONF_SECRET_ACCESS_KEY): cv.string,
    vol.Optional(CONF_TARGET, default=DEFAULT_TARGET): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up platform."""

    entities = []
    for camera in config[CONF_SOURCE]:
        entities.append(Rekognition(
            client,
            config.get(CONF_REGION),
            config.get(CONF_TARGET),
            camera[CONF_ENTITY_ID],
            camera.get(CONF_NAME),
        ))
    add_devices(entities)


class Rekognition(ImageProcessingEntity):
    """Perform object and label recognition."""

    def __init__(self, client, region, target, camera_entity, name=None):
        """Init with the client."""
        self._client = client
        self._region = region
        self._target = target
        if name:  # Since name is optional.
            self._name = name
        else:
            entity_name = split_entity_id(camera_entity)[1]
            self._name = "{} {} {}".format('rekognition', target, entity_name)
        self._camera_entity = camera_entity
        self._state = None  # The number of instances of interest
        self._labels = {} # The parsed label data

    def process_image(self, image):
        """Process an image."""
        self._state = None
        self._labels = {}
        response = self._client.detect_labels(Image={'Bytes': image})
        self._state = get_label_instances(response, self._target)
        self._labels = parse_labels(response)

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
        attr = self._labels
        attr['target'] = self._target
        return attr

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name
