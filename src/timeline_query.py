
from pathlib import Path
import pandas as pd

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]

TIMELINE_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "patient_timelines.csv"
)


def load_timeline():
    """Load the processed patient timeline."""

    print("Loading patient timelines...")

    if not TIMELINE_PATH.exists():
        raise FileNotFoundError(
            f"Timeline file not found: {TIMELINE_PATH}"
        )

    timeline = pd.read_csv(TIMELINE_PATH)

    required_columns = [
        "person_id",
        "event_order",
        "event_timestamp",
        "event_type",
        "event_text",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in timeline.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns in CSV: {missing_columns}"
        )

    print(f"Total events loaded: {len(timeline)}")

    return timeline


def get_patient_timeline(person_id, timeline=None):
    """Get chronological events for one patient."""

    if timeline is None:
        timeline = load_timeline()

    patient_timeline = timeline[
        timeline["person_id"].astype(str) == str(person_id)
    ].copy()

    if patient_timeline.empty:
        return patient_timeline

    # Parse timestamps using day-first format where applicable.
    patient_timeline["event_timestamp"] = pd.to_datetime(
        patient_timeline["event_timestamp"],
        errors="coerce",
        dayfirst=True,
    )

    # Sort by timestamp, then event order.
    patient_timeline = patient_timeline.sort_values(
        by=["event_timestamp", "event_order"],
        na_position="last",
    )

    return patient_timeline


def display_patient_timeline(person_id, timeline):
    """Display one patient's clinical journey."""

    patient_timeline = get_patient_timeline(
        person_id,
        timeline,
    )

    print("\n" + "=" * 70)
    print("PATIENT CLINICAL JOURNEY")
    print("=" * 70)
    print(f"Patient ID: {person_id}")

    if patient_timeline.empty:
        print("No events found for this patient.")
        return

    print(f"Total events: {len(patient_timeline)}")

    for _, event in patient_timeline.iterrows():

        timestamp = event["event_timestamp"]

        if pd.notna(timestamp):
            timestamp_text = timestamp.strftime(
                "%d %b %Y, %H:%M"
            )
        else:
            timestamp_text = "Date unavailable"

        event_type = str(event["event_type"])

        event_text = str(event["event_text"])

        print(f"\n[{timestamp_text}]")
        print(f"Event: {event_type}")
        print(f"Details: {event_text}")
        print("-" * 60)


def main():
    """Allow the user to select a patient."""

    try:
        timeline = load_timeline()

    except (FileNotFoundError, ValueError, pd.errors.ParserError) as error:
        print(f"Error loading timeline: {error}")
        return

    patient_ids = sorted(
        timeline["person_id"]
        .dropna()
        .astype(str)
        .unique()
    )

    if not patient_ids:
        print("No patients found.")
        return

    print("\nCLINICAL TIMELINE EXPLORER")
    print("=" * 40)
    print(f"Patients available: {len(patient_ids)}")

    for index, patient_id in enumerate(
        patient_ids,
        start=1,
    ):
        print(f"{index}. {patient_id}")

    while True:

        choice = input(
            "\nEnter patient number (or Q to quit): "
        ).strip()

        if choice.lower() == "q":
            print("Exiting timeline explorer.")
            break

        if not choice.isdigit():
            print("Please enter a valid number.")
            continue

        patient_number = int(choice)

        if not 1 <= patient_number <= len(patient_ids):
            print("Invalid patient number. Try again.")
            continue

        selected_patient = patient_ids[patient_number - 1]

        display_patient_timeline(
            selected_patient,
            timeline,
        )


if __name__ == "__main__":
    main()
