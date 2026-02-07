import argparse
import asyncio
import json


# from ixhardware import get_chassis_hardware, parse_dmi

from .installer import Installer
from .installer_menu import InstallerMenu


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", action="store_true")

    args = parser.parse_args()

    vendor  = "OneNAS"
    version = "260207"
    try:
        with open("/.data/.version") as f:
            version = f.read().strip()

        with open("/.data/.vendor") as f:
            vendor = json.loads(f.read()).get("name", "OneNAS")
    except Exception:
        pass

    # dmi = parse_dmi()
    # tn_model = get_chassis_hardware(dmi)

    installer = Installer(version, None, vendor, None)

    if args.doc:
        print(
            "API documentation generation has been removed along with server functionality."
        )

    else:
        loop = asyncio.get_event_loop()
        loop.create_task(InstallerMenu(installer).run())
        loop.run_forever()


if __name__ == "__main__":
    main()
