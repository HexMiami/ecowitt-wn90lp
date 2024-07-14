# ecowitt-wn90lp

The Ecowitt WN90LP is an RS485 Modbus RTU variant of the Ecowitt WS90 outdoor
weather sensor:

- [WN90LP Product Page](https://www.ecowitt.com/shop/goodsDetail/287)
- [Unofficial wiki of Ecowitt products](
  https://meshka.eu/Ecowitt/dokuwiki/doku.php?id=start)

This package provides an asyncio client using `pymodbus` to access the
registers of the WN90LP device, primarily for reading weather data. It aims to
be fairly comprehensive and specification-compliant, though is missing some
features supported by the sensor.

This package is not provided by or affiliated with Ecowitt or Fine Offset or
any related entities or brands that sell the WN90LP.

## About Us
This package is freely provided by **Hextronics** to give back to the open
source community. We produce battery-swapping drone-in-a-box hardware and
solutions to enable aerial autonomy. Consider checking out our drone stations
at <https://hextronics.com/>

We use this package to integrate a weather station into our stations so
our customers can always know when weather permits flight operations!

## Example
```py
async def main() -> None:
    client = WS90Client('/dev/ttyUSB0')
    await client.connect()
    print(await client.read_all())
    client.close()
```
> Light: 27600 lux  
> UV Index: 2.0  
> Temperature: 26.4 °C  
> Humidity: 91 %  
> Wind Speed: 0.0 m/s  
> Gust Speed: 1.0 m/s  
> Wind Direction: 213 °  
> Abs. Pressure: 101860 Pa  
> Rainfall: 0.0 mm

## Future Work
- Support measurement commands, registers 0x9C92–0x9C9A excl. 0x9C99
  - Per documentation: "9C92H~9C9AH are commands for start a measurement.
    Time for solar reading needs 113ms; temperature and wind measurement needs
    31ms before data can be read. Barometer reading needs 136ms."
  - Client methods for individual measurements.
  - Bulk measurement of all, and return a `WS90Measurement`.
- Support alternate baudrates and changing baudrate while connected.
- Support values with units and measurement uncertainty (see manual § 8).
- 0xFDFDFD recovery mode.

## Contributing
- Ensure your editor respects EditorConfig files.
- 80 character hard ruler.
- Use PEP 8 as a baseline for style.
- Always have zero Pyright errors from `poetry run pyright`.
  We may need to stub `pymodbus` eventually.
- We do not accept contributions under alternate licenses.
