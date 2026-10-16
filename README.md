# Kraken Meter Reading Importer

**Author:** Adith Jaison

## Getting Started

### Requirements

- Python 3.10 or later
- pip

### 1. Extract the submission

Extract the submitted tarball and enter the project directory:

```bash
tar -xzf Adith_Jaison_Kraken_Task.tar.gz
cd kraken_task
```

The directory name may differ depending on the submitted archive.

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Set up the database

```bash
python manage.py migrate
```

### 5. Run the checks and tests

```bash
python manage.py check
python manage.py test
```

### 6. Import the sample file

From the project root, run:

```bash
python manage.py import_d0010 readings/tests/sample_data/sample_d0010.uff
```

On a clean database, the supplied sample file is expected to import 13 readings.

### 7. Access Django Admin

Create an administrator account:

```bash
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/admin/ and sign in with the superuser credentials.





## What I Didn’t Have Time to Complete / Assumptions / Future Ideas

### Assumptions

- **Timezone:** Django is configured with `USE_TZ = True` and `TIME_ZONE = "UTC"`. Reading timestamps are made timezone-aware using the configured timezone. The assumption that source timestamps represent UTC should be confirmed against the source system's conventions.
- **Deduplication:** A database uniqueness constraint uses the source filename, MPAN, meter serial number, register ID, reading date, reading type and reading value. Re-importing the same file should not create duplicate records. Identical readings from different filenames can be stored separately.
- **Ignored fields:** The importer currently focuses on fields required to search and review readings. Other D0010 fields are not persisted unless explicitly handled by the parser.

### Limitations and Future Ideas

- **REST upload:** File imports are currently performed using a Django management command. A REST API upload endpoint has not been implemented.
- **Parser coverage:** Expand support and tests for optional and conditional D0010 record types, and improve validation of malformed records.
- **Import reporting:** Report created, skipped and invalid records more comprehensively.
- **Testing:** Add regression tests for duplicate imports, malformed records and optional record types.
- **Scalability:** Improve processing for larger files while preserving transaction safety and duplicate handling.
- **Admin experience:** Add further filtering and date-range search options if required.