from pathlib import Path
import pandas as pd



PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

EVENTS_PATH = PROCESSED_DIR / "clinical_events.csv"
NOTES_PATH = PROCESSED_DIR / "processed_clinical_notes.csv"

OUTPUT_PATH = PROCESSED_DIR / "temporal_events.csv"



def load_data():

    print("Loading clinical events...")

    events = pd.read_csv(EVENTS_PATH)

    print(f"Events loaded: {len(events)}")

    print("Loading clinical notes...")

    notes = pd.read_csv(NOTES_PATH)

    print(f"Notes loaded: {len(notes)}")

    return events, notes



def build_temporal_order():

    events, notes = load_data()

    print("\nEvent columns:")
    print(events.columns.tolist())

    print("\nNote columns:")
    print(notes.columns.tolist())


    # ========================================================
    # 1. MAKE SURE PERSON_ID EXISTS
    # ========================================================

    # Clinical events should already contain person_id.
    # If it does not, recover it from the clinical notes
    # using clinical_note_id.

    if "person_id" not in events.columns:

        print("\n'person_id' not found in events.")

        if "clinical_note_id" in events.columns and "person_id" in notes.columns:

            person_mapping = notes[
                ["clinical_note_id", "person_id"]
            ].drop_duplicates(
                subset=["clinical_note_id"]
            )

            events = events.merge(
                person_mapping,
                on="clinical_note_id",
                how="left"
            )

            print("person_id recovered from clinical notes.")

        else:
            raise ValueError(
                "Cannot create person_id because the required "
                "columns are missing."
            )


    # ========================================================
    # 2. MAKE SURE ADMISSION_ID EXISTS
    # ========================================================

    if "admission_id" not in events.columns:

        if "clinical_note_id" in events.columns and "admission_id" in notes.columns:

            admission_mapping = notes[
                ["clinical_note_id", "admission_id"]
            ].drop_duplicates(
                subset=["clinical_note_id"]
            )

            events = events.merge(
                admission_mapping,
                on="clinical_note_id",
                how="left"
            )

            print("admission_id recovered from clinical notes.")


    # ========================================================
    # 3. CREATE EVENT TIMESTAMP
    # ========================================================

    # The event extractor created event_date.
    # We convert it into a proper datetime value.

    if "event_date" in events.columns:

        events["event_timestamp"] = pd.to_datetime(
            events["event_date"],
            errors="coerce",
            dayfirst=True
        )

    else:

        events["event_timestamp"] = pd.NaT


    # ========================================================
    # 4. USE NOTE CREATION TIMESTAMP WHERE NECESSARY
    # ========================================================

    # Some events may not have a valid event_date.
    # We therefore use the clinical note creation time
    # as a fallback.

    if "clinical_note_id" in events.columns:

        note_times = notes[
            [
                "clinical_note_id",
                "creation_timestamp"
            ]
        ].drop_duplicates(
            subset=["clinical_note_id"]
        )

        events = events.merge(
            note_times,
            on="clinical_note_id",
            how="left",
            suffixes=("", "_note")
        )

        events["note_timestamp"] = pd.to_datetime(
            events["creation_timestamp"],
            errors="coerce",
            dayfirst=True
        )

        events["event_timestamp"] = events[
            "event_timestamp"
        ].fillna(
            events["note_timestamp"]
        )


    # ========================================================
    # 5. REMOVE TEMPORARY COLUMN
    # ========================================================

    if "note_timestamp" in events.columns:

        events = events.drop(
            columns=["note_timestamp"]
        )


    # ========================================================
    # 6. CHECK REQUIRED COLUMNS
    # ========================================================

    print("\nTimeline columns before sorting:")
    print(events.columns.tolist())

    if "person_id" not in events.columns:

        raise ValueError(
            "person_id is still missing after merging."
        )

    if "event_timestamp" not in events.columns:

        raise ValueError(
            "event_timestamp could not be created."
        )


    # ========================================================
    # 7. SORT EVENTS CHRONOLOGICALLY
    # ========================================================

    print("\nSorting events chronologically...")

    events = events.sort_values(
        by=[
            "person_id",
            "event_timestamp"
        ],
        ascending=True,
        na_position="last"
    ).reset_index(drop=True)


    # ========================================================
    # 8. CREATE EVENT ORDER
    # ========================================================

    # This gives every patient's events a chronological number.

    events["event_order"] = (
        events
        .groupby("person_id")
        .cumcount()
        + 1
    )


    # ========================================================
    # 9. CREATE READABLE DATE
    # ========================================================

    events["event_date_readable"] = events[
        "event_timestamp"
    ].dt.strftime(
        "%Y-%m-%d %H:%M"
    )


    # ========================================================
    # 10. SAVE RESULT
    # ========================================================

    events.to_csv(
        OUTPUT_PATH,
        index=False
    )


    # ========================================================
    # 11. DISPLAY RESULTS
    # ========================================================

    print("\n========================================")
    print("TEMPORAL ORDERING COMPLETED")
    print("========================================")

    print(f"Total events: {len(events)}")

    print(
        f"Patients represented: "
        f"{events['person_id'].nunique()}"
    )

    print(
        f"Events with valid timestamps: "
        f"{events['event_timestamp'].notna().sum()}"
    )

    print(
        f"Events without timestamps: "
        f"{events['event_timestamp'].isna().sum()}"
    )

    print("\nSample chronological events:")

    display_columns = [
        "person_id",
        "event_order",
        "event_timestamp",
        "event_type",
        "event_text"
    ]

    # Only display columns that actually exist
    display_columns = [
        column
        for column in display_columns
        if column in events.columns
    ]

    print(
        events[display_columns]
        .head(15)
        .to_string(index=False)
    )

    print("\nSaved to:")
    print(OUTPUT_PATH)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    build_temporal_order()
