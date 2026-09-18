import networkx as nx
import pandas as pd

# Load data
patients = pd.read_csv("data/patients.csv")
admissions = pd.read_csv("data/admissions.csv")
notes = pd.read_csv("data/synthetic_clinical_notes.csv")


def build_case(person_id):

    patient_admissions = admissions[
        admissions["patient_id"] == person_id
    ]

    admission_ids = patient_admissions["admission_id"].tolist()

    case_notes = notes[
        notes["admission_id"].isin(admission_ids)
    ].copy()

    case_notes["creation_timestamp"] = pd.to_datetime(
        case_notes["creation_timestamp"],
        dayfirst=True,
        errors="coerce"
    )

    return case_notes.sort_values("creation_timestamp")


def build_knowledge_graph(case_notes):

    graph = nx.DiGraph()

    for _, note in case_notes.iterrows():

        text = str(note["clean_note_text"])
        date = note["creation_timestamp"]
        source = note["clinical_note_id"]

        # Add entities when they appear together
        if "headache" in text.lower() and "RCVS" in text:

            graph.add_node("Headache", type="Symptom")
            graph.add_node("RCVS", type="Diagnosis")

            graph.add_edge(
                "Headache",
                "RCVS",
                relationship="associated_with",
                date=str(date),
                source=source
            )

        if "MRI" in text or "MRA" in text:

            graph.add_node("MRI/MRA", type="Investigation")
            graph.add_node("RCVS", type="Diagnosis")

            graph.add_edge(
                "MRI/MRA",
                "RCVS",
                relationship="investigated",
                date=str(date),
                source=source
            )

        if "nimodipine" in text.lower():

            graph.add_node("Nimodipine", type="Medication")
            graph.add_node("RCVS", type="Diagnosis")

            graph.add_edge(
                "Nimodipine",
                "RCVS",
                relationship="treatment_for",
                date=str(date),
                source=source
            )

    return graph


# ---------------------------------------
# TEST
# ---------------------------------------

person_id = patients.iloc[0]["person_id"]

case_notes = build_case(person_id)

graph = build_knowledge_graph(case_notes)

print("KNOWLEDGE GRAPH")
print("=" * 80)

print("\nENTITIES:")

for node, data in graph.nodes(data=True):

    print(
        "-",
        node,
        "| Type:",
        data["type"]
    )


print("\nRELATIONSHIPS:")

for source, target, data in graph.edges(data=True):

    print(
        "-",
        source,
        "→",
        data["relationship"],
        "→",
        target
    )

    print(
        "  Date:",
        data["date"]
    )

    print(
        "  Source:",
        data["source"]
    )