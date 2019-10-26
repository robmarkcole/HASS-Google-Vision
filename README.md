# HASS-Google-Vision
[Home Assistant](https://www.home-assistant.io/) custom component for image processing with Google Vision. 

Detect objects in camera feeds using Google Vision. [Upload a photo to try out the processing here.](https://cloud.google.com/vision/)(see the `Objects` tab). Trigger the image processing by calling the `image_processing.scan` service (note default scanning is disabled to prevent unintentionally racking up bills). The component adds an image_processing entity where the state of the entity is the total number of `target` objects that are above a confidence threshold which has a default value of 80%. The time of the last detection of the target object is in the `last_detection` attribute. The type and number of objects (of any confidence) is listed in the `summary` attribute. If `save_file_folder` is configured, on each new detection of the target an annotated image with the name `google_vision_latest_{target}.jpg` is saved if it doesnt already exist, and over-written if it does exist. This image shows the bounding box around detected targets and can be displayed on the Home Assistant front end using a local_file camera (see later in this readme). Use the [foler_watcher](https://www.home-assistant.io/integrations/folder_watcher/) to detect when this file has changed if you want to include it in notifications. An event `image_processing.object_detected` is fired for each object detected and can be used to track multiple object types, for example incrementing a [counter](https://www.home-assistant.io/integrations/counter/), or kicking off an automation.

<p align="center">
<img src="https://github.com/robmarkcole/HASS-Google-Vision/blob/master/development/usage.png" width="500">
</p>

<p align="center">
<img src="https://github.com/robmarkcole/HASS-Google-Vision/blob/master/development/detail.png" width="400">
</p>

## Google Vision API key file & API Pricing
Follow the instructions on https://cloud.google.com/docs/authentication/getting-started to download your API key, which is a `.json` file. Place the file in your Home Assistant config folder.

[Read pricing](https://cloud.google.com/vision/pricing). The first 1000 calls per month are free, additional calls are charged. Be sure that you understand how the image processing scan_interval works, or risk running up bills.

## Home Assistant config
Place the `custom_components` folder in your configuration directory (or add its contents to an existing `custom_components` folder). Add to your Home-Assistant config:

```yaml
image_processing:
  - platform: google_vision
    api_key_file: /config/Google_API_key.json
    source:
      - entity_id: camera.local_file
```

Configuration variables:
- **api_key_file**: the path to your API key file.
- **target**: (optional) The target object class, default `person`.
- **save_file_folder**: (Optional) The folder to save processed images to. Note that folder path should be added to [whitelist_external_dirs](https://www.home-assistant.io/docs/configuration/basic/)
- **confidence**: (Optional) The confidence (in %) above which detected targets are counted in the sensor state. Default value: 80
- **name**: (Optional) A custom name for the the entity.
- **source**: Must be a camera.

## Displaying the `google_vision_latest_{target}.jpg` file
It easy to display the google_vision_latest_{target}.jpg image with a [local_file](https://www.home-assistant.io/integrations/local_file) camera. An example configuration is:

```
camera:
  - platform: local_file
    file_path: /config/www/google_vision/google_vision_latest_person.jpg
    name: google_vision_latest_person
```

## Automation to send the `google_vision_latest_{target}.jpg` file in a notification
Configure the [folder_watcher](https://www.home-assistant.io/integrations/folder_watcher/) in `configuration.yaml`, e.g.:

```yaml
folder_watcher:
  - folder: /config/www
```
Then in `automations.yaml` we will send a photo when `google_vision_latest_{target}.jpg` is modified:

```yaml
- id: '1527837198169'
  alias: New detection
  trigger:
    platform: event
    event_type: folder_watcher
    event_data:
      file : google_vision_latest_person.jpg
  action:
    service: telegram_bot.send_photo
    data:
      file: /config/www/google_vision_images/google_vision_latest_person.jpg
```

#### Event `image_processing.object_detected`
An event `image_processing.object_detected` is fired for each object detected above the configured `confidence` threshold. This is the recommended way to check the confidence of detections, and to keep track of objects that are not configured as the `target` (configure logger level to `debug` to observe events in the Home Assistant logs). An example use case for event is to get an alert when some rarely appearing object is detected, or to increment a [counter](https://www.home-assistant.io/components/counter/). The `image_processing.object_detected` event payload includes:

- `entity_id` : the entity id responsible for the event
- `object` : the object detected
- `confidence` : the confidence in detection in the range 0 - 1 where 1 is 100% confidence.

An example automation using the `image_processing.object_detected` event is given below:

```yaml
- action:
  - data_template:
      title: "New object detection"
      message: "{{ trigger.event.data.object }} with confidence {{ trigger.event.data.confidence }}"
    service: telegram_bot.send_message
  alias: Object detection automation
  condition: []
  id: '1120092824622'
  trigger:
  - platform: event
    event_type: image_processing.object_detected
    event_data:
      object: person
```