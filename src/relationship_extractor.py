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


def extract_relationships(note_text):

    relationships = []

    text = str(note_text)

    # MRI/MRA → confirms → RCVS
    if re.search(r"MRI|MRA", text, re.IGNORECASE) and \
       re.search(r"confirm|confirmed", text, re.IGNORECASE) and \
       re.search(r"RCVS", text, re.IGNORECASE):

        relationships.append({
            "entity_1": "MRI/MRA",
            "relationship": "confirmed",
            "entity_2": "RCVS"
        })

    # Nimodipine → treatment for → RCVS
    if re.search(r"nimodipine", text, re.IGNORECASE) and \
       re.search(r"RCVS", text, re.IGNORECASE):

        relationships.append({
            "entity_1": "Nimodipine",
            "relationship": "treatment_for",
            "entity_2": "RCVS"
        })

    # Headache → associated with → RCVS
    if re.search(r"headache", text, re.IGNORECASE) and \
       re.search(r"RCVS", text, re.IGNORECASE):

        relationships.append({
            "entity_1": "Headache",
            "relationship": "associated_with",
            "entity_2": "RCVS"
        })

    # CT → investigation for → Headache
    if re.search(r"\bCT\b|CT scan|CT head", text, re.IGNORECASE) and \
       re.search(r"headache", text, re.IGNORECASE):

        relationships.append({
            "entity_1": "CT scan",
            "relationship": "investigated",
            "entity_2": "Headache"
        })

    return relationships


# ---------------------------------------
# TEST
# ---------------------------------------

person_id = patients.iloc[0]["person_id"]

case_notes = build_case(person_id)

print("CASE ID:", person_id)
print("=" * 80)

for _, note in case_notes.iterrows():

    relationships = extract_relationships(
        note["clean_note_text"]
    )

    if relationships:

        print("\nDATE:", note["creation_timestamp"])
        print("NOTE:", note["note_type"])

        print("RELATIONSHIPS:")

        for relation in relationships:

            print(
                "  ",
                relation["entity_1"],
                "→",
                relation["relationship"],
                "→",
                relation["entity_2"]
            )