"""Platform for light integration."""
# https://github.com/home-assistant/example-custom-config/tree/master/custom_components/example_light
# https://developers.home-assistant.io/docs/core/entity/light/
# https://storage-asset.msi.com/files/pdf/Mystic_Light_Software_Development_Kit.pdf

from __future__ import annotations

import logging

import voluptuous as vol
import requests
import json
import math

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (ATTR_BRIGHTNESS, PLATFORM_SCHEMA, ATTR_RGB_COLOR, ATTR_EFFECT,
                                            LightEntity, LightEntityFeature, ColorMode)
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string
})

BRIGHTNESS_SCALE = (1, 5)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the Awesome Light platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    host = config[CONF_HOST]

    url = f"http://{host}:5001/mystic_light"

    payload = {
        "query": """query GetDevices {
            devices {
                name
                leds {
                    name
                    state {
                        color {
                            red
                            green
                            blue
                        }
                        bright
                        speed
                        style
                    }
                }
            }
        }""",
        "variables": {}
    }
    headers = {'Content-Type': 'application/json'}

    response = requests.request("POST", url, headers=headers, data=json.dumps(payload))

    if response and response.status_code == 200 and response.text:
        devices = response.json().get('data', {}).get('devices', [])
        devices_count = len(devices)
        _LOGGER.info(f"{devices_count} Mystic Light device(s) found")
        for device in devices:
            leds = device.get('leds',[])
            leds_count = len(leds)
            device_name = device.get('name', 'Uknown Name')
            _LOGGER.info(f"{leds_count} LED(s) found for Mystic Light device {device_name}")
            add_entities(MysticLight(led, host, device_name) for led in leds)
    else:
        _LOGGER.error(f"Could not connect to {url}, {response.status_code}: {response.text}")
        return



class MysticLight(LightEntity):

    def updateLightStatus(self, host, device_name, led_name, style, red, green, blue, brightness):
        _LOGGER.debug(f"Changing light status for {device_name}:{led_name} to effect {style}, brightness {brightness}, color ({red}, {green}, {blue})")

        url = f"http://{host}:5001/mystic_light"

        payload = {
            "query": """mutation SetStateForSingleLed($device_name: String!, $led_name: String!, $state: DeviceLedStateInput!) {
                devices(filter: { names: [$device_name] }) {
                    leds(filter: { names: [$led_name] }) {
                        setState(state: $state)
                    }
                }
            }""",
            "variables": {
                "device_name": device_name,
                "led_name": led_name,
                "state": {
                    **({"style": style} if style is not None else {}),
                    **({"color": {"red": red, "green": green, "blue": blue}} if (red, green, blue) != (None, None, None) else {}),
                    **({"bright": brightness} if brightness is not None else {})
                }
            }
        }

        headers = {'Content-Type': 'application/json'}

        _LOGGER.debug(f"... {json.dumps(payload)}")

        response = requests.request("POST", url, headers=headers, data=json.dumps(payload))

        if response and response.status_code == 200 and response.text:
            _LOGGER.debug(f"... {response.text}")
            return True
        else:
            _LOGGER.error(f"Could not connect to {url}, {response.status_code}: {response.text}")
            return False

    def __init__(self, light, host, device_name) -> None:
        """Initialize an MysticLight."""
        _LOGGER.debug(light)
        self._light = light
        self._name = device_name + ' ' + light.get('name')
        self._attr_unique_id = 'mystic_light_' + device_name + '_' + light.get('name')
        self._state = None
        self._brightness = light.get('state').get('bright') * 50 # values from 1 to 5
        self._host = host
        self._device_name = device_name
        self._led_name = light.get('name')
        self._attr_supported_color_modes = {ColorMode.BRIGHTNESS, ColorMode.RGB}
        self._attr_color_mode = ColorMode.BRIGHTNESS
        self._attr_supported_features |= LightEntityFeature.EFFECT
        self._effect = None
        self._color = None

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    @property
    def brightness(self):
        """Return the brightness of the light.

        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._brightness

    # @property
    # def color_mode(self):
    #     return ColorMode.BRIGHTNESS

    # def supported_color_modes(self):
    #     return self._attr_supported_color_modes

    @property
    def effect_list(self) -> list[str]:
        return ["NoAnimation", "Lightning", "JCORSAIR_ColorWave", "Energy", "ColorRing", "Flame", "JCORSAIR_Clock", "JCORSAIR_ColorShift", "Direct Lighting Control", "Stack", "MusicConcert", "DoubleMeteor", "MusicMusic", "RainbowDoubleflashing", "Direct All Sync", "Flashing", "MusicRecreation", "Weather", "JCORSAIR_Visor", "JCORSAIR_ColorPulse", "CPUTemp", "Planetary", "Meteor", "Rainbow", "Breathing"]


    @property
    def effect(self) -> str | None:
        """Return the current effect."""
        return self._effect


    @property
    def rgb_color(self):
        """Return value for rgb."""
        return self._color

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self._state

    def turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        host = self._host
        device_name = self._device_name
        led_name = self._led_name

        effect = kwargs.get(ATTR_EFFECT)
        if effect is None:
            effect = 'NoAnimation'

        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is not None:
            brightness = math.ceil(brightness / 50)

        rgb = kwargs.get(ATTR_RGB_COLOR)
        color_r = 255
        color_g = 0
        color_b = 0
        if rgb is not None:
            # effect = 'NoAnimation'
            color_r = rgb[0]
            color_g = rgb[1]
            color_b = rgb[2]

        self.updateLightStatus(host, device_name, led_name, effect, color_r, color_g, color_b, brightness)


    def turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        host = self._host
        device_name = self._device_name
        led_name = self._led_name

        self.updateLightStatus(host, device_name, led_name, "NoAnimation", 0, 0, 0, None)


    def update(self) -> None:
        """Fetch new state data for this light.

        This is the only method that should fetch new data for Home Assistant.
        """
        host = self._host
        device_name = self._device_name
        led_name = self._led_name

        _LOGGER.debug(f"Starting state update for {device_name}:{led_name}")

        url = f"http://{host}:5001/mystic_light"

        payload = {
            "query": """query GetDevices($device_name: String!, $led_name: String!) {
                devices(filter: { names: [$device_name] }) {
                    name
                    leds(filter: { names: [$led_name] }) {
                        name
                        state {
                            color {
                                red
                                green
                                blue
                            }
                            bright
                            speed
                            style
                        }
                    }
                }
            }""",
            "variables": {
                "device_name": device_name,
                "led_name": led_name
            }
        }
        headers = {'Content-Type': 'application/json'}

        response = requests.request("POST", url, headers=headers, data=json.dumps(payload))

        if response and response.status_code == 200 and response.text:
            devices = response.json().get('data', {}).get('devices', [])
            for device in devices: # graphql above already filters by device name and led name
                if device_name == device.get('name'):
                    for led in device.get('leds', []):
                        if led_name == led.get('name'):
                            _LOGGER.debug(f"... led {device_name}:{led_name} found for update: {led}")
                            led_state = led.get('state')
                            led_color = led_state.get('color')
                            led_color_r = led_color.get('red')
                            led_color_g = led_color.get('green')
                            led_color_b = led_color.get('blue')
                            led_style = led_state.get('style')

                            self._color = (led_color_r, led_color_g, led_color_b)

                            if led_style == 'NoAnimation' and led_color_r == 0 and led_color_g == 0 and led_color_b == 0:
                                self._state = False
                            else:
                                self._state = True

                            led_brightness = led_state.get('bright')
                            self._brightness = led_brightness * 50

                            self._effect = led_state.get('style')


        else:
            _LOGGER.error(f"... Could not get status from {url}, {response.status_code}: {response.text}")
            return


