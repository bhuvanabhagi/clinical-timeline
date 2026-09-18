import pandas as pd

# Load extracted entities
entities = pd.read_csv("data/extracted_entities.csv")

# Clinical categories we actually need
useful_categories = [
    "Diagnosis",
    "Symptom",
    "Medication",
    "Investigation",
    "Lab Test",
    "Date",
    "TIME",
    "Location",
    "Person",
    "Identifier"
]

# Keep only useful clinical entities
clinical_entities = entities[
    entities["clinical_category"].isin(useful_categories)
].copy()

# Save the filtered data
clinical_entities.to_csv(
    "data/clinical_entities.csv",
    index=False
)

print("=" * 70)
print("CLINICAL ENTITY FILTERING COMPLETE")
print("=" * 70)

print("Original entities:", len(entities))
print("Clinical entities:", len(clinical_entities))

print("\nCategories kept:")
print(
    clinical_entities["clinical_category"]
    .value_counts()
)

print("\nSaved file:")
print("data/clinical_entities.csv")