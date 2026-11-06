
# Fictional healthcare data
appointments = {
    101: 2,
    102: 3,
    103: 1
}

patient_statuses = {
    101: "Active",
    102: "Active",
    103: "Inactive"
}


def get_appointment_count(patient_id):
    if patient_id not in appointments:
        return {"error": "Patient not found"}

    return {"appointment_count": appointments[patient_id]}


def get_patient_status(patient_id):
    if patient_id not in patient_statuses:
        return {"error": "Patient not found"}

    return {"patient_status": patient_statuses[patient_id]}
