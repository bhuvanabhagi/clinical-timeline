import pandas as pd
import spacy
import re

# Load spaCy
nlp = spacy.load("en_core_web_sm")

# Load clinical notes
notes = pd.read_csv("data/synthetic_clinical_notes.csv")


def normalize_entity(text, spacy_label):

    text_lower = text.lower().strip()

    # Diagnosis
    if re.search(r"\brcvs\b", text_lower):
        return "Diagnosis"

    # Symptoms
    if re.search(
        r"headache|pain|nausea|vomiting|dizziness|stiffness|weakness",
        text_lower
    ):
        return "Symptom"

    # Medications
    if re.search(
        r"nimodipine|amlodipine|paracetamol|ibuprofen|aspirin",
        text_lower
    ):
        return "Medication"

    # Investigations
    if re.search(
        r"\bct\b|ct scan|mri|mra|x-ray|ultrasound",
        text_lower
    ):
        return "Investigation"

    # Lab tests
    if re.search(
        r"blood test|bloods|fbc|crp|renal|lft|sodium|potassium|wbc",
        text_lower
    ):
        return "Lab Test"

    # Dates
    if spacy_label == "DATE":
        return "Date"

    # People
    if spacy_label == "PERSON":
        return "Person"

    # Locations
    if spacy_label in ["GPE", "LOC", "FAC"]:
        return "Location"

    # Identifiers
    if re.fullmatch(r"[A-Za-z0-9\-]+", text.strip()):
        if any(char.isdigit() for char in text):
            return "Identifier"

    return spacy_label


# Extract entities from one note
def extract_normalized_entities(text):

    doc = nlp(str(text))

    entities = []

    for ent in doc.ents:

        category = normalize_entity(
            ent.text,
            ent.label_
        )

        entities.append({
            "text": ent.text,
            "original_label": ent.label_,
            "clinical_category": category
        })

    return entities


# --------------------------------
# Process ALL 1602 clinical notes
# --------------------------------

all_entities = []

for _, note in notes.iterrows():

    entities = extract_normalized_entities(
        note["clean_note_text"]
    )

    for entity in entities:

        all_entities.append({
            "note_id": note["clinical_note_id"],
            "admission_id": note["admission_id"],
            "date": note["creation_timestamp"],
            "entity": entity["text"],
            "spacy_label": entity["original_label"],
            "clinical_category": entity["clinical_category"]
        })


# Convert to DataFrame
entities_df = pd.DataFrame(all_entities)


# Save results
entities_df.to_csv(
    "data/extracted_entities.csv",
    index=False
)


print("=" * 70)
print("ENTITY EXTRACTION COMPLETE")
print("=" * 70)

print("Notes processed:", len(notes))
print("Entities extracted:", len(entities_df))

print("\nSaved file:")
print("data/extracted_entities.csv")

print("\nEntity categories:")
print(
    entities_df["clinical_category"]
    .value_counts()
)