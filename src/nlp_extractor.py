import pandas as pd
import spacy

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Load dataset
notes = pd.read_csv("data/synthetic_clinical_notes.csv")


def extract_entities(text):

    doc = nlp(str(text))

    entities = []

    for ent in doc.ents:
        entities.append({
            "text": ent.text,
            "label": ent.label_
        })

    return entities


# ---------------------------------------
# TEST ON ALL NOTES
# ---------------------------------------

print("TOTAL NOTES:", len(notes))
print("=" * 80)

total_entities = 0

for index, note in notes.iterrows():

    entities = extract_entities(note["clean_note_text"])

    total_entities += len(entities)

    if index < 10:
        print("\nNOTE:", index + 1)
        print("TEXT:", note["clean_note_text"][:200])
        print("ENTITIES:")

        for entity in entities:
            print(
                "  -",
                entity["text"],
                "|",
                entity["label"]
            )

print("\n" + "=" * 80)
print("TOTAL ENTITIES EXTRACTED:", total_entities)