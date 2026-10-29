#!/usr/bin/env python3
"""Compile the existing recreation into one byte per seven-pixel column.

Only the selected constant assignments in main.py are read. Its imports, screen
setup, and event loop are never executed. No pygame or extra packages required.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONSTANTS = {
    "MATRIX_HEIGHT", "MATRIX_WIDTH", "FPS", "SCROLL_SPEED_COLS_PER_SEC",
    "PHRASE_GAP", "INTER_CHAR_BLANKS", "FONT",
}


def constant_value(node: ast.AST, values: dict[str, Any]) -> Any:
    """Evaluate only literals and the few arithmetic forms used by constants."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in values:
        return values[node.id]
    if isinstance(node, (ast.List, ast.Tuple)):
        result = [constant_value(n, values) for n in node.elts]
        return tuple(result) if isinstance(node, ast.Tuple) else result
    if isinstance(node, ast.Dict):
        return {constant_value(k, values): constant_value(v, values)
                for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -constant_value(node.operand, values)
    if isinstance(node, ast.BinOp):
        left, right = constant_value(node.left, values), constant_value(node.right, values)
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Div):
            return left / right
    raise ValueError(f"Unsupported constant expression: {ast.dump(node)}")


def read_constants(path: Path) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for statement in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name) and target.id in CONSTANTS:
                    values[target.id] = constant_value(statement.value, values)
    if missing := CONSTANTS - values.keys():
        raise ValueError(f"Missing constants in {path}: {sorted(missing)}")
    if values["MATRIX_HEIGHT"] != 7 or values["MATRIX_WIDTH"] != 35:
        raise ValueError("This hardware export requires a 35-column, 7-row display")
    if values["FPS"] <= 0 or values["SCROLL_SPEED_COLS_PER_SEC"] <= 0:
        raise ValueError("Frame rate and scroll speed must be positive")
    for char, rows in values["FONT"].items():
        if not rows or not rows[0] or len(rows) > 7:
            raise ValueError(f"Invalid glyph height/width: {char!r}")
        if any(set(row) - {"0", "1"} for row in rows):
            raise ValueError(f"Nonbinary glyph: {char!r}")
    return values


def char_columns(char: str, constants: dict[str, Any]) -> bytes:
    font = constants["FONT"]
    rows = font.get(char.lower(), font[" "])
    rows = ["0" * len(rows[0])] * (7 - len(rows)) + rows
    return bytes(sum((row[x:x + 1] == "1") << y for y, row in enumerate(rows))
                 for x in range(len(rows[0])))


def text_columns(text: str, constants: dict[str, Any]) -> bytes:
    gap = bytes(max(0, int(constants["INTER_CHAR_BLANKS"])))
    return b"".join(char_columns(char, constants) + gap for char in text)


def command_columns(command: dict[str, Any], constants: dict[str, Any]) -> bytes:
    if command["type"] == "scrolling":
        phrases = [text_columns(phrase, constants) for phrase in command.get("content", [])]
        gap = bytes(max(0, int(constants["PHRASE_GAP"])))
        return (bytes(max(0, int(command.get("start-pos", 0))))
                + gap.join(phrases)
                + bytes(max(0, int(command.get("end-gap", 0)))))
    if command["type"] == "flash":
        width = constants["MATRIX_WIDTH"]
        word = text_columns(command.get("word", ""), constants)[:width]
        full = bytearray((bytes(max(0, int(command.get("word-pos", 0)))) + word)[:width])
        full.extend(bytes(width - len(full)))
        position = command.get("punctuation_pos", -1)
        position = -1 if position is None else int(position)
        if command.get("punctuation") and 0 <= position < width:
            punctuation = text_columns(command["punctuation"], constants)
            for index, column in enumerate(punctuation[:width - position], position):
                full[index] = column  # Original helper replaces, rather than ORs.
        return bytes(full)
    raise ValueError(f"Unsupported command type: {command['type']!r}")


@dataclass(frozen=True)
class Command:
    kind: str
    offset: int
    length: int
    flash_frames: int
    next_index: int


def compile_sequence(sequence: list[dict[str, Any]], constants: dict[str, Any]) -> tuple[bytes, list[Command]]:
    if not sequence:
        raise ValueError("Cannot export an empty sequence")
    if len(sequence) > 65535:
        raise ValueError("Too many commands for uint16_t indexes")
    data = bytearray()
    commands = []
    for index, command in enumerate(sequence):
        columns = command_columns(command, constants)
        if len(columns) > 65535:
            raise ValueError(f"Command {index} is too long for uint16_t length")
        frames = max(1, int(command.get("flash-duration", 1))) if command["type"] == "flash" else 0
        if frames > 65535:
            raise ValueError(f"Command {index} flash duration exceeds uint16_t")
        # Match main.py: after the last scrolling command, restart at command 1;
        # a last flash command would instead wrap to command 0.
        next_index = index + 1
        if next_index == len(sequence):
            next_index = 1 if command["type"] == "scrolling" else 0
        if next_index >= len(sequence):
            raise ValueError("The source's repeat-at-1 behavior needs at least two commands")
        commands.append(Command(command["type"], len(data), len(columns), frames, next_index))
        data.extend(columns)
    if len(data) > 0xFFFFFFFF:
        raise ValueError("Column data exceeds uint32_t offsets")
    return bytes(data), commands


def render_header(data: bytes, commands: list[Command], constants: dict[str, Any], digest: str) -> str:
    fps = Fraction(str(constants["FPS"]))
    speed = Fraction(str(constants["SCROLL_SPEED_COLS_PER_SEC"]))
    lines = [
        "/* Generated by hardware/tools/export_sequence.py. Do not edit by hand.",
        " * Bit 0 is the top pixel; bit 6 is the bottom pixel. Bit 7 is always 0.",
        " * Data is columns per command, not a per-frame movie.",
        f" * Input SHA-256: {digest}",
        " */", "#ifndef HOUSE_RULES_GENERATED_SEQUENCE_H", "#define HOUSE_RULES_GENERATED_SEQUENCE_H",
        "#include <stdint.h>", "", "#define HR_MATRIX_WIDTH 35u", "#define HR_MATRIX_HEIGHT 7u",
        f"#define HR_FPS_NUM {fps.numerator}u", f"#define HR_FPS_DEN {fps.denominator}u",
        f"#define HR_SCROLL_COLS_NUM {speed.numerator}u", f"#define HR_SCROLL_COLS_DEN {speed.denominator}u",
        f"#define HR_COMMAND_COUNT {len(commands)}u", f"#define HR_COLUMN_BYTES {len(data)}u",
        "#define HR_INITIAL_COMMAND 0u", "#define HR_KIND_SCROLLING 0u", "#define HR_KIND_FLASH 1u", "",
        "typedef struct {", "    uint32_t offset;", "    uint16_t length;", "    uint16_t flash_frames;",
        "    uint16_t next_index;", "    uint8_t kind;", "} HouseRulesCommand;", "",
        "static const uint8_t hr_columns[HR_COLUMN_BYTES] = {",
    ]
    for start in range(0, len(data), 20):
        lines.append("    " + ", ".join(f"0x{value:02x}" for value in data[start:start + 20]) + ",")
    lines.extend(["};", "", "static const HouseRulesCommand hr_commands[HR_COMMAND_COUNT] = {"])
    for index, command in enumerate(commands):
        kind = "HR_KIND_SCROLLING" if command.kind == "scrolling" else "HR_KIND_FLASH"
        lines.append(f"    {{{command.offset}u, {command.length}u, {command.flash_frames}u, {command.next_index}u, {kind}}}, /* {index} */")
    lines.extend(["};", "", "#endif", ""])
    return "\n".join(lines)


def export(source: Path, sequence_path: Path, output: Path) -> dict[str, Any]:
    constants = read_constants(source)
    sequence = json.loads(sequence_path.read_text(encoding="utf-8"))
    data, commands = compile_sequence(sequence, constants)
    digest = hashlib.sha256(source.read_bytes() + b"\0" + sequence_path.read_bytes()).hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    (output / "generated_sequence.h").write_text(render_header(data, commands, constants, digest), encoding="utf-8")
    (output / "sequence_columns.bin").write_bytes(data)
    manifest = {
        "format_version": 1, "matrix_width": 35, "matrix_height": 7, "top_row_bit": 0,
        "fps": constants["FPS"], "scroll_columns_per_second": constants["SCROLL_SPEED_COLS_PER_SEC"],
        "initial_command": 0, "input_sha256": digest, "column_bytes": len(data),
        "commands": [command.__dict__ for command in commands],
    }
    (output / "sequence_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "main.py")
    parser.add_argument("--sequence", type=Path, default=ROOT / "sequence.json")
    parser.add_argument("--output", type=Path, default=ROOT / "hardware" / "firmware")
    args = parser.parse_args()
    manifest = export(args.source, args.sequence, args.output)
    print(f"Exported {len(manifest['commands'])} commands, {manifest['column_bytes']} column bytes to {args.output}")


if __name__ == "__main__":
    main()
