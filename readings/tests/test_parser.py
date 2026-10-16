from datetime import datetime
from decimal import Decimal

from django.test import SimpleTestCase

from readings.services.parser import parse_reading


class ParseReadingTests(SimpleTestCase):

    def test_converts_reading_fields(self):
        record = {
            "mpan": "1234567890123",
            "meter_serial_number": "METER123",
            "register_id": "1",
            "reading_date": "2026-10-15 10:30:00",
            "reading_type": "A",
            "reading_value": "12345.678",
        }

        result = parse_reading(record)
        self.assertEqual(result.mpan, "1234567890123")
        self.assertEqual(result.meter_serial_number, "METER123")
        self.assertEqual(result.register_id, "1")
        self.assertEqual(
            result.reading_date,
            datetime(2026, 10, 15, 10, 30),
        )
        self.assertEqual(result.reading_type, "A")
        self.assertEqual(result.reading_value, Decimal("12345.678"))
