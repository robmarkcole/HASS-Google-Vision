# HASS-Google-Vision
Home Assistant custom component for image processing with Google Vision. Detect objects (and faces, to be added) using Google Vision. [Upload a photo to try out the processing here.](https://cloud.google.com/vision/)

## Get API key file
Follow the instructions on https://cloud.google.com/docs/authentication/getting-started to download your API key, which is a `.json` file.

## Pricing
Read pricing. The first 1000 calls are free, 0.225 cent per call after that.

## Home Assistant config
Place the `custom_components` folder in your configuration directory (or add its contents to an existing `custom_components` folder). Add to your Home-Assistant config:

```yaml
image_processing:
  - platform: google_vision
    source:
      - entity_id: camera.local_file
```