Analiza Bazy danych i optymalizacja zapytań
==============================================

Analiza normalizacji
--------------------

Model logiczny jest w 3NF:
- Każda tabela ma pojedynczy klucz główny.
- Atrybuty niekluczowe zależą wyłącznie od klucza.
- Brak zależności przechodnich (specjalizacja wydzielona osobno).

Potencjalne problemy wydajnościowe
----------------------------------

- Brak indeksów poza kluczami głównymi.
- Częste filtrowanie po `visit_datetime` i `doctor_id` wymaga skanów.

Strategie optymalizacji
-----------------------

**1. Indeksy**

.. code-block:: sql

    CREATE INDEX idx_visit_patient    ON Visit(patient_id);
    CREATE INDEX idx_visit_doctor     ON Visit(doctor_id);
    CREATE INDEX idx_visit_date       ON Visit(visit_datetime);
    CREATE INDEX idx_visit_doc_date   ON Visit(doctor_id, visit_datetime);

**2. Partycjonowanie**

- Partycjonuj tabelę `Visit` według miesiąca `visit_datetime`.

**3. Widoki materializowane**

.. code-block:: sql

    CREATE MATERIALIZED VIEW mv_daily_visits AS
    SELECT DATE(visit_datetime) AS day,
           doctor_id,
           COUNT(*) AS total
    FROM Visit
    GROUP BY day, doctor_id;

**4. Optymalizacja zapytań**

- Używaj `EXPLAIN (ANALYZE, BUFFERS)` do analizy planów.
- Unikaj `SELECT *`, wybieraj konkretne kolumny.

Przykład optymalizacji:

.. code-block:: sql

    -- Przed optymalizacją:
    SELECT p.first_name, p.last_name, COUNT(*) AS cnt
    FROM Visit v
    JOIN Patient p ON v.patient_id = p.patient_id
    WHERE v.visit_datetime BETWEEN '2025-06-01' AND '2025-12-31'
    GROUP BY p.first_name, p.last_name;

    -- Po (z indeksem na visit_datetime):
    EXPLAIN ANALYZE
    SELECT p.first_name, p.last_name, COUNT(*) AS cnt
    FROM Visit v
    JOIN Patient p ON v.patient_id = p.patient_id
    WHERE v.visit_datetime BETWEEN '2025-06-01' AND '2025-12-31'
    GROUP BY p.first_name, p.last_name
    LIMIT 10;

Prezentacja skryptów wspomagających
---------------------------------------------


.. code-block:: python

    import sqlite3
    import pandas as pd

    class ClinicDB:
        """
        Klasa do obsługi bazy danych kliniki SQLite z wykorzystaniem Pandas.

        Atrybuty:
            conn (sqlite3.Connection): Połączenie z bazą.
        """

        def __init__(self, db_path='clinic.db'):
            """
            Inicjalizuje połączenie z bazą.
            """
            self.conn = sqlite3.connect(db_path)

        def get_all_patients(self):
            """
            Zwraca DataFrame ze wszystkimi pacjentami.
            """
            return pd.read_sql("SELECT * FROM Patient", self.conn)

        def find_patients_by_name(self, name_part):
            """
            Wyszukuje pacjentów po fragmencie imienia/nazwiska.
            """
            q = "SELECT * FROM Patient WHERE first_name LIKE ? OR last_name LIKE ?"
            return pd.read_sql(q, self.conn, params=(f"%{name_part}%",)*2)

    .. code-block:: python

        import sqlite3
        import time

        def measure_sqlite_queries(db_path, queries):
            """
            Mierzy czas wykonania zapytań SQL na SQLite.
            """
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            for q in queries:
                t0 = time.time()
                cur.execute(q)
                rows = cur.fetchall()
                print(f"Czas: {time.time()-t0:.4f}s, wierszy: {len(rows)}")
            conn.close()

    .. code-block:: python

        import sqlite3
        import pandas as pd
        import matplotlib.pyplot as plt

        def generate_reports(db_path="clinic.db"):
            """
            Generuje raporty i wykresy z danych kliniki.
            """
            conn = sqlite3.connect(db_path)
            df = pd.read_sql("SELECT * FROM Visit", conn)
            # ... wykresy ...
            conn.close()

Wnioski
-------

- Model w 3NF minimalizuje redundancję i ułatwia utrzymanie.  
- Indeksy i widoki materializowane znacząco przyspieszą zapytania analityczne.  
- Regularne analizowanie planów (`EXPLAIN ANALYZE`) pozwoli wychwycić wąskie gardła.
