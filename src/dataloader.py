from pathlib import Path
import pandas as pd


# Project root = clinical-timeline/
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Dataset paths
PATIENTS_PATH = PROJECT_ROOT / "data" / "raw" / "patients.csv"
ADMISSIONS_PATH = PROJECT_ROOT / "data" / "raw" / "admissions.csv"
NOTES_PATH = PROJECT_ROOT / "data" / "raw" / "synthetic_clinical_notes.csv"


def load_data():
    patients = pd.read_csv(PATIENTS_PATH)
    admissions = pd.read_csv(ADMISSIONS_PATH)
    notes = pd.read_csv(NOTES_PATH)

    return patients, admissions, notes


if __name__ == "__main__":

    patients, admissions, notes = load_data()

    print("\n========== PATIENTS ==========")
    print("Shape:", patients.shape)
    print("Columns:", patients.columns.tolist())

    print("\n========== ADMISSIONS ==========")
    print("Shape:", admissions.shape)
    print("Columns:", admissions.columns.tolist())

    print("\n========== CLINICAL NOTES ==========")
    print("Shape:", notes.shape)
    print("Columns:", notes.columns.tolist())