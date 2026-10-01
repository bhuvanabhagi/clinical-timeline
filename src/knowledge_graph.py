from pathlib import Path
import pandas as pd

#paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_PATH = PROCESSED_DIR / "temporal_events.csv"

OUTPUT_PATH = PROCESSED_DIR / "knowledge_graph.csv"



def load_events():

    print("Loading temporal events...")

    events = pd.read_csv(INPUT_PATH)

    print(f"Total events loaded: {len(events)}")

    return events




def build_knowledge_graph():

    events = load_events()

    print("\nEvent columns:")
    print(events.columns.tolist())



    graph_records = []

    for _, row in events.iterrows():

        person_id = row.get("person_id")

        event_type = row.get("event_type")

        event_text = row.get("event_text")

        event_timestamp = row.get("event_timestamp")

        event_order = row.get("event_order")

        clinical_note_id = row.get("clinical_note_id")

        admission_id = row.get("admission_id")


        # Skip events without a patient
        if pd.isna(person_id):
            continue

        

        if event_type == "Symptom":

            relationship = "EXPERIENCED"

        elif event_type == "Investigation":

            relationship = "UNDERWENT"

        elif event_type == "Diagnosis":

            relationship = "DIAGNOSED_WITH"

        elif event_type == "Treatment":

            relationship = "TREATED_WITH"

        elif event_type == "Monitoring":

            relationship = "MONITORED_BY"

        elif event_type == "Discharge":

            relationship = "DISCHARGED_AFTER"

        elif event_type == "Follow-up":

            relationship = "FOLLOWED_UP"

        else:

            relationship = "RELATED_TO"


 

        graph_records.append({

            "patient_id": person_id,

            "relationship": relationship,

            "event_type": event_type,

            "event": event_text,

            "event_timestamp": event_timestamp,

            "event_order": event_order,

            "clinical_note_id": clinical_note_id,

            "admission_id": admission_id

        })




    graph = pd.DataFrame(graph_records)




    graph.to_csv(
        OUTPUT_PATH,
        index=False
    )




    print("\n========================================")
    print("KNOWLEDGE GRAPH DATA CREATED")
    print("========================================")

    print(f"Graph relationships: {len(graph)}")

    print(
        f"Patients represented: "
        f"{graph['patient_id'].nunique()}"
    )

    print("\nRelationship distribution:")

    print(
        graph["relationship"]
        .value_counts()
    )


    print("\nSample graph relationships:")

    print(
        graph[
            [
                "patient_id",
                "relationship",
                "event_type",
                "event_timestamp",
                "event"
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


    print("\nSaved to:")
    print(OUTPUT_PATH)



if __name__ == "__main__":

    build_knowledge_graph()
