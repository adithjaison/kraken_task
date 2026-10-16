from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class ReadingRecord:
    mpan: str
    meter_serial_number: str
    register_id: str
    reading_date: datetime
    reading_type: str
    reading_value: Decimal


def parse_reading(record: dict):

    try:
        return ReadingRecord(
            mpan=record["mpan"].strip(),
            meter_serial_number=record["meter_serial_number"].strip(),
            register_id=record["register_id"].strip(),
            reading_date=datetime.strptime(
                record["reading_date"],
                "%Y-%m-%d %H:%M:%S",
            ),
            reading_type=record["reading_type"].strip(),
            reading_value=Decimal(record["reading_value"].strip()),
        )
    except (KeyError, ValueError, InvalidOperation) as exc:
        raise ValueError(f"Invalid reading record: {exc}") from exc


@dataclass
class MpanGroup:
    mpan: str
    meter_record: list[str] | None = None
    reading_records: list[list[str]] | None = None

    def __post_init__(self):
        if self.reading_records is None:
            self.reading_records = []


@dataclass
class D0010File:
    header: list[str]
    trailer: list[str]
    mpan_groups: list[MpanGroup]


def parse_d0010(path):
    with open(path, "r", encoding="utf-8") as file:
        lines = [line.rstrip("\r\n").split("|") for line in file if line.strip()]

    if not lines or lines[0][0] != "ZHV":
        raise ValueError("D0010 file must start with a ZHV header")
    if lines[-1][0] != "ZPT":
        raise ValueError("D0010 file must end with a ZPT trailer")

    header = lines[0]
    trailer = lines[-1]
    mpan_groups = []
    current_group = None

    for record in lines[1:-1]:
        record_type = record[0]
        if record_type == "026":
            current_group = MpanGroup(mpan=record[1])
            mpan_groups.append(current_group)
        elif record_type == "028":
            if current_group is None:
                raise ValueError("Meter record found before an MPAN record")
            if current_group.meter_record is not None:
                raise ValueError("Unexpected second meter record for an MPAN")
            current_group.meter_record = record

        elif record_type == "030":
            if current_group is None:
                raise ValueError("Reading found before an MPAN record")
            current_group.reading_records.append(record)
        else:
            raise ValueError(f"Unexpected record type: {record_type}")

    for group in mpan_groups:
        if group.meter_record is None:
            raise ValueError(f"Missing meter record for MPAN {group.mpan}")
        if not group.reading_records:
            raise ValueError(f"Missing readings for MPAN {group.mpan}")

    return D0010File(
        header=header,
        trailer=trailer,
        mpan_groups=mpan_groups,
    )
