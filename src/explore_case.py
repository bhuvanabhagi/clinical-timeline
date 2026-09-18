import pandas as pd

patients = pd.read_csv("data/patients.csv")
admissions = pd.read_csv("data/admissions.csv")
notes = pd.read_csv("data/synthetic_clinical_notes.csv")

# Select the first patient
patient_id = patients.iloc[0]["person_id"]

print("PATIENT ID:", patient_id)

# Find this patient's admission
patient_admissions = admissions[
    admissions["patient_id"] == patient_id
]

print("\nADMISSIONS:")
print(
    patient_admissions[
        ["admission_id", "admission_timestamp", "admission_title", "ward"]
    ].to_string(index=False)
)

# Get admission IDs
admission_ids = patient_admissions["admission_id"].tolist()

# Find clinical notes for these admissions
patient_notes = notes[
    notes["admission_id"].isin(admission_ids)
].sort_values("creation_timestamp")

print("\nNUMBER OF CLINICAL NOTES:", len(patient_notes))

print("\nCLINICAL NOTES:\n")

for _, note in patient_notes.iterrows():
    print("=" * 80)
    print("NOTE ID:", note["clinical_note_id"])
    print("DATE:", note["creation_timestamp"])
    print("TYPE:", note["note_type"])
    print("SUBJECT:", note["note_subject"])
    print("\nTEXT:")
    print(note["clean_note_text"])