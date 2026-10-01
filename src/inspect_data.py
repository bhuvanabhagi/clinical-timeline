from dataloader import load_data


def inspect_data():

    patients, admissions, notes = load_data()

    print("\n" + "=" * 70)
    print("PATIENT DATA")
    print("=" * 70)

    print("Number of patients:", len(patients))
    print("\nColumns:")
    print(patients.columns.tolist())

    print("\nFirst 3 patients:")
    print(patients.head(3).to_string())


    print("\n" + "=" * 70)
    print("ADMISSION DATA")
    print("=" * 70)

    print("Number of admissions:", len(admissions))
    print("\nColumns:")
    print(admissions.columns.tolist())

    print("\nFirst 3 admissions:")
    print(admissions.head(3).to_string())


    print("\n" + "=" * 70)
    print("CLINICAL NOTES")
    print("=" * 70)

    print("Number of notes:", len(notes))
    print("\nColumns:")
    print(notes.columns.tolist())

    print("\nFirst 5 notes:")

    columns_to_show = [
        "clinical_note_id",
        "admission_id",
        "note_subject",
        "note_type",
        "creation_timestamp",
        "clean_note_text"
    ]

    available_columns = [
        col for col in columns_to_show
        if col in notes.columns
    ]

    print(
        notes[available_columns]
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    inspect_data()