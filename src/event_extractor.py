import pandas as pd
import re

# Load data
patients = pd.read_csv("data/patients.csv")
admissions = pd.read_csv("data/admissions.csv")
notes = pd.read_csv("data/synthetic_clinical_notes.csv")


def build_case(person_id):

    # Find patient's admission
    patient_admissions = admissions[
        admissions["patient_id"] == person_id
    ]

    admission_ids = patient_admissions["admission_id"].tolist()

    # Find notes belonging to this case
    case_notes = notes[
        notes["admission_id"].isin(admission_ids)
    ].copy()

    # Convert dates
    case_notes["creation_timestamp"] = pd.to_datetime(
        case_notes["creation_timestamp"],
        dayfirst=True,
        errors="coerce"
    )

    # Sort by date
    case_notes = case_notes.sort_values("creation_timestamp")

    return case_notes


def extract_events(note_text):

    events = []

    text = str(note_text)

    # Event 1: Headache / symptom
    if re.search(r"headache", text, re.IGNORECASE):
        events.append({
            "event_type": "Symptom",
            "event": "Headache",
            "evidence": "headache"
        })

    # Event 2: CT scan
    if re.search(r"\bCT\b|CT scan|CT head", text, re.IGNORECASE):
        events.append({
            "event_type": "Investigation",
            "event": "CT scan",
            "evidence": "CT"
        })

    # Event 3: MRI/MRA
    if re.search(r"MRI|MRA", text, re.IGNORECASE):
        events.append({
            "event_type": "Investigation",
            "event": "MRI/MRA",
            "evidence": "MRI/MRA"
        })

    # Event 4: Diagnosis
    if re.search(r"RCVS", text, re.IGNORECASE):
        events.append({
            "event_type": "Diagnosis",
            "event": "RCVS",
            "evidence": "RCVS"
        })

    # Event 5: Medication
    if re.search(r"nimodipine", text, re.IGNORECASE):
        events.append({
            "event_type": "Treatment",
            "event": "Nimodipine",
            "evidence": "nimodipine"
        })

    # Event 6: Discharge
    if re.search(r"discharge|discharged", text, re.IGNORECASE):
        events.append({
            "event_type": "Disposition",
            "event": "Discharge",
            "evidence": "discharge"
        })

    return events


# ---------------------------------------
# TEST EVENT EXTRACTION
# ---------------------------------------

person_id = patients.iloc[0]["person_id"]

case_notes = build_case(person_id)

print("CASE ID:", person_id)
print("=" * 80)

for _, note in case_notes.iterrows():

    events = extract_events(note["clean_note_text"])

    print("\nDATE:", note["creation_timestamp"])
    print("NOTE TYPE:", note["note_type"])

    if events:

        print("EVENTS:")

        for event in events:
            print(
                "  -",
                event["event_type"],
                ":",
                event["event"]
            )

    else:
        print("EVENTS: None")