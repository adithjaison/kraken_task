from decimal import Decimal
from pathlib import Path

from django.test import SimpleTestCase

from readings.services.parser import convert_group_readings, parse_d0010


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

    def test_rejects_file_without_header(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "invalid.uff"
            file_path.write_text(
                "026|1200023305967|V|\n"
                "028|F75A 00802|D|\n"
                "030|S|20160222000000|56311.0|||T|N|\n"
                "ZPT|0000475656|35||11|20160302154650|\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                parse_d0010(file_path)

    def test_rejects_file_without_trailer(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "invalid.uff"
            file_path.write_text(
                "ZHV|0000475656|D0010002|D|UDMS|X|MRCY|20160302153151||||OPER|\n"
                "026|1200023305967|V|\n"
                "028|F75A 00802|D|\n"
                "030|S|20160222000000|56311.0|||T|N|\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                parse_d0010(file_path)

    def test_converts_group_into_reading_objects(self):
        result = parse_d0010(self.file_path)
        group = result.mpan_groups[0]

        readings = convert_group_readings(group)

        self.assertEqual(readings[0].mpan, "1200023305967")
        self.assertEqual(readings[0].meter_serial_number, "F75A 00802")
        self.assertEqual(readings[0].register_id, "S")
        self.assertEqual(readings[0].reading_value, Decimal("56311.0"))
