"""Compare the export with original helpers, without importing the GUI program."""
import ast
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("export_sequence", ROOT / "hardware/tools/export_sequence.py")
exporter = importlib.util.module_from_spec(SPEC)
# dataclasses looks up its defining module.
import sys
sys.modules[SPEC.name] = exporter
SPEC.loader.exec_module(exporter)


class ExportSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.constants = exporter.read_constants(ROOT / "main.py")
        cls.sequence = json.loads((ROOT / "sequence.json").read_text())
        # These are the original repository functions, compiled in isolation.
        helpers = {"char_to_columns", "text_to_columns", "build_scrolling_buffer_for_cmd",
                   "build_flash_columns", "get_visible_columns_from_buffer"}
        tree = ast.parse((ROOT / "main.py").read_text())
        isolated = ast.Module(body=[node for node in tree.body
                                    if isinstance(node, ast.FunctionDef) and node.name in helpers],
                              type_ignores=[])
        cls.original = dict(cls.constants)
        exec(compile(isolated, "original_helpers", "exec"), cls.original)

    @staticmethod
    def pack(columns):
        return bytes(sum(bit << row for row, bit in enumerate(column)) for column in columns)

    def test_every_glyph_matches_original(self):
        for char in list(self.constants["FONT"]) + ["A", "@"]:
            with self.subTest(char=char):
                self.assertEqual(exporter.char_columns(char, self.constants),
                                 self.pack(self.original["char_to_columns"](char)))

    def test_every_command_and_pixel_matches_original(self):
        for index, command in enumerate(self.sequence):
            with self.subTest(index=index):
                if command["type"] == "scrolling":
                    expected = self.original["build_scrolling_buffer_for_cmd"](command)
                else:
                    expected = self.original["build_flash_columns"](
                        command.get("word", ""), command.get("word-pos", 0),
                        command.get("punctuation", ""), command.get("punctuation_pos", -1))
                actual = exporter.command_columns(command, self.constants)
                self.assertEqual(actual, self.pack(expected))
                self.assertTrue(all(value < 128 for value in actual))

    def test_punctuation_replaces_existing_columns_and_clips(self):
        command = {"type": "flash", "word": "mmmmmmm", "word-pos": 0,
                   "punctuation": "?", "punctuation_pos": 33}
        expected = self.original["build_flash_columns"]("mmmmmmm", 0, "?", 33)
        self.assertEqual(exporter.command_columns(command, self.constants), self.pack(expected))

    def test_flash_duration_and_last_scrolling_wrap_are_preserved(self):
        data, commands = exporter.compile_sequence(self.sequence, self.constants)
        self.assertEqual(commands[-1].kind, "scrolling")
        self.assertEqual(commands[-1].next_index, 1)
        for raw, compiled in zip(self.sequence, commands):
            self.assertEqual(compiled.flash_frames,
                             int(raw["flash-duration"]) if raw["type"] == "flash" else 0)
            self.assertEqual(len(data[compiled.offset:compiled.offset + compiled.length]), compiled.length)

    def test_initial_lead_in_is_skipped_on_subsequent_loops(self):
        _, commands = exporter.compile_sequence(self.sequence, self.constants)
        index = 0
        first_pass = []
        for _ in commands:
            first_pass.append(index)
            index = commands[index].next_index
        self.assertEqual(first_pass, list(range(len(commands))))
        self.assertEqual(index, 1)
        repeat_pass = []
        for _ in range(len(commands) - 1):
            repeat_pass.append(index)
            index = commands[index].next_index
        self.assertEqual(repeat_pass, list(range(1, len(commands))))
        self.assertEqual(index, 1)

    def test_last_flash_wraps_to_zero(self):
        _, commands = exporter.compile_sequence(
            [{"type": "scrolling", "content": ["hello"]},
             {"type": "flash", "word": "a", "flash-duration": 12}], self.constants)
        self.assertEqual(commands[-1].next_index, 0)

    def test_source_is_parsed_without_running_imports_or_screen_setup(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "constants.py"
            source.write_text("raise RuntimeError('must not run')\n" + (ROOT / "main.py").read_text())
            self.assertEqual(exporter.read_constants(source), self.constants)

    def test_constants_reject_executable_expression(self):
        with self.assertRaises(ValueError):
            exporter.constant_value(ast.parse("__import__('os').getcwd()", mode="eval").body, {})

    def test_generated_outputs_reproduce_the_compiled_payload(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            manifest = exporter.export(ROOT / "main.py", ROOT / "sequence.json", output)
            data, commands = exporter.compile_sequence(self.sequence, self.constants)
            self.assertEqual((output / "sequence_columns.bin").read_bytes(), data)
            self.assertEqual(json.loads((output / "sequence_manifest.json").read_text()), manifest)
            header = (output / "generated_sequence.h").read_text()
            self.assertIn("#define HR_SCROLL_COLS_NUM 95u", header)
            self.assertIn("#define HR_SCROLL_COLS_DEN 2u", header)
            self.assertEqual(len(manifest["commands"]), len(commands))
            repeat_output = output / "repeat"
            exporter.export(ROOT / "main.py", ROOT / "sequence.json", repeat_output)
            for filename in ("generated_sequence.h", "sequence_columns.bin", "sequence_manifest.json"):
                self.assertEqual((output / filename).read_bytes(),
                                 (repeat_output / filename).read_bytes(), filename)

    def test_malformed_input_fails_explicitly(self):
        with self.assertRaises(ValueError):
            exporter.compile_sequence([], self.constants)
        with self.assertRaises(ValueError):
            exporter.compile_sequence([{"type": "surprise"}], self.constants)


if __name__ == "__main__":
    unittest.main()
