# MSI Mystic Light integration
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs) [![stability-alpha](https://img.shields.io/badge/stability-alpha-f4d03f.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#alpha)

## Prerequisites

To use this component, you must install the [Mystic Light Server](https://github.com/and7ey/mystic_light_ha_app) on your Windows PC.

## Limitations

Please note the following restrictions:

1. Not all devices are returned by the server application.
2. The effects list is hardcoded, which means some effects may not be supported by your specific hardware.
3. When turning on the lights, they will restore to default settings (Rainbow effect with red color).

## Troubleshooting

To gain more insight into potential issues, enable component logging:
logger:
```
  default: warning
  logs:
    custom_components.mystic_light: debug
```
This configuration will provide more detailed information about what's happening during component operation.

