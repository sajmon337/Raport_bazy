Kod bazy danych:
=====================

.. code-block:: python

    from sqlalchemy import create_engine, text
    import simplejson
    import pandas as pd

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

    # --- Wczytywanie danych ---

    # Wczytywanie pacjentów
    import json
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

    # przykładowe zapytania do bazy danych w celu zmierzenia czasu wykonania i pobrania wyniku
    import sqlite3
    import time

    def measure_sqlite_queries(db_path, queries):
    """
    Mierzy czas wykonania podanych zapytań SQL na bazie SQLite i wypisuje wyniki.

    Args:
        db_path (str): Ścieżka do pliku bazy SQLite.
        queries (list of str): Lista zapytań SQL do wykonania.

    Efekty działania:
        Wypisuje na standardowe wyjście zapytanie, czas wykonania oraz liczbę zwróconych wierszy.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for q in queries:
        start = time.time()
        cursor.execute(q)
        rows = cursor.fetchall()
        duration = time.time() - start
        print(f"Zapytanie:\n{q}")
        print(f"Czas wykonania: {duration:.4f} s")
        print(f"Liczba zwróconych wierszy: {len(rows)}")
        print("-" * 40)

    conn.close()

    if __name__ == "__main__":
    db_path = "clinic.db"
    queries = [
        "SELECT * FROM Visit WHERE status = 'completed' LIMIT 100;",
        "SELECT patient_id, COUNT(*) FROM Visit GROUP BY patient_id LIMIT 100;",
        "SELECT * FROM Doctor WHERE specialization LIKE 'cardio%' LIMIT 100;"
    ]

    measure_sqlite_queries(db_path, queries)



    # wypisanie raportu z bazy danych
    import sqlite3
    import pandas as pd
    import matplotlib.pyplot as plt

    def generate_reports(db_path="clinic.db"):
    """
    Generuje raporty i wizualizacje na podstawie danych kliniki z bazy SQLite.

    Args:
        db_path (str): Ścieżka do pliku bazy SQLite.

    Efekty działania:
        - Wyświetla statystyki liczby pacjentów, lekarzy i wizyt.
        - Wyświetla liczby wizyt pogrupowane wg lekarzy i statusów.
        - Generuje wykresy słupkowe wizyt wg lekarzy oraz wykres liniowy wizyt w czasie.
    """
    # Połączenie z bazą
    conn = sqlite3.connect(db_path)
    
    # Wczytanie danych do DataFrame’ów
    patients = pd.read_sql_query("SELECT * FROM Patient", conn)
    doctors = pd.read_sql_query("SELECT * FROM Doctor", conn)
    visits = pd.read_sql_query("SELECT * FROM Visit", conn)
    
    # Połączenie danych wizyt z lekarzami i pacjentami
    visits_full = visits.merge(doctors, on="doctor_id", suffixes=('', '_doctor')) \
                        .merge(patients, on="patient_id", suffixes=('', '_patient'))

    print("\n Liczba pacjentów:", len(patients))
    print(" Liczba lekarzy:", len(doctors))
    print(" Liczba wizyt:", len(visits))

    # Wizyty wg lekarzy
    visits_per_doctor = visits_full.groupby(["first_name", "last_name"]).size().sort_values(ascending=False)
    print("\n Liczba wizyt wg lekarzy:")
    print(visits_per_doctor)

    # Wizyty wg statusu
    status_counts = visits["status"].value_counts()
    print("\n Liczba wizyt wg statusu:")
    print(status_counts)

    # Wizyty wg miesiąca
    visits["visit_month"] = pd.to_datetime(visits["visit_datetime"]).dt.to_period("M")
    visits_per_month = visits["visit_month"].value_counts().sort_index()

    # Wykres: liczba wizyt na lekarza
    plt.figure(figsize=(10, 5))
    visits_per_doctor.plot(kind="bar", title="Liczba wizyt wg lekarzy")
    plt.xlabel("Lekarz")
    plt.ylabel("Liczba wizyt")
    plt.tight_layout()
    plt.show()

    # Wykres: wizyty w czasie
    plt.figure(figsize=(10, 5))
    visits_per_month.plot(kind="line", marker="o", title="Wizyty w czasie")
    plt.xlabel("Miesiąc")
    plt.ylabel("Liczba wizyt")
    plt.tight_layout()
    plt.show()

    conn.close()

    # Uruchom raport
    generate_reports()


  
    # reset tabeli
    import sqlite3

    conn = sqlite3.connect("clinic.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS Visit;")
    cursor.execute("DROP TABLE IF EXISTS Patient;")
    cursor.execute("DROP TABLE IF EXISTS Doctor;")
    conn.commit()
    conn.close()
    print("Baza danych została zresetowana.")

    # Metody zapytań bazy danych
    import sqlite3
    import pandas as pd

    class ClinicDB:
    """
    Klasa do obsługi bazy danych kliniki SQLite z wykorzystaniem Pandas.

    Atrybuty:
        conn (sqlite3.Connection): Połączenie z bazą danych.

    Metody:
        get_all_patients(): Zwraca DataFrame ze wszystkimi pacjentami.
        get_all_doctors(): Zwraca DataFrame ze wszystkimi lekarzami.
        get_all_visits(): Zwraca DataFrame ze wszystkimi wizytami.
        find_patients_by_name(name_part): Wyszukuje pacjentów po fragmencie imienia lub nazwiska.
        find_doctor_by_specialization(specialization): Wyszukuje lekarzy według specjalizacji.
        get_visits_by_patient(pesel): Pobiera wizyty konkretnego pacjenta po peselu.
        get_visits_by_doctor(doctor_last_name): Pobiera wizyty danego lekarza po nazwisku.
        get_visits_by_status(status): Pobiera wizyty o określonym statusie.
        close(): Zamknięcie połączenia z bazą.
    """

    def __init__(self, db_path='clinic.db'):
        """
        Inicjalizuje połączenie z bazą danych.

        Args:
            db_path (str): Ścieżka do pliku bazy SQLite.
        """
        self.conn = sqlite3.connect(db_path)
    
    def get_all_patients(self):
        """
        Pobiera wszystkie rekordy z tabeli Patient.

        Returns:
            pandas.DataFrame: Dane pacjentów.
        """
        return pd.read_sql("SELECT * FROM Patient", self.conn)

    def get_all_doctors(self):
        """
        Pobiera wszystkie rekordy z tabeli Doctor.

        Returns:
            pandas.DataFrame: Dane lekarzy.
        """
        return pd.read_sql("SELECT * FROM Doctor", self.conn)

    def get_all_visits(self):
        """
        Pobiera wszystkie rekordy z tabeli Visit.

        Returns:
            pandas.DataFrame: Dane wizyt.
        """
        return pd.read_sql("SELECT * FROM Visit", self.conn)

    def find_patients_by_name(self, name_part):
        """
        Wyszukuje pacjentów, których imię lub nazwisko zawiera podany fragment.

        Args:
            name_part (str): Fragment imienia lub nazwiska.

        Returns:
            pandas.DataFrame: Dane znalezionych pacjentów.
        """
        query = """
        SELECT * FROM Patient
        WHERE first_name LIKE ? OR last_name LIKE ?
        """
        param = f"%{name_part}%"
        return pd.read_sql(query, self.conn, params=(param, param))

    def find_doctor_by_specialization(self, specialization):
        """
        Wyszukuje lekarzy według fragmentu specjalizacji.

        Args:
            specialization (str): Fragment specjalizacji.

        Returns:
            pandas.DataFrame: Dane znalezionych lekarzy.
        """
        query = """
        SELECT * FROM Doctor
        WHERE specialization LIKE ?
        """
        return pd.read_sql(query, self.conn, params=(f"%{specialization}%",))

    def get_visits_by_patient(self, pesel):
        """
        Pobiera wizyty konkretnego pacjenta na podstawie numeru PESEL.

        Args:
            pesel (str): Numer PESEL pacjenta.

        Returns:
            pandas.DataFrame: Dane wizyt pacjenta z nazwiskami lekarzy.
        """
        query = """
        SELECT v.visit_id, v.visit_datetime, v.status, v.notes,
               d.first_name AS doctor_first_name, d.last_name AS doctor_last_name
        FROM Visit v
        JOIN Patient p ON v.patient_id = p.patient_id
        JOIN Doctor d ON v.doctor_id = d.doctor_id
        WHERE p.pesel = ?
        """
        return pd.read_sql(query, self.conn, params=(pesel,))

    def get_visits_by_doctor(self, doctor_last_name):
        """
        Pobiera wizyty lekarza na podstawie fragmentu jego nazwiska.

        Args:
            doctor_last_name (str): Fragment nazwiska lekarza.

        Returns:
            pandas.DataFrame: Dane wizyt z nazwiskami pacjentów.
        """
        query = """
        SELECT v.visit_id, v.visit_datetime, v.status, v.notes,
               p.first_name AS patient_first_name, p.last_name AS patient_last_name
        FROM Visit v
        JOIN Doctor d ON v.doctor_id = d.doctor_id
        JOIN Patient p ON v.patient_id = p.patient_id
        WHERE d.last_name LIKE ?
        """
        return pd.read_sql(query, self.conn, params=(f"%{doctor_last_name}%",))

    def get_visits_by_status(self, status):
        """
        Pobiera wizyty o określonym statusie.

        Args:
            status (str): Status wizyty.

        Returns:
            pandas.DataFrame: Dane wizyt o podanym statusie.
        """
        query = "SELECT * FROM Visit WHERE status = ?"
        return pd.read_sql(query, self.conn, params=(status,))
    
    def close(self):
        """
        Zamyka połączenie z bazą danych.
        """
        self.conn.close()

    # Backup bazy danych
    import shutil
    import os

    db_name = 'clinic.db'
    if os.path.exists(db_name):
    shutil.copy(db_name, db_name + '.bak')
    print(f"Kopia zapasowa zapisana jako: {db_name}.bak")
    else:
    print("Plik bazy danych nie istnieje.")
