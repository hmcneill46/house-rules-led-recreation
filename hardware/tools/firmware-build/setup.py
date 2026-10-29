#!/usr/bin/env python3
"""Install pinned free build tools into a task-specific cache on Intel macOS."""
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import tarfile

if platform.system() != "Darwin" or platform.machine() != "x86_64":
    raise SystemExit("This installer is pinned to the verified Intel macOS archive. Install Arduino CLI1.5.1 for your host manually, then pass --cli/--config to build.py.")
cache = Path.home() / ".cache/house-rules-arduino"
(cache / "bin").mkdir(parents=True, exist_ok=True)
(cache / "downloads").mkdir(exist_ok=True)
archive = cache / "downloads/arduino-cli.tar.gz"
expected = "c982e940027996bea9901050e95fae99c59c1dcfee54beedecaf28141e7bf2e7"
if not archive.exists():
    subprocess.run(["curl", "-L", "--fail", "--silent", "--show-error",
                    "https://downloads.arduino.cc/arduino-cli/arduino-cli_1.5.1_macOS_64bit.tar.gz",
                    "-o", str(archive)], check=True)
if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
    raise SystemExit("Arduino CLI archive SHA-256 differs from the pinned archive; refusing to execute it.")
cli = cache / "bin/arduino-cli"
with tarfile.open(archive) as tar:
    cli.write_bytes(tar.extractfile("arduino-cli").read())
cli.chmod(0o755)
config = cache / "arduino-cli.yaml"
config.write_text("board_manager:\n  additional_urls:\n    - https://github.com/stm32duino/BoardManagerFiles/raw/main/package_stmicroelectronics_index.json\n"
                  + "directories:\n"
                  + "\n".join(f"  {key}: {json.dumps(str(cache / value))}" for key, value in
                              [("data", "data"), ("downloads", "downloads"), ("user", "user")])
                  + "\nupdater:\n  enable_notification: false\n")
for args in [["core", "update-index"], ["core", "install", "STMicroelectronics:stm32@3.0.0"]]:
    subprocess.run([str(cli), *args, "--config-file", str(config)], check=True)
print("Pinned build tools ready in", cache)
