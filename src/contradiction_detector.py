import pandas as pd
import re

# Load data
patients = pd.read_csv("data/patients.csv")
admissions = pd.read_csv("data/admissions.csv")
notes = pd.read_csv("data/synthetic_clinical_notes.csv")


def build_case(person_id):

    patient_admissions = admissions[
        admissions["patient_id"] == person_id
    ]

    admission_ids = patient_admissions["admission_id"].tolist()

    case_notes = notes[
        notes["admission_id"].isin(admission_ids)
    ].copy()

    case_notes["creation_timestamp"] = pd.to_datetime(
        case_notes["creation_timestamp"],
        dayfirst=True,
        errors="coerce"
    )

    return case_notes.sort_values("creation_timestamp")


def extract_medication_info(text):

    medications = []

    text = str(text)

    # Look for nimodipine dosage
    matches = re.findall(
        r"nimodipine\s+(\d+)\s*mg",
        text,
        re.IGNORECASE
    )

    for dose in matches:
        medications.append({
            "medication": "Nimodipine",
            "dose": int(dose)
        })

    return medications


def detect_changes(case_notes):

    findings = []

    previous_medications = {}

    for _, note in case_notes.iterrows():

        medications = extract_medication_info(
            note["clean_note_text"]
        )

        for medication in medications:

            name = medication["medication"]
            dose = medication["dose"]

            if name in previous_medications:

                previous_dose = previous_medications[name]["dose"]

                if dose != previous_dose:

                    findings.append({
                        "type": "Potential medication change",
                        "medication": name,
                        "previous_dose": previous_dose,
                        "new_dose": dose,
                        "date": note["creation_timestamp"]
                    })

            previous_medications[name] = {
                "dose": dose,
                "date": note["creation_timestamp"]
            }

    return findings


# ---------------------------------------
# TEST
# ---------------------------------------

person_id = patients.iloc[0]["person_id"]

case_notes = build_case(person_id)

findings = detect_changes(case_notes)

print("CASE ID:", person_id)
print("=" * 80)

print("\nPOTENTIAL CHANGES / INCONSISTENCIES")
print("-" * 80)

if findings:

    for finding in findings:

        print(
            "\nType:",
            finding["type"]
        )

        print(
            "Medication:",
            finding["medication"]
        )

        print(
            "Previous dose:",
            finding["previous_dose"],
            "mg"
        )

        print(
            "New dose:",
            finding["new_dose"],
            "mg"
        )

        print(
            "Date:",
            finding["date"]
        )

else:

    print("No potential changes detected.")