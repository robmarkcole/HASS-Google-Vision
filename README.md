# HASS-Google-Vision
Home Assistant custom component for image processing with Google Vision. Detect objects (and faces, to be added) using Google Vision. [Upload a photo to try out the processing here.](https://cloud.google.com/vision/)

## Get API key file
Follow the instructions on https://cloud.google.com/docs/authentication/getting-started to download your API key, which is a `.json` file.

## Pricing
[Read pricing](https://cloud.google.com/vision/pricing). The first 1000 calls per month are free, additional calls are charged.

## Home Assistant config
Place the `custom_components` folder in your configuration directory (or add its contents to an existing `custom_components` folder). Add to your Home-Assistant config:

```yaml
image_processing:
  - platform: google_vision
    api_key_file: /Users/robin/.homeassistant/Google_API_key.json
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