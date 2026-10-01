from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TIMELINE_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "patient_timelines.csv"
)


def get_patient_timeline(person_id):

    timeline = pd.read_csv(TIMELINE_PATH)

    patient_timeline = timeline[
        timeline["person_id"] == person_id
    ].copy()

    patient_timeline = patient_timeline.sort_values(
        by="event_order"
    )

    return patient_timeline


if __name__ == "__main__":

    timeline = pd.read_csv(TIMELINE_PATH)

    # Take the first patient available in the dataset
    person_id = timeline["person_id"].dropna().iloc[0]

    print("Patient ID:")
    print(person_id)

    print("\nPatient Timeline:")
    print("=" * 60)

    patient_timeline = get_patient_timeline(person_id)

    print(
        patient_timeline[
            [
                "event_order",
                "event_timestamp",
                "event_type",
                "event_text"
            ]
        ].to_string(index=False)
    )