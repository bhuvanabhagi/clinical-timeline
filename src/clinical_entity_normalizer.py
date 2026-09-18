import pandas as pd
import spacy
import re

# Load spaCy
nlp = spacy.load("en_core_web_sm")

# Load clinical notes
notes = pd.read_csv("data/synthetic_clinical_notes.csv")


# -----------------------------
# Clinical entity normalization
# -----------------------------

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

    # Person
    if spacy_label == "PERSON":
        return "Person"

    # Location
    if spacy_label in ["GPE", "LOC", "FAC"]:
        return "Location"

    # Identifiers
    if re.fullmatch(r"[A-Za-z0-9\-]+", text.strip()):
        if any(char.isdigit() for char in text):
            return "Identifier"

    # Keep original spaCy category if nothing matched
    return spacy_label


# -----------------------------
# Extract and normalize
# -----------------------------

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


# -----------------------------
# Test on first 10 notes
# -----------------------------

print("TOTAL NOTES:", len(notes))
print("=" * 80)

total_entities = 0

for index, note in notes.iterrows():

    entities = extract_normalized_entities(
        note["clean_note_text"]
    )

    total_entities += len(entities)

    if index < 10:

        print("\nNOTE:", index + 1)

        print("ENTITIES:")

        for entity in entities:

            print(
                "  -",
                entity["text"],
                "| spaCy:",
                entity["original_label"],
                "| Clinical:",
                entity["clinical_category"]
            )


print("\n" + "=" * 80)
print("TOTAL ENTITIES:", total_entities)