from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.utils import timezone

# D0010 record field indexes
MPAN_VALUE_INDEX = 1

METER_SERIAL_NUMBER_INDEX = 1
METER_READING_TYPE_INDEX = 2

REGISTER_ID_INDEX = 1
READING_DATE_INDEX = 2
READING_VALUE_INDEX = 3

HEADER_FILE_ID_INDEX = 1
HEADER_FLOW_ID_INDEX = 2
TRAILER_FILE_ID_INDEX = 1
TRAILER_RECORD_COUNT_INDEX = 2
TRAILER_GROUP_COUNT_INDEX = 4

TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"


@dataclass(frozen=True)
class ReadingRecord:
    mpan: str
    meter_serial_number: str
    register_id: str
    reading_date: datetime
    reading_type: str
    reading_value: Decimal


@dataclass
class MpanGroup:
    mpan: str
    meter_record: list[str] | None = None
    reading_records: list[list[str]] = field(default_factory=list)
    readings: list[ReadingRecord] = field(default_factory=list)


@dataclass
class D0010File:
    header: list[str]
    trailer: list[str]
    mpan_groups: list[MpanGroup]


def parse_reading(record: dict) -> ReadingRecord:
    """Convert extracted reading fields into a validated ReadingRecord."""
    try:
        reading_date = datetime.strptime(
            record["reading_date"].strip(),
            TIMESTAMP_FORMAT,
        )

        # Use the Django-configured timezone consistently.
        if timezone.is_naive(reading_date):
            reading_date = timezone.make_aware(reading_date)

        return ReadingRecord(
            mpan=record["mpan"].strip(),
            meter_serial_number=record["meter_serial_number"].strip(),
            register_id=record["register_id"].strip(),
            reading_date=reading_date,
            reading_type=record["reading_type"].strip(),
            reading_value=Decimal(record["reading_value"].strip()),
        )
    except (KeyError, AttributeError, TypeError, ValueError, InvalidOperation) as exc:
        raise ValueError(f"Invalid reading record: {exc}") from exc


def parse_d0010(path: str | Path) -> D0010File:
    """Parse a D0010 file and convert its readings into structured objects."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            lines = [line.rstrip("\r\n").split("|") for line in file if line.strip()]
    except OSError:
        raise
    except UnicodeError as exc:
        raise ValueError(f"Unable to decode D0010 file: {exc}") from exc

    if not lines:
        raise ValueError("D0010 file is empty")

    header = lines[0]
    trailer = lines[-1]

    if header[0] != "ZHV":
        raise ValueError("D0010 file must start with a ZHV header")

    if trailer[0] != "ZPT":
        raise ValueError("D0010 file must end with a ZPT trailer")

    if len(header) <= HEADER_FLOW_ID_INDEX:
        raise ValueError("Invalid ZHV header: missing flow identifier")

    if not header[HEADER_FLOW_ID_INDEX].startswith("D0010"):
        raise ValueError(
            "Unexpected flow identifier: " f"{header[HEADER_FLOW_ID_INDEX]!r}"
        )

    if len(header) <= HEADER_FILE_ID_INDEX:
        raise ValueError("Invalid ZHV header: missing file ID")

    if len(trailer) <= TRAILER_GROUP_COUNT_INDEX:
        raise ValueError("Invalid ZPT trailer: missing required fields")

    if header[HEADER_FILE_ID_INDEX] != trailer[TRAILER_FILE_ID_INDEX]:
        raise ValueError("Header and trailer file IDs do not match")

    try:
        declared_record_count = int(trailer[TRAILER_RECORD_COUNT_INDEX])
        declared_group_count = int(trailer[TRAILER_GROUP_COUNT_INDEX])
    except (ValueError, IndexError) as exc:
        raise ValueError("Invalid record or group count in ZPT trailer") from exc

    body_records = lines[1:-1]
    actual_record_count = len(body_records)

    if declared_record_count != actual_record_count:
        raise ValueError(
            "Trailer record count mismatch: "
            f"expected {declared_record_count}, found {actual_record_count}"
        )

    actual_group_count = sum(1 for record in body_records if record[0] == "026")

    if declared_group_count != actual_group_count:
        raise ValueError(
            "Trailer group count mismatch: "
            f"expected {declared_group_count}, found {actual_group_count}"
        )

    mpan_groups = []
    current_group = None

    for record in body_records:
        record_type = record[0]

        if record_type == "026":
            if len(record) <= MPAN_VALUE_INDEX or not record[MPAN_VALUE_INDEX].strip():
                raise ValueError(f"Invalid 026 record: {record!r}")

            current_group = MpanGroup(mpan=record[MPAN_VALUE_INDEX].strip())
            mpan_groups.append(current_group)

        elif record_type == "028":
            if current_group is None:
                raise ValueError("Meter record found before an MPAN record")

            if len(record) <= METER_READING_TYPE_INDEX:
                raise ValueError(f"Invalid 028 record: {record!r}")

            if current_group.meter_record is not None:
                raise ValueError(
                    f"Unexpected second meter record for MPAN " f"{current_group.mpan}"
                )

            current_group.meter_record = record

        elif record_type == "030":
            if current_group is None:
                raise ValueError("Reading found before an MPAN record")

            if len(record) <= READING_VALUE_INDEX:
                raise ValueError(f"Invalid 030 record: {record!r}")

            current_group.reading_records.append(record)

        else:
            raise ValueError(f"Unexpected record type: {record_type}")

    if not mpan_groups:
        raise ValueError("D0010 file contains no MPAN groups")

    for group in mpan_groups:
        if group.meter_record is None:
            raise ValueError(f"Missing meter record for MPAN {group.mpan}")

        if not group.reading_records:
            raise ValueError(f"Missing readings for MPAN {group.mpan}")

        group.readings = convert_group_readings(group)

    return D0010File(
        header=header,
        trailer=trailer,
        mpan_groups=mpan_groups,
    )


def convert_group_readings(group: MpanGroup) -> list[ReadingRecord]:
    """Combine meter details with register readings for one MPAN."""
    if group.meter_record is None:
        raise ValueError(f"Missing meter record for MPAN {group.mpan}")

    meter_record = group.meter_record

    if len(meter_record) <= METER_READING_TYPE_INDEX:
        raise ValueError(f"Invalid 028 record for MPAN {group.mpan}: {meter_record!r}")

    meter_serial_number = meter_record[METER_SERIAL_NUMBER_INDEX].strip()
    reading_type = meter_record[METER_READING_TYPE_INDEX].strip()

    if not meter_serial_number:
        raise ValueError(f"Missing meter serial number for MPAN {group.mpan}")

    if not reading_type:
        raise ValueError(f"Missing reading type for MPAN {group.mpan}")

    readings = []

    for record in group.reading_records:
        try:
            if len(record) <= READING_VALUE_INDEX:
                raise ValueError(
                    "Expected at least 4 fields in a 030 record; "
                    f"received {len(record)}"
                )

            reading = parse_reading(
                {
                    "mpan": group.mpan,
                    "meter_serial_number": meter_serial_number,
                    "register_id": record[REGISTER_ID_INDEX],
                    "reading_date": record[READING_DATE_INDEX],
                    "reading_type": reading_type,
                    "reading_value": record[READING_VALUE_INDEX],
                }
            )
            readings.append(reading)

        except (IndexError, ValueError) as exc:
            raise ValueError(
                f"Invalid 030 record for MPAN {group.mpan}: " f"{record!r} ({exc})"
            ) from exc

    return readings
