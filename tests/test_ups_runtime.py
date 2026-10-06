import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from ups_runtime import (Battery, load_from_csv, required_capacity_ah,  # noqa: E402
                         required_ups_va, runtime_minutes)


class BatteryTests(unittest.TestCase):
    def test_usable_energy(self):
        # 48 V x 100 Ah x 0.8 DoD x 0.9 efficiency x 0.8 aging = 2764.8 Wh
        self.assertAlmostEqual(Battery(48, 100).usable_wh(), 2764.8)

    def test_lead_acid_gives_less_than_lifepo4(self):
        self.assertLess(Battery(48, 100, "lead-acid").usable_wh(),
                        Battery(48, 100, "lifepo4").usable_wh())

    def test_unknown_chemistry_rejected(self):
        with self.assertRaises(ValueError):
            Battery(48, 100, "nickel")

    def test_non_positive_size_rejected(self):
        with self.assertRaises(ValueError):
            Battery(0, 100)


class RuntimeTests(unittest.TestCase):
    def test_runtime(self):
        # 2764.8 Wh / 1000 W = 2.7648 h = 165.888 min
        self.assertAlmostEqual(runtime_minutes(Battery(48, 100), 1000), 165.888)

    def test_zero_load_rejected(self):
        with self.assertRaises(ValueError):
            runtime_minutes(Battery(48, 100), 0)

    def test_sizing_is_inverse_of_runtime(self):
        minutes = runtime_minutes(Battery(48, 100), 1000)
        self.assertAlmostEqual(required_capacity_ah(1000, minutes, 48), 100)

    def test_ups_rating(self):
        # 900 W / 0.9 PF = 1000 VA, plus 25 % headroom = 1250 VA
        self.assertAlmostEqual(required_ups_va(900), 1250)


class CsvTests(unittest.TestCase):
    def test_load_from_csv(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False,
                                         encoding="utf-8", newline="") as f:
            f.write("device,quantity,watts\nhost,2,350\nswitch,1,150\n")
            path = f.name
        try:
            self.assertEqual(load_from_csv(path), 850)
        finally:
            os.remove(path)

    def test_sample_file_total(self):
        sample = Path(__file__).resolve().parent.parent / "data" / "sample_load.csv"
        self.assertEqual(load_from_csv(str(sample)), 1610)


if __name__ == "__main__":
    unittest.main()
