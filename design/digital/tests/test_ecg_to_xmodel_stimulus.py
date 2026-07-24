from __future__ import annotations

import csv
import importlib.util
import json
import sys
import struct
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "ecg_to_xmodel_stimulus.py"
BATCH_SCRIPT = REPO / "tools" / "batch_make_xmodel_stimulus.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


stimulus = load_module(SCRIPT, "ecg_to_xmodel_stimulus_test")


class EcgToXmodelStimulusTest(unittest.TestCase):
    def write_csv(self, path: Path, rows: list[dict[str, object]]) -> None:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    def read_stimulus(self, path: Path) -> list[dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def test_linear_csv_mv_generates_required_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_csv = root / "ecg.csv"
            self.write_csv(
                input_csv,
                [
                    {"time_s": 0.0, "ecg_mV": 0.0},
                    {"time_s": 0.5, "ecg_mV": 1.0},
                    {"time_s": 1.0, "ecg_mV": 0.0},
                ],
            )
            out_dir = root / "out"
            result = stimulus.main(
                [
                    "--input",
                    str(input_csv),
                    "--out-dir",
                    str(out_dir),
                    "--time-col",
                    "time_s",
                    "--value-col",
                    "ecg_mV",
                    "--input-units",
                    "mV",
                    "--duration-sec",
                    "1",
                    "--stim-fs",
                    "2",
                    "--dac-mode",
                    "linear",
                ]
            )

            rows = self.read_stimulus(result.stimulus_csv)
            self.assertEqual(["time_s", "vin_v"], list(rows[0].keys()))
            self.assertEqual(len(rows), 3)
            self.assertAlmostEqual(float(rows[1]["vin_v"]), 0.001)
            self.assertTrue(result.stimulus_pwl.exists())
            self.assertTrue(result.metadata_json.exists())
            self.assertTrue(result.readme.exists())
            self.assertEqual(result.qa_plot.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

            metadata = json.loads(result.metadata_json.read_text(encoding="utf-8"))
            self.assertEqual(metadata["output_units"], "V")
            self.assertIn("not a recovery of the original raw analog ECG", metadata["limitation"])
            self.assertIn("PowerShell examples", result.readme.read_text(encoding="utf-8"))

    def test_unit_scales(self) -> None:
        self.assertAlmostEqual(stimulus.unit_scale_to_volts("V"), 1.0)
        self.assertAlmostEqual(stimulus.unit_scale_to_volts("mV"), 1.0e-3)
        self.assertAlmostEqual(stimulus.unit_scale_to_volts("uV"), 1.0e-6)
        self.assertAlmostEqual(stimulus.unit_scale_to_volts("uv"), 1.0e-6)

    def test_zoh_holds_previous_sample(self) -> None:
        source_t = stimulus.np.array([0.0, 1.0, 2.0])
        source_v = stimulus.np.array([0.0, 1.0, 2.0])
        target_t = stimulus.np.array([0.0, 0.25, 0.999, 1.0, 1.5])
        out = stimulus.reconstruct_zoh(source_t, source_v, target_t)
        self.assertEqual(out.tolist(), [0.0, 0.0, 0.0, 1.0, 1.0])

    def test_csv_channel_one_selects_second_value_column(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_csv = root / "ecg.csv"
            self.write_csv(
                input_csv,
                [
                    {"time_s": 0.0, "lead0_mV": 1.0, "lead1_mV": 10.0},
                    {"time_s": 1.0, "lead0_mV": 2.0, "lead1_mV": 20.0},
                ],
            )
            result = stimulus.main(
                [
                    "--input",
                    str(input_csv),
                    "--out-dir",
                    str(root / "out"),
                    "--time-col",
                    "time_s",
                    "--channel",
                    "1",
                    "--input-units",
                    "mV",
                    "--duration-sec",
                    "1",
                    "--stim-fs",
                    "1",
                    "--dac-mode",
                    "linear",
                ]
            )
            metadata = json.loads(result.metadata_json.read_text(encoding="utf-8"))
            self.assertEqual(metadata["channel_name"], "lead1_mV")
            rows = self.read_stimulus(result.stimulus_csv)
            self.assertAlmostEqual(float(rows[0]["vin_v"]), 0.010)

    def test_value_col_overrides_channel_selection(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_csv = root / "ecg.csv"
            self.write_csv(
                input_csv,
                [
                    {"time_s": 0.0, "lead0_mV": 1.0, "lead1_mV": 10.0},
                    {"time_s": 1.0, "lead0_mV": 2.0, "lead1_mV": 20.0},
                ],
            )
            result = stimulus.main(
                [
                    "--input",
                    str(input_csv),
                    "--out-dir",
                    str(root / "out"),
                    "--time-col",
                    "time_s",
                    "--value-col",
                    "lead1_mV",
                    "--channel",
                    "0",
                    "--input-units",
                    "mV",
                    "--duration-sec",
                    "1",
                    "--stim-fs",
                    "1",
                ]
            )
            metadata = json.loads(result.metadata_json.read_text(encoding="utf-8"))
            self.assertEqual(metadata["channel_name"], "lead1_mV")

    def test_nan_outside_selected_window_does_not_fail_error_policy(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_csv = root / "ecg.csv"
            self.write_csv(
                input_csv,
                [
                    {"time_s": 0.0, "ecg_mV": 0.0},
                    {"time_s": 1.0, "ecg_mV": 1.0},
                    {"time_s": 2.0, "ecg_mV": ""},
                ],
            )
            result = stimulus.main(
                [
                    "--input",
                    str(input_csv),
                    "--out-dir",
                    str(root / "out"),
                    "--time-col",
                    "time_s",
                    "--value-col",
                    "ecg_mV",
                    "--input-units",
                    "mV",
                    "--duration-sec",
                    "1",
                    "--stim-fs",
                    "1",
                    "--nan-policy",
                    "error",
                ]
            )
            self.assertTrue(result.stimulus_csv.exists())

    def test_zoh_pwl_uses_staircase_points(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_csv = root / "ecg.csv"
            self.write_csv(
                input_csv,
                [
                    {"time_s": 0.0, "ecg_mV": 0.0},
                    {"time_s": 1.0, "ecg_mV": 1.0},
                ],
            )
            result = stimulus.main(
                [
                    "--input",
                    str(input_csv),
                    "--out-dir",
                    str(root / "out"),
                    "--time-col",
                    "time_s",
                    "--value-col",
                    "ecg_mV",
                    "--input-units",
                    "mV",
                    "--duration-sec",
                    "1",
                    "--stim-fs",
                    "2",
                    "--dac-mode",
                    "zoh",
                ]
            )
            csv_rows = self.read_stimulus(result.stimulus_csv)
            pwl_lines = result.stimulus_pwl.read_text(encoding="utf-8").splitlines()
            metadata = json.loads(result.metadata_json.read_text(encoding="utf-8"))
            self.assertGreater(len(pwl_lines), len(csv_rows))
            self.assertEqual(metadata["pwl"]["semantics"], "mode-aware staircase for zoh")

    def test_pchip_is_shape_preserving_for_monotone_data(self) -> None:
        source_t = stimulus.np.array([0.0, 1.0, 2.0, 3.0])
        source_v = stimulus.np.array([0.0, 1.0, 1.5, 2.0])
        target_t = stimulus.np.linspace(0.0, 3.0, 61)
        out = stimulus.reconstruct_pchip(source_t, source_v, target_t)
        self.assertGreaterEqual(float(out.min()), 0.0)
        self.assertLessEqual(float(out.max()), 2.0)
        self.assertTrue(bool(stimulus.np.all(stimulus.np.diff(out) >= -1.0e-12)))

    def test_nan_interpolation_and_low_fs_warning_are_recorded(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_csv = root / "ecg.csv"
            self.write_csv(
                input_csv,
                [
                    {"time_s": 0.0, "ecg_mV": 0.0},
                    {"time_s": 1.0, "ecg_mV": ""},
                    {"time_s": 2.0, "ecg_mV": 2.0},
                ],
            )
            result = stimulus.main(
                [
                    "--input",
                    str(input_csv),
                    "--out-dir",
                    str(root / "out"),
                    "--time-col",
                    "time_s",
                    "--value-col",
                    "ecg_mV",
                    "--input-units",
                    "mV",
                    "--stim-fs",
                    "1",
                    "--duration-sec",
                    "2",
                    "--dac-mode",
                    "linear",
                ]
            )
            metadata = json.loads(result.metadata_json.read_text(encoding="utf-8"))
            codes = {warning["code"] for warning in metadata["warnings"]}
            self.assertIn("NAN_LONG_GAP_INTERPOLATED", codes)
            self.assertIn("LOW_SOURCE_FS", codes)
            rows = self.read_stimulus(result.stimulus_csv)
            self.assertAlmostEqual(float(rows[1]["vin_v"]), 0.001)

    def test_max_output_points_guard(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_csv = root / "ecg.csv"
            self.write_csv(
                input_csv,
                [
                    {"time_s": 0.0, "ecg_mV": 0.0},
                    {"time_s": 1.0, "ecg_mV": 1.0},
                ],
            )
            with self.assertRaises(ValueError):
                stimulus.main(
                    [
                        "--input",
                        str(input_csv),
                        "--out-dir",
                        str(root / "out"),
                        "--time-col",
                        "time_s",
                        "--value-col",
                        "ecg_mV",
                        "--input-units",
                        "mV",
                        "--duration-sec",
                        "1",
                        "--stim-fs",
                        "100",
                        "--max-output-points",
                        "10",
                    ]
                )

    def test_batch_routes_known_class_segments(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_root = root / "data"
            nsr = input_root / "nsrdb"
            nsr.mkdir(parents=True)
            self.write_csv(
                nsr / "case001.csv",
                [
                    {"time_s": 0.0, "ecg_mV": 0.0},
                    {"time_s": 1.0, "ecg_mV": 1.0},
                ],
            )

            sys_path_added = False
            if str(REPO / "tools") not in sys.path:
                sys.path.insert(0, str(REPO / "tools"))
                sys_path_added = True
            try:
                batch = load_module(BATCH_SCRIPT, "batch_make_xmodel_stimulus_test")
                summary = batch.main(
                    [
                        "--input-root",
                        str(input_root),
                        "--output-root",
                        str(root / "build"),
                        "--duration-sec",
                        "1",
                        "--stim-fs",
                        "1",
                        "--input-units",
                        "mV",
                        "--time-col",
                        "time_s",
                        "--value-col",
                        "ecg_mV",
                    ]
                )
            finally:
                if sys_path_added:
                    sys.path.remove(str(REPO / "tools"))

            self.assertEqual(summary["counts"]["ok"], 1)
            self.assertTrue((root / "build" / "NSR").exists())

    def test_batch_manifest_handles_first_failure_then_success(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_root = root / "data" / "nsrdb"
            input_root.mkdir(parents=True)
            (input_root / "a_bad.csv").write_text("time_s,bad\n0,0\n", encoding="utf-8")
            self.write_csv(
                input_root / "b_good.csv",
                [
                    {"time_s": 0.0, "ecg_mV": 0.0},
                    {"time_s": 1.0, "ecg_mV": 1.0},
                ],
            )
            sys_path_added = False
            if str(REPO / "tools") not in sys.path:
                sys.path.insert(0, str(REPO / "tools"))
                sys_path_added = True
            try:
                batch = load_module(BATCH_SCRIPT, "batch_make_xmodel_stimulus_test_mixed")
                summary = batch.main(
                    [
                        "--input-root",
                        str(root / "data"),
                        "--output-root",
                        str(root / "build"),
                        "--duration-sec",
                        "1",
                        "--stim-fs",
                        "1",
                        "--input-units",
                        "mV",
                        "--time-col",
                        "time_s",
                        "--value-col",
                        "ecg_mV",
                    ]
                )
            finally:
                if sys_path_added:
                    sys.path.remove(str(REPO / "tools"))
            self.assertEqual(summary["counts"]["failed"], 1)
            self.assertEqual(summary["counts"]["ok"], 1)
            self.assertTrue((root / "build" / "summary_manifest.csv").exists())

    def test_batch_skips_generated_output_under_input_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_root = root / "data"
            nsr = input_root / "nsrdb"
            generated = input_root / "build" / "xmodel_stimulus" / "NSR" / "old"
            nsr.mkdir(parents=True)
            generated.mkdir(parents=True)
            self.write_csv(
                nsr / "case001.csv",
                [
                    {"time_s": 0.0, "ecg_mV": 0.0},
                    {"time_s": 1.0, "ecg_mV": 1.0},
                ],
            )
            self.write_csv(
                generated / "stimulus_xmodel.csv",
                [
                    {"time_s": 0.0, "vin_v": 0.0},
                    {"time_s": 1.0, "vin_v": 1.0},
                ],
            )
            sys_path_added = False
            if str(REPO / "tools") not in sys.path:
                sys.path.insert(0, str(REPO / "tools"))
                sys_path_added = True
            try:
                batch = load_module(BATCH_SCRIPT, "batch_make_xmodel_stimulus_test_skip")
                summary = batch.main(
                    [
                        "--input-root",
                        str(input_root),
                        "--output-root",
                        str(input_root / "build" / "xmodel_stimulus"),
                        "--duration-sec",
                        "1",
                        "--stim-fs",
                        "1",
                        "--input-units",
                        "mV",
                        "--time-col",
                        "time_s",
                        "--value-col",
                        "ecg_mV",
                    ]
                )
            finally:
                if sys_path_added:
                    sys.path.remove(str(REPO / "tools"))
            self.assertEqual(summary["counts"]["ok"], 1)
            self.assertEqual(len(summary["rows"]), 1)

    def test_internal_wfdb_rejects_unsupported_modifiers(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "r.hea").write_text(
                "r 1 250 2\nr.dat 16+1 200/mV 16 0 0 0 0 lead\n",
                encoding="utf-8",
            )
            (root / "r.dat").write_bytes(struct.pack("<hh", 0, 1))
            with self.assertRaises(ValueError):
                stimulus.main(
                    [
                        "--input",
                        str(root / "r.hea"),
                        "--out-dir",
                        str(root / "out"),
                        "--duration-sec",
                        "0.004",
                    ]
                )

    def test_internal_wfdb_missing_gain_warns(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "r.hea").write_text("r 1 250 2\nr.dat 16\n", encoding="utf-8")
            (root / "r.dat").write_bytes(struct.pack("<hh", 0, 200))
            result = stimulus.main(
                [
                    "--input",
                    str(root / "r.hea"),
                    "--out-dir",
                    str(root / "out"),
                    "--duration-sec",
                    "0.004",
                    "--low-source-fs-warn-hz",
                    "0",
                ]
            )
            metadata = json.loads(result.metadata_json.read_text(encoding="utf-8"))
            codes = {warning["code"] for warning in metadata["warnings"]}
            self.assertIn("WFDB_GAIN_ASSUMED", codes)
            self.assertTrue(metadata["input_metadata"]["wfdb_signals"][0]["gain_assumed"])


if __name__ == "__main__":
    unittest.main()
