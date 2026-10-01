from pathlib import Path
import pandas as pd


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

TEMPORAL_EVENTS_PATH = PROCESSED_DIR / "temporal_events.csv"
OUTPUT_PATH = PROCESSED_DIR / "patient_timelines.csv"


# ============================================================
# BUILD PATIENT TIMELINES
# ============================================================

def build_patient_timelines():

    print("Loading temporal events...")

    events = pd.read_csv(TEMPORAL_EVENTS_PATH)

    print(f"Events loaded: {len(events)}")

    # Convert timestamp
    events["event_timestamp"] = pd.to_datetime(
        events["event_timestamp"],
        errors="coerce"
    )

    # Sort chronologically for each patient
    events = events.sort_values(
        by=["person_id", "event_timestamp"],
        ascending=True
    ).reset_index(drop=True)

    # Create event order for each patient
    events["event_order"] = (
        events.groupby("person_id").cumcount() + 1
    )

    # Create a readable timeline description
    events["timeline_entry"] = (
        events["event_timestamp"].astype(str)
        + " | "
        + events["event_type"].fillna("Unknown")
        + " | "
        + events["event_text"].fillna("")
    )

    # Select useful columns
    timeline = events[
        [
            "person_id",
            "admission_id",
            "clinical_note_id",
            "event_order",
            "event_timestamp",
            "event_type",
            "event_text",
            "timeline_entry"
        ]
    ]

    # Save
    timeline.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\n========================================")
    print("PATIENT TIMELINE BUILD COMPLETED")
    print("========================================")

    print(f"Total timeline events: {len(timeline)}")
    print(f"Patients represented: {timeline['person_id'].nunique()}")

    print("\nSample patient timeline:")

    first_patient = timeline["person_id"].dropna().iloc[0]

    sample = timeline[
        timeline["person_id"] == first_patient
    ][
        [
            "event_order",
            "event_timestamp",
            "event_type",
            "event_text"
        ]
    ].head(10)

    print(sample.to_string(index=False))

    print("\nSaved to:")
    print(OUTPUT_PATH)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    build_patient_timelines()