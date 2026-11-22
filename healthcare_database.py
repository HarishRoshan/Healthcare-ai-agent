import sqlite3

connection = sqlite3.connect("healthcare.db")

cursor = connection.cursor()

# Create patients table
cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    patient_id INTEGER PRIMARY KEY,
    appointment_count INTEGER,
    patient_status TEXT
)
""")

connection.commit()

print("Patients table created successfully!")

# Insert fictional patient records
patients = [
    (101, 2, "Active"),
    (102, 3, "Active"),
    (103, 1, "Inactive")
]

cursor.executemany("""
INSERT OR IGNORE INTO patients
(patient_id, appointment_count, patient_status)
VALUES (?, ?, ?)
""", patients)

connection.commit()

print("Patient records inserted successfully!")
# Retrieve all patient records
cursor.execute("SELECT * FROM patients")

records = cursor.fetchall()

for patient in records:
    print(patient)
# Find a specific patient
patient_id = 102

cursor.execute(
    "SELECT * FROM patients WHERE patient_id = ?",
    (patient_id,)
)

patient = cursor.fetchone()

print("Selected patient:", patient)
# Update patient 102's appointment count
patient_id = 102
new_count = 4

cursor.execute(
    """
    UPDATE patients
    SET appointment_count = ?
    WHERE patient_id = ?
    """,
    (new_count, patient_id)
)

connection.commit()

print("Patient appointment count updated!")

# Verify the updated record
cursor.execute(
    "SELECT * FROM patients WHERE patient_id = ?",
    (patient_id,)
)

updated_patient = cursor.fetchone()

print("Updated patient:", updated_patient)

connection.close()