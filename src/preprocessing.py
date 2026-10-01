from pathlib import Path
import pandas as pd

from dataloader import load_data


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Output folder
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def preprocess_notes():

    # Load raw data
    patients, admissions, notes = load_data()

    print("Raw clinical notes:", len(notes))

    # Keep only the columns we need for the timeline pipeline
    required_columns = [
        "clinical_note_id",
        "admission_id",
        "person_id",
        "note_subject",
        "note_type",
        "creation_timestamp",
        "clean_note_text"
    ]

    notes = notes[required_columns].copy()

    # Remove notes with no text
    notes = notes.dropna(subset=["clean_note_text"])

    # Convert timestamps to datetime
    notes["creation_timestamp"] = pd.to_datetime(
        notes["creation_timestamp"],
        dayfirst=True,
        errors="coerce"
    )

    # Remove completely empty text
    notes["clean_note_text"] = (
        notes["clean_note_text"]
        .astype(str)
        .str.strip()
    )

    notes = notes[
        notes["clean_note_text"].str.len() > 0
    ]

    # Remove exact duplicate notes
    notes = notes.drop_duplicates(
        subset=["clinical_note_id"]
    )

    # Sort chronologically
    notes = notes.sort_values(
        by=["person_id", "creation_timestamp"]
    )

    # Save processed data
    output_path = PROCESSED_DIR / "processed_clinical_notes.csv"

    notes.to_csv(
        output_path,
        index=False
    )

    print("\nPreprocessing completed.")
    print("Processed notes:", len(notes))
    print("Saved to:")
    print(output_path)


if __name__ == "__main__":
    preprocess_notes()