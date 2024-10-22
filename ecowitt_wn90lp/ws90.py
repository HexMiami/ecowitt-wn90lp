"""
Ecowitt WS90: WN90LP RS485 Modbus Client
Author: Corey Matyas <corey@hextronics.tech>
Copyright 2024 Hex Inc | Released under BSD-2-Clause
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Final, cast

from pymodbus.client import AsyncModbusSerialClient


WS90_DEFAULT_SLAVE_ID: Final[int] = 0x90

class WS90Client:
    def __init__(
        self,
        device: str,
        slave_id: int = WS90_DEFAULT_SLAVE_ID,
    ) -> None:
        self.client: AsyncModbusSerialClient = AsyncModbusSerialClient(
            port=device,
            baudrate=9600,
            bytesize=8,
            parity='N', # 'N'one
            stopbits=1,
            # strict=False, # TODO: works on 3.11+, not 3.9
        )
        self.slave_id: int = slave_id

    async def connect(self) -> None:
        success: bool = await self.client.connect()
        if not success:
            raise Exception("Modbus client connection failure")

    def close(self) -> None:
        if self.client.connected:
            self.client.close()

    async def _read_register(self, address: int) -> int:
        resp = await self.client.read_holding_registers(
            address=address,
            count=1,
            slave=self.slave_id,
        )
        # pymodbus annotates ModbusReponse.registers as list[Unknown]
        # don't see stubs available or an easy way to resolve this
        return cast(int, resp.registers[0]) # type: ignore

    async def _read_registers(self, address: int, count: int) -> list[int]:
        resp = await self.client.read_holding_registers(
            address=address,
            count=count,
            slave=self.slave_id,
        )
        # pymodbus annotates ModbusReponse.registers as list[Unknown]
        # don't see stubs available or an easy way to resolve this
        return cast(list[int], resp.registers) # type: ignore

    async def _write_register(self, address: int, value: int) -> None:
        await self.client.write_register(
            address=address,
            value=value,
            slave=self.slave_id,
        )

    async def read_device_name(self) -> int:
        """Should always return 0x90"""
        return await self._read_register(0x160)

    async def read_data_rate(self) -> WS90DataRate:
        return WS90DataRate(await self._read_register(0x161))

    async def write_data_rate(self, rate: WS90DataRate) -> None:
        await self._write_register(0x161, rate)

    async def read_device_address(self) -> int:
        return await self._read_register(0x162)

    async def write_device_address(self, address: int) -> None:
        assert 1 <= address and address <= 252
        await self._write_register(0x162, address)

    async def read_device_id(self) -> int:
        msb: int = await self._read_register(0x163)
        lsb: int = await self._read_register(0x164)
        return (msb << 8) + lsb

    def _process_light(self, value: int) -> int:
        if value == 0xFFFF:
            raise WS90Exception("Invalid light reading")
        assert 0 <= value and value <= 30_000
        return value * 10

    async def read_light(self) -> int:
        """
        Light value from 0 to 300,000 lux (resolution: 10 lux),
        updated every 8.75s
        """
        return self._process_light(await self._read_register(0x165))

    def _process_uv_index(self, value: int) -> float:
        if value == 0xFFFF:
            raise WS90Exception("Invalid UV index reading")
        assert 0 <= value and value <= 150
        return value / 10

    async def read_uv_index(self) -> float:
        """
        UV index from 0 to 15 (resolution: 0.1), updated every 8.75s
        """
        return self._process_uv_index(await self._read_register(0x166))

    def _process_temperature(self, value: int) -> float:
        if value == 0xFFFF:
            raise WS90Exception("Invalid temperature reading")
        assert 0 <= value and value <= 1000
        return (value - 400) / 10

    async def read_temperature(self) -> float:
        """
        Temperature from -40.0 °C to 60.0 °C (resolution: 0.1 °C),
        updated every 8.75s
        """     
        return self._process_temperature(await self._read_register(0x167))

    def _process_humidity(self, value: int) -> int:
        if value == 0xFFFF:
            raise WS90Exception("Invalid humidity reading")
        assert 1 <= value and value <= 99
        return value

    async def read_humidity(self) -> int:
        """
        Humidity from 1 - 99% (resolution: 1%), updated every 8.75s
        """
        return self._process_humidity(await self._read_register(0x168))

    def _process_wind_speed(self, value: int) -> float:
        if value == 0xFFFF:
            raise WS90Exception("Invalid wind speed reading")
        assert 0 <= value and value <= 400
        return value / 10

    async def read_wind_speed(self) -> float:
        """
        Wind speed from 0.0 - 40.0 m/s (resolution: 0.1 m/s), updated every 2s
        """
        return self._process_wind_speed(await self._read_register(0x169))

    def _process_gust_speed(self, value: int) -> float:
        if value == 0xFFFF:
            raise WS90Exception("Invalid gust speed reading")
        assert 0 <= value and value <= 400
        return value / 10

    async def read_gust_speed(self) -> float:
        """
        Gust speed from 0.0 - 40.0 m/s (resolution: 0.1 m/s), updated every 2s
        """
        return self._process_gust_speed(await self._read_register(0x16A))

    def _process_wind_direction(self, value: int) -> int:
        if value == 0xFFFF:
            raise WS90Exception("Invalid wind direction reading")
        assert 0 <= value and value <= 359
        return value

    async def read_wind_direction(self) -> int:
        """
        Wind direction from 0° - 359° (resolution: 1°), updated every 2s
        """
        return self._process_wind_direction(await self._read_register(0x16B))

    def _process_rainfall(self, value: int) -> float:
        assert 0 <= value and value <= 99999
        return value / 10

    async def read_rainfall(self) -> float:
        """
        Rainfall from 0 - 9999 mm (resolution: 0.1 mm),
        updated every 8.75s
        """
        return self._process_rainfall(await self._read_register(0x16C))

    def _process_pressure_abs(self, value: int) -> int:
        if value == 0xFFFF:
            raise WS90Exception("Invalid absolute pressure reading")
        return value * 10

    async def read_pressure_abs(self) -> int:
        """
        Absolute pressure in Pa (resolution: 10 Pa),
        updated every 8.75s
        """
        return self._process_pressure_abs(await self._read_register(0x16D))

    def _process_raincounter(self, value: int) -> float:
        return value / 100

    async def read_raincounter(self) -> float:
        """
        RainCounter amount in millimeters (resolution: 0.01mm),
        updated every 8.75s. Device documentation recommends the use of
        read_rainfall in most cases.
        """
        return self._process_raincounter(await self._read_register(0x16E))

    async def read_all(self) -> WS90Reading:
        """
        Read all most recently stored values. See WS90Reading for units and
        ranges on fields. Wind values update every 2 seconds; all other values
        update every 8.75 seconds.
        """
        values: list[int] = await self._read_registers(0x165, 0x09)
        return WS90Reading(
            light=self._process_light(values[0]),
            uv_index=self._process_uv_index(values[1]),
            temperature=self._process_temperature(values[2]),
            humidity=self._process_humidity(values[3]),
            wind_speed=self._process_wind_speed(values[4]),
            gust_speed=self._process_gust_speed(values[5]),
            wind_direction=self._process_wind_direction(values[6]),
            rainfall=self._process_rainfall(values[7]),
            pressure_abs=self._process_pressure_abs(values[8]),
        )


class WS90DataRate(IntEnum):
    BAUD_4800   = 1
    BAUD_9600   = 2
    BAUD_19200  = 3
    BAUD_115200 = 4

    def rate(self) -> int:
        return {
            self.BAUD_4800:   4800,
            self.BAUD_9600:   9600,
            self.BAUD_19200:  19200,
            self.BAUD_115200: 115200,
        }[self]


class WS90Exception(Exception):
    pass


# @dataclass(slots=True, frozen=True, kw_only=True) # TODO: Py 3.11
@dataclass(frozen=True)
class WS90Measurement:
    light: int
    """Light from 0 to 300,000 lux (resolution: 10 lux)"""

    uv_index: float
    """UV index from 0 to 15 (resolution: 0.1)"""

    temperature: float
    """Temperature from -40.0 °C to 60.0 °C (resolution: 0.1 °C)"""

    humidity: int
    """Humidity from 1 - 99% (resolution: 1%)"""

    wind_speed: float
    """Wind speed from 0.0 - 40.0 m/s (resolution: 0.1 m/s)"""

    gust_speed: float
    """Gust speed from 0.0 - 40.0 m/s (resolution: 0.1 m/s)"""

    wind_direction: int
    """Wind direction from 0° - 359° (resolution: 1°)"""

    pressure_abs: int
    """Absolute pressure in Pa (resolution: 10 Pa)"""

    def __str__(self) -> str:
        return (
            f"Light: {self.light} lux\n"
            f"UV Index: {self.uv_index}\n"
            f"Temperature: {self.temperature} °C\n"
            f"Humidity: {self.humidity} %\n"
            f"Wind Speed: {self.wind_speed} m/s\n"
            f"Gust Speed: {self.gust_speed} m/s\n"
            f"Wind Direction: {self.wind_direction} °\n"
            f"Abs. Pressure: {self.pressure_abs} Pa\n"
        )


# @dataclass(slots=True, frozen=True, kw_only=True) # TODO: Py 3.11
@dataclass(frozen=True)
class WS90Reading(WS90Measurement):
    rainfall: float
    """Rainfall from 0 - 9999 mm (resolution: 0.1 mm)"""

    def __str__(self) -> str:
        return (
            super(WS90Reading, self).__str__()
            + f"Rainfall: {self.rainfall} mm\n"
        )
