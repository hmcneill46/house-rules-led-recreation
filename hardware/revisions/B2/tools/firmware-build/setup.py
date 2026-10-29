#!/usr/bin/env python3
"""Install the pinned official Arduino-Pico core in B2's private cache."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

CORE = "6.3.1"
INDEX = "https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json"
CORE_SHA256 = "6fa7a30671d3b08f77be41b92079fd83b0b98c375ff4f4a46d01132b69024485"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", type=Path, default=Path.home()/".cache/house-rules-arduino/bin/arduino-cli")
    ap.add_argument("--cache", type=Path, default=Path.home()/".cache/house-rules-b2-arduino")
    args = ap.parse_args()
    if not args.cli.is_file():
        raise SystemExit("Provide the existing pinned Arduino CLI 1.5.1 with --cli.")
    version = json.loads(subprocess.check_output([str(args.cli), "version", "--format", "json"], text=True))
    if version.get("VersionString") != "1.5.1":
        raise SystemExit("B2 requires Arduino CLI 1.5.1.")
    args.cache.mkdir(parents=True, exist_ok=True)
    config = args.cache/"arduino-cli.yaml"
    config.write_text(json.dumps({"board_manager": {"additional_urls": [INDEX]},
        "directories": {"data": str(args.cache/"data"), "downloads": str(args.cache/"downloads"),
                        "user": str(args.cache/"user")}}, indent=2)+"\n")
    def run(*command):
        subprocess.run([str(args.cli), *command, "--config-file", str(config)], check=True)
    run("core", "update-index")
    # Arduino CLI verifies package/tool checksums from the official release index.
    run("core", "install", "rp2040:rp2040@"+CORE)
    archive=args.cache/"downloads/packages"/("rp2040-"+CORE+".zip")
    if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest()!=CORE_SHA256:
        raise SystemExit("Pinned Arduino-Pico archive SHA-256 verification failed.")
    print("Pinned Arduino-Pico", CORE, "installed in", args.cache)
    print("Expected core archive SHA-256:", CORE_SHA256)


if __name__ == "__main__":
    main()
