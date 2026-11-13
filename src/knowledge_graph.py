
from pathlib import Path
import pandas as pd
import networkx as nx

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_PATH = PROCESSED_DIR / "clinical_triples.csv"


def load_triples():
    print("Loading clinical triples...")
    triples = pd.read_csv(INPUT_PATH)

    print("Total triples:", len(triples))
    return triples


def build_patient_graph(patient_id, triples):

    patient_data = triples[
        triples["patient_id"].astype(str) == str(patient_id)
    ].copy()

    if patient_data.empty:
        print("No data found for this patient.")
        return

    graph = nx.MultiDiGraph()

    # Add patient node
    patient_node = f"Patient:{patient_id}"

    graph.add_node(
        patient_node,
        label="Patient",
        node_type="Patient"
    )

    processed_notes = set()

    for index, row in patient_data.iterrows():

        note_id = str(row["clinical_note_id"])
        event_type = str(row["event_type"])
        event_date = str(row["event_date"])

        # Create a unique note/event node
        if note_id and note_id.lower() not in ("nan", "none"):

            note_key = note_id

        else:
            note_key = f"row_{index}"

        event_node = f"ClinicalNote:{patient_id}:{note_key}"

        event_label = (
            f"{event_type} | {event_date}"
        )

        # Add each clinical note only once
        if event_node not in processed_notes:

            graph.add_node(
                event_node,
                label=event_label,
                node_type="Clinical Event",
                event_type=event_type,
                event_date=event_date,
                clinical_note_id=note_id
            )

            graph.add_edge(
                patient_node,
                event_node,
                label="HAS_CLINICAL_EVENT",
                relationship="HAS_CLINICAL_EVENT"
            )

            processed_notes.add(event_node)

        predicate = str(row["predicate"]).strip()
        obj = str(row["object"]).strip()
        evidence = str(row["evidence"])

        # Skip generic event-category objects.
        # The actual event is already represented by the note node.
        if predicate == "HAS_CLINICAL_EVENT":
            continue

        if obj.lower() in ("", "nan", "none"):
            continue

        # Add clinical concept node
        concept_node = f"Concept:{obj}"

        graph.add_node(
            concept_node,
            label=obj,
            node_type="Clinical Concept"
        )

        # Connect the clinical note to the extracted concept
        graph.add_edge(
            event_node,
            concept_node,
            label=predicate,
            relationship=predicate,
            evidence=evidence[:500]
        )

    # Save patient-specific graph
    output_path = (
        PROCESSED_DIR /
        f"knowledge_graph_patient_{patient_id}.gexf"
    )

    nx.write_gexf(graph, output_path)

    print("\n" + "=" * 45)
    print("PATIENT KNOWLEDGE GRAPH CREATED")
    print("=" * 45)

    print("Patient ID:", patient_id)
    print("Clinical notes:", len(processed_notes))
    print("Total nodes:", graph.number_of_nodes())
    print("Total relationships:", graph.number_of_edges())
    print("Saved to:", output_path)


def main():

    triples = load_triples()

    required_columns = [
        "patient_id",
        "clinical_note_id",
        "event_type",
        "event_date",
        "predicate",
        "object",
        "evidence"
    ]

    missing = [
        col for col in required_columns
        if col not in triples.columns
    ]

    if missing:
        print("Missing columns:", missing)
        return

    patients = sorted(
        triples["patient_id"]
        .dropna()
        .astype(str)
        .unique()
    )

    print("\nPATIENT KNOWLEDGE GRAPH EXPLORER")
    print("=" * 45)

    for i, patient in enumerate(patients, start=1):
        print(f"{i}. {patient}")

    while True:

        choice = input(
            "\nEnter patient number (or Q to quit): "
        ).strip()

        if choice.lower() == "q":
            print("Exiting explorer.")
            break

        if not choice.isdigit():
            print("Please enter a valid number.")
            continue

        index = int(choice)

        if index < 1 or index > len(patients):
            print("Number out of range.")
            continue

        patient_id = patients[index - 1]

        build_patient_graph(patient_id, triples)


if __name__ == "__main__":
    main()
