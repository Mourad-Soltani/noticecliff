# Signature: Mourad.Soltani
import unittest

from noticecliff.calculator import NoticeCliffError, compute_cliff, risk_band


class CalculatorTests(unittest.TestCase):
    def test_calendar_thirty_days(self):
        result = compute_cliff("2026-12-01", 30, as_of="2026-10-01")
        self.assertEqual(result.cancel_by, "2026-11-01")
        self.assertEqual(result.days_remaining, 31)
        self.assertEqual(result.risk, "safe")

    def test_business_days_skip_weekend(self):
        # 2026-11-16 is a Monday. 5 business days ending the day before renewal
        # walk back across the prior weekend.
        result = compute_cliff("2026-11-16", 5, count_mode="business", as_of="2026-11-01")
        self.assertEqual(result.cancel_by, "2026-11-09")
        self.assertTrue(any(d.startswith("2026-11-14") or d.startswith("2026-11-1") for d in result.skipped_dates))

    def test_missed_window(self):
        result = compute_cliff("2026-10-05", 10, as_of="2026-10-01")
        self.assertEqual(result.cancel_by, "2026-09-25")
        self.assertEqual(result.risk, "missed")
        self.assertLess(result.days_remaining, 0)

    def test_buffer_pulls_date_forward(self):
        plain = compute_cliff("2026-12-01", 30, as_of="2026-10-01")
        buffered = compute_cliff("2026-12-01", 30, buffer_days=2, as_of="2026-10-01")
        self.assertEqual(buffered.cancel_by, "2026-10-30")
        self.assertNotEqual(plain.cancel_by, buffered.cancel_by)

    def test_rejects_bad_mode(self):
        with self.assertRaises(NoticeCliffError):
            compute_cliff("2026-12-01", 10, count_mode="lunar")

    def test_risk_bands(self):
        self.assertEqual(risk_band(-1), "missed")
        self.assertEqual(risk_band(0), "critical")
        self.assertEqual(risk_band(14), "soon")
        self.assertEqual(risk_band(15), "safe")


if __name__ == "__main__":
    unittest.main()
