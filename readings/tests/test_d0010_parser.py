from pathlib import Path

from django.test import SimpleTestCase

from readings.services.parser import parse_d0010


class ParseD0010Tests(SimpleTestCase):
    def setUp(self):
        self.file_path = Path(__file__).parent / "sample_data" / "sample_d0010.uff"

    def test_parses_header_and_trailer(self):
        result = parse_d0010(self.file_path)
        self.assertEqual(result.header[0], "ZHV")
        self.assertEqual(result.trailer[0], "ZPT")

    def test_groups_records_by_mpan(self):

        result = parse_d0010(self.file_path)

        self.assertEqual(len(result.mpan_groups), 11)

        first_group = result.mpan_groups[0]
        self.assertEqual(first_group.mpan, "1200023305967")
        self.assertEqual(first_group.meter_record[0], "028")
        self.assertEqual(len(first_group.reading_records), 1)

    def test_mpan_can_have_multiple_readings(self):
        result = parse_d0010(self.file_path)

        group = next(
            group for group in result.mpan_groups if group.mpan == "2200031930792"
        )

        self.assertEqual(len(group.reading_records), 2)
        self.assertEqual(group.reading_records[0][1], "01")
        self.assertEqual(group.reading_records[1][1], "02")
