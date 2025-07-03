Projektowanie bazy danych - modele
==================================================


:author: Mateusz Brokos, Szymon Blatkowski

Wprowadzenie
------------

Prowadzący: Piotr Czaja  

Kurs: Bazy Danych 1

Celem tego raportu jest przedstawienie pełnego procesu projektowania i optymalizacji bazy danych wspierającej rejestrację oraz obsługę wizyt lekarskich w przychodni.




Model Konceptualny
------------------

.. code-block:: none

           +-----------+      1       *      +-----------+
           |  Pacjent  |---------------------|   Wizyta  |
           +-----------+                     +-----------+
           | PK: id    |                     | PK: id    |
           +-----------+                     +-----------+
                ^  \
                |   \
         umawia się   \
           (1..*)      v
           +-----------+
           |  Lekarz   |
           +-----------+
           | PK: id    |
           +-----------+

Legenda
  • Pacjent – może umawiać wiele wizyt (1..*)  
  • Wizyta – dotyczy jednego pacjenta i jednego lekarza  
  • Lekarz – może prowadzić wiele wizyt (1..*)



Model Logiczny
------------------

.. code-block:: none

  +-------------+       +------------+       +-----------+
  |   Pacjent   |       |   Lekarz   |       |   Wizyta  |
  +-------------+       +------------+       +-----------+
  | PK: patient_id    | PK: doctor_id   | PK: visit_id    |
  | first_name        | first_name      | patient_id (FK) |
  | last_name         | last_name       | doctor_id  (FK) |
  | pesel             | specialization_id (FK)| visit_datetime |
  | birth_date        +------------+---+| status         |
  | email             | specialization_id → Specialization | notes |
  | phone             |                |
  +-------------+     +--------------+    

Dodatkowa encja:

.. code-block:: none

  +--------------------+
  |  Specialization    |
  +--------------------+
  | PK: specialization_id |
  | name               |
  +--------------------+

Relacje
  • Visit.patient_id → Patient.patient_id (1:N)  
  • Visit.doctor_id  → Doctor.doctor_id  (1:N)  
  • Doctor.specialization_id → Specialization.specialization_id (1:N)

Model Fizyczny
------------------

.. code-block:: sql

    CREATE TABLE Specialization (
        specialization_id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE
    );

    CREATE TABLE Doctor (
        doctor_id SERIAL PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        license_number VARCHAR(20) UNIQUE NOT NULL,
        specialization_id INTEGER
            REFERENCES Specialization(specialization_id)
            ON UPDATE CASCADE ON DELETE SET NULL
    );

    CREATE TABLE Patient (
        patient_id SERIAL PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        pesel CHAR(11) UNIQUE NOT NULL,
        birth_date DATE NOT NULL,
        email VARCHAR(100),
        phone VARCHAR(20)
    );

    CREATE TABLE Visit (
        visit_id SERIAL PRIMARY KEY,
        patient_id INTEGER NOT NULL
            REFERENCES Patient(patient_id)
            ON UPDATE CASCADE ON DELETE CASCADE,
        doctor_id INTEGER NOT NULL
            REFERENCES Doctor(doctor_id)
            ON UPDATE CASCADE ON DELETE CASCADE,
        visit_datetime TIMESTAMP NOT NULL,
        status VARCHAR(20) NOT NULL,
        notes TEXT
    );

Przykładowe rekordy
--------------------------

Tabela Specialization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - specialization_id
     - name
   * - 1
     - Internista
   * - 2
     - Pediatra
   * - 3
     - Kardiolog

Tabela Doctor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - doctor_id
     - first_name
     - last_name
     - license_number
     - specialization_id
   * - 1
     - Anna
     - Nowak
     - PWZ123456
     - 1
   * - 2
     - Paweł
     - Kowalski
     - PWZ654321
     - 2

Tabela Patient
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - patient_id
     - first_name
     - last_name
     - pesel
     - birth_date
     - email
     - phone
   * - 1
     - Maria
     - Wiśniewska
     - 90010112345
     - 1990-01-01
     - maria@example.com
     - +48123123123
   * - 2
     - Tomasz
     - Dąbrowski
     - 85050554321
     - 1985-05-05
     - tomasz@example.com
     - +48987654321

Tabela Visit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - visit_id
     - patient_id
     - doctor_id
     - visit_datetime
     - status
     - notes
   * - 1
     - 1
     - 1
     - 2025-06-01 10:30:00
     - zaplanowana
     - "Pierwsza wizyta"
   * - 2
     - 2
     - 2
     - 2025-06-02 14:00:00
     - odbyta
     - "Kontrola po leczeniu"
