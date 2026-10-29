#!/usr/bin/env python3
"""Bundle local artwork and pin paths into one offline HTML functional viewer."""
import base64
import json
from pathlib import Path
import matrix_model as model

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def main():
    array = model.ModuleArray()
    manifest = json.loads((ROOT / "hardware/firmware/sequence_manifest.json").read_text())
    data = (ROOT / "hardware/firmware/sequence_columns.bin").read_bytes()
    original = json.loads((ROOT / "sequence.json").read_text())
    payload = {
        "manifest": manifest,
        "data": base64.b64encode(data).decode("ascii"),
        "paths": [p.__dict__ for p in array.paths],
        "labels": [" / ".join(c.get("content", [])[:2]) if c["type"] == "scrolling"
                   else c.get("word", "") + c.get("punctuation", "") for c in original],
    }
    template = (HERE / "viewer-template.html").read_text()
    rendered = template.replace("/*__MODEL_DATA__*/", json.dumps(payload).replace("</", "<\\/"))
    (HERE / "matrix-emulator.html").write_text(rendered)
    print("Wrote offline matrix-emulator.html: 245 physical diode paths, 39 commands.")


if __name__ == "__main__":
    main()
