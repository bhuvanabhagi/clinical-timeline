import pandas as pd

patients = pd.read_csv("data/patients.csv")
admissions = pd.read_csv("data/admissions.csv")
notes = pd.read_csv("data/synthetic_clinical_notes.csv")

print("PATIENTS")
print("Number of patients:", len(patients))
print("Columns:", patients.columns.tolist())

print("\nADMISSIONS")
print("Number of admissions:", len(admissions))
print("Columns:", admissions.columns.tolist())

print("\nCLINICAL NOTES")
print("Number of notes:", len(notes))
print("Columns:", notes.columns.tolist())