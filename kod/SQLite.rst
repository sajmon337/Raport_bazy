SQLite – skrypty obsługi bazy i raportowania
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import sqlite3
    import pandas as pd
    import matplotlib.pyplot as plt
    import time
    import shutil
    import os

    # Pomiar czasu zapytań
    def measure_sqlite_queries(db_path, queries):
        """
        Mierzy czas wykonania podanych zapytań SQL na bazie SQLite i wypisuje wyniki.
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

    # Generowanie raportu i wykresów
    def generate_reports(db_path="clinic.db"):
        """
        Generuje raporty i wizualizacje na podstawie danych kliniki z bazy SQLite.
        """
        conn = sqlite3.connect(db_path)
        patients = pd.read_sql_query("SELECT * FROM Patient", conn)
        doctors = pd.read_sql_query("SELECT * FROM Doctor", conn)
        visits = pd.read_sql_query("SELECT * FROM Visit", conn)

        visits_full = visits.merge(doctors, on="doctor_id", suffixes=('', '_doctor')) \
                            .merge(patients, on="patient_id", suffixes=('', '_patient'))

        print("\nLiczba pacjentów:", len(patients))
        print("Liczba lekarzy:", len(doctors))
        print("Liczba wizyt:", len(visits))

        visits_per_doctor = visits_full.groupby(["first_name", "last_name"]).size().sort_values(ascending=False)
        print("\nLiczba wizyt wg lekarzy:")
        print(visits_per_doctor)

        status_counts = visits["status"].value_counts()
        print("\nLiczba wizyt wg statusu:")
        print(status_counts)

        visits["visit_month"] = pd.to_datetime(visits["visit_datetime"]).dt.to_period("M")
        visits_per_month = visits["visit_month"].value_counts().sort_index()

        plt.figure(figsize=(10, 5))
        visits_per_doctor.plot(kind="bar", title="Liczba wizyt wg lekarzy")
        plt.xlabel("Lekarz")
        plt.ylabel("Liczba wizyt")
        plt.tight_layout()
        plt.show()

        plt.figure(figsize=(10, 5))
        visits_per_month.plot(kind="line", marker="o", title="Wizyty w czasie")
        plt.xlabel("Miesiąc")
        plt.ylabel("Liczba wizyt")
        plt.tight_layout()
        plt.show()

        conn.close()

    generate_reports()

    # Reset bazy danych
    def reset_database():
        conn = sqlite3.connect("clinic.db")
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS Visit;")
        cursor.execute("DROP TABLE IF EXISTS Patient;")
        cursor.execute("DROP TABLE IF EXISTS Doctor;")
        conn.commit()
        conn.close()
        print("Baza danych została zresetowana.")

    # Klasa do zapytań
    class ClinicDB:
        """
        Klasa do obsługi bazy danych kliniki SQLite.
        """
        def __init__(self, db_path='clinic.db'):
            self.conn = sqlite3.connect(db_path)

        def get_all_patients(self):
            return pd.read_sql("SELECT * FROM Patient", self.conn)

        def get_all_doctors(self):
            return pd.read_sql("SELECT * FROM Doctor", self.conn)

        def get_all_visits(self):
            return pd.read_sql("SELECT * FROM Visit", self.conn)

        def find_patients_by_name(self, name_part):
            query = """
            SELECT * FROM Patient
            WHERE first_name LIKE ? OR last_name LIKE ?
            """
            param = f"%{name_part}%"
            return pd.read_sql(query, self.conn, params=(param, param))

        def find_doctor_by_specialization(self, specialization):
            query = """
            SELECT * FROM Doctor
            WHERE specialization LIKE ?
            """
            return pd.read_sql(query, self.conn, params=(f"%{specialization}%",))

        def get_visits_by_patient(self, pesel):
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
            query = "SELECT * FROM Visit WHERE status = ?"
            return pd.read_sql(query, self.conn, params=(status,))

        def close(self):
            self.conn.close()

    # Backup bazy
    db_name = 'clinic.db'
    if os.path.exists(db_name):
        shutil.copy(db_name, db_name + '.bak')
        print(f"Kopia zapasowa zapisana jako: {db_name}.bak")
    else:
        print("Plik bazy danych nie istnieje.")
