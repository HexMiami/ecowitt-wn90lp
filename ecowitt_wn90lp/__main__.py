import argparse
import asyncio

from ecowitt_wn90lp.ws90 import WS90Client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ecowitt_wn90lp: read all values",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "device",
        help="path to serial device",
        default="/dev/ttyUSB0",
    )
    return parser.parse_args()


async def _main() -> None:
    args = parse_args()
    client = WS90Client(args.device)
    await client.connect()
    print(await client.read_all())
    client.close()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(_main())

