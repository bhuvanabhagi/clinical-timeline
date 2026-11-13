
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "clinical_events.csv"
)

events = pd.read_csv(PATH)

sample = events[
    events["clinical_note_id"].astype(str).str.contains(
        " ",
        regex=False
    )
]

print("Total extracted rows:", len(events))
print("\nEvent categories:")
print(events["event_type"].value_counts())

print("\nSample rows:")
print(
    events[
        [
            "clinical_note_id",
            "event_type",
            "event_text"
        ]
    ].head(15).to_string(index=False)
)
