PostgreSQL – kod
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from sqlalchemy import create_engine, text
    import simplejson
    import pandas as pd
    import json

    # Wczytaj dane do połączenia z pliku JSON
    with open("/home/student02/lab8/database_creds.json") as db_con_file:
        creds = simplejson.loads(db_con_file.read())

    connection = (
        f"postgresql+psycopg://{creds['user_name']}:{creds['password']}@"
        f"{creds['host_name']}:{creds['port_number']}/{creds['db_name']}"
    )

    engine = create_engine(connection)

    # Utworzenie tabel, jeśli nie istnieją
    create_tables_sql = """
    CREATE TABLE IF NOT EXISTS Patient (
        patient_id SERIAL PRIMARY KEY,
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        pesel VARCHAR(11) UNIQUE,
        birth_date DATE,
        email VARCHAR(100),
        phone VARCHAR(20)
    );

    CREATE TABLE IF NOT EXISTS Doctor (
        doctor_id SERIAL PRIMARY KEY,
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        license_number INTEGER UNIQUE
    );

    CREATE TABLE IF NOT EXISTS Visit (
        visit_id SERIAL PRIMARY KEY,
        patient_id INTEGER REFERENCES Patient(patient_id),
        doctor_id INTEGER REFERENCES Doctor(doctor_id),
        visit_datetime TIMESTAMP,
        status VARCHAR(20),
        notes TEXT
    );
    """

    with engine.begin() as conn:
        conn.execute(text(create_tables_sql))

    # Wczytywanie pacjentów
    with open('patients.json', 'r', encoding='utf-8') as f:
        patients = json.load(f)

    with engine.begin() as conn:
        for p in patients:
            try:
                conn.execute(text('''
                    INSERT INTO Patient (first_name, last_name, pesel, birth_date, email, phone)
                    VALUES (:first_name, :last_name, :pesel, :birth_date, :email, :phone)
                    ON CONFLICT (pesel) DO NOTHING
                '''), p)
            except Exception as e:
                print(f"Błąd przy dodawaniu pacjenta {p['pesel']}: {e}")

    # Wczytywanie lekarzy
    with open('doctors.json', 'r', encoding='utf-8') as f:
        doctors = json.load(f)

    with engine.begin() as conn:
        for d in doctors:
            try:
                conn.execute(text('''
                    INSERT INTO Doctor (first_name, last_name, license_number)
                    VALUES (:first_name, :last_name, :license_number)
                    ON CONFLICT (license_number) DO NOTHING
                '''), d)
            except Exception as e:
                print(f"Błąd przy dodawaniu lekarza {d['license_number']}: {e}")

    # Wczytywanie wizyt
    df = pd.read_csv('visits.csv')

    with engine.begin() as conn:
        for _, row in df.iterrows():
            try:
                conn.execute(text('''
                    INSERT INTO Visit (patient_id, doctor_id, visit_datetime, status, notes)
                    VALUES (:patient_id, :doctor_id, :visit_datetime, :status, :notes)
                '''), {
                    "patient_id": row['patient_id'],
                    "doctor_id": row['doctor_id'],
                    "visit_datetime": row['visit_datetime'],
                    "status": row['status'],
                    "notes": row.get('notes', None)
                })
            except Exception as e:
                print(f"Błąd przy dodawaniu wizyty {row}: {e}")

    print("Dane testowe zostały załadowane.")
