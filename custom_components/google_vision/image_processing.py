"""
Perform image processing with Google Vision
"""
import base64
import json
import logging
import time
import io
import os
from datetime import timedelta
from typing import Union, List, Set, Dict

from PIL import Image, ImageDraw

import voluptuous as vol

import gvision.core as gv

from homeassistant.util.pil import draw_box
import homeassistant.util.dt as dt_util
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import split_entity_id
import homeassistant.helpers.config_validation as cv
from homeassistant.components.image_processing import (
    PLATFORM_SCHEMA,
    ImageProcessingEntity,
    ATTR_CONFIDENCE,
    CONF_SOURCE,
    CONF_ENTITY_ID,
    CONF_NAME,
)


_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(days=365)  # Effectively disable scan.

CONF_API_KEY_FILE = "api_key_file"
CONF_SAVE_FILE_FOLDER = "save_file_folder"
CONF_TARGET = "target"
DEFAULT_TARGET = "person"
EVENT_OBJECT_DETECTED = "image_processing.object_detected"
EVENT_FILE_SAVED = "image_processing.file_saved"
FILE = "file"
OBJECT = "object"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY_FILE): cv.string,
        vol.Optional(CONF_TARGET, default=DEFAULT_TARGET): cv.string,
        vol.Optional(CONF_SAVE_FILE_FOLDER): cv.isdir,
    }
)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up platform."""

    save_file_folder = config.get(CONF_SAVE_FILE_FOLDER)
    if save_file_folder:
        save_file_folder = os.path.join(save_file_folder, "")  # If no trailing / add it

    entities = []
    for camera in config[CONF_SOURCE]:
        entities.append(
            Gvision(
                config.get(CONF_TARGET),
                config.get(CONF_API_KEY_FILE),
                config.get(ATTR_CONFIDENCE),
                save_file_folder,
                camera[CONF_ENTITY_ID],
                camera.get(CONF_NAME),
            )
        )
    add_devices(entities)


class Gvision(ImageProcessingEntity):
    """Perform object recognition with Google Vision."""

    def __init__(
        self, target, api_key_file, confidence, save_file_folder, camera_entity, name=None
    ):
        """Init with the client."""
        self._target = target
        self._api = gv.Vision(api_key_file)
        self._confidence = confidence  # the confidence threshold
        if name:  # Since name is optional.
            self._name = name
        else:
            entity_name = split_entity_id(camera_entity)[1]
            self._name = "{} {} {}".format("google vision", target, entity_name)
        self._camera_entity = camera_entity
        self._state = None  # The number of instances of interest
        self._summary = {}
        self._last_detection = None
        if save_file_folder:
            self._save_file_folder = save_file_folder

    def process_image(self, image):
        """Process an image."""
        self._state = None
        self._summary = {}

        response = self._api.object_localization(image)
        objects = response.localized_object_annotations

        if not len(objects) > 0:
            return

        self._state = len(gv.get_object_confidences(objects, self._target))
        self._summary = gv.get_objects_summary(objects)
        self.fire_object_detected_events(objects, self._confidence)

        if self._state > 0:
            self._last_detection = dt_util.now()

        if hasattr(self, "_save_file_folder") and self._state > 0:
            self.save_image(image, objects, self._target, self._save_file_folder)

    def save_image(self, image, objects, target, directory):
        """Save a timestamped image with bounding boxes around targets."""

        img = Image.open(io.BytesIO(bytearray(image))).convert("RGB")
        draw = ImageDraw.Draw(img)

        for obj in objects:
            obj_confidence = gv.format_confidence(obj.score)
            if obj_confidence > self._confidence:
                if obj.name.lower() == target and obj_confidence >= self._confidence:
                    box = gv.get_box(obj.bounding_poly.normalized_vertices)
                    draw_box(draw, box, img.width, img.height)

        latest_save_path = directory + "google_vision_latest_{}.jpg".format(target)
        img.save(latest_save_path)

    def fire_object_detected_events(self, objects, confidence_threshold):
        """Fire event if detection above confidence threshold."""

        for obj in objects:
            obj_confidence = gv.format_confidence(obj.score)
            if obj_confidence > confidence_threshold:
                self.hass.bus.fire(
                    EVENT_OBJECT_DETECTED,
                    {
                        ATTR_ENTITY_ID: self.entity_id,
                        OBJECT: obj.name.lower(),
                        ATTR_CONFIDENCE: obj_confidence,
                    },
                )

    @property
    def camera_entity(self):
        """Return camera entity id from process pictures."""
        return self._camera_entity

    @property
    def state(self):
        """Return the state of the entity."""
        return self._state

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        target = self._target
        if self._state != None and self._state > 1:
            target += "s"
        return target

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        attr = {}
        attr["target"] = self._target
        attr["summary"] = self._summary
        if self._last_detection:
            attr[
                "last_{}_detection".format(self._target)
            ] = self._last_detection.strftime("%Y-%m-%d %H:%M:%S")
        return attr
