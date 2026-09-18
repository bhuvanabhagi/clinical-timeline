import pandas as pd

patients = pd.read_csv("data/patients.csv")
admissions = pd.read_csv("data/admissions.csv")
notes = pd.read_csv("data/synthetic_clinical_notes.csv")


def build_timeline(person_id):

    # Find patient's admissions
    patient_admissions = admissions[
        admissions["patient_id"] == person_id
    ]

    admission_ids = patient_admissions["admission_id"].tolist()

    # Get all notes for this case
    case_notes = notes[
        notes["admission_id"].isin(admission_ids)
    ].copy()

    # Convert dates
    case_notes["creation_timestamp"] = pd.to_datetime(
        case_notes["creation_timestamp"],
        dayfirst=True
    )

    # Sort chronologically
    case_notes = case_notes.sort_values("creation_timestamp")

    # Create timeline
    timeline = []

    for _, note in case_notes.iterrows():

        event = {
            "date": note["creation_timestamp"],
            "note_type": note["note_type"],
            "subject": note["note_subject"],
            "text": note["clean_note_text"]
        }

        timeline.append(event)

    return timeline


# Test with first patient
person_id = patients.iloc[0]["person_id"]

timeline = build_timeline(person_id)

print("CASE TIMELINE")
print("=" * 70)

for event in timeline:

    print("\nDATE:", event["date"])
    print("TYPE:", event["note_type"])
    print("SUBJECT:", event["subject"])
    print("-" * 70)