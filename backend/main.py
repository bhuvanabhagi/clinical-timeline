
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import csv
import html

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


# ==================================================
# 1. PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = BASE_DIR / "data" / "processed" / "clinical_triples.csv"
FRONTEND_DIR = BASE_DIR / "frontend"


# ==================================================
# 2. FASTAPI APPLICATION
# ==================================================

app = FastAPI(
    title="Clinical Timeline Intelligence",
    description="Patient journey reconstruction and knowledge graph",
    version="1.1.0"
)

app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static"
)


# ==================================================
# 3. COMMON FUNCTIONS
# ==================================================

def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def load_triples():

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Clinical triples file not found: {DATA_FILE}"
        )

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("The triples CSV has no header.")

        required = {
            "patient_id",
            "clinical_note_id",
            "predicate",
            "object"
        }

        missing = required - set(reader.fieldnames)

        if missing:
            raise ValueError(
                f"Missing columns in clinical_triples.csv: {sorted(missing)}"
            )

        return list(reader)


def parse_date(value):

    value = clean(value)

    if not value:
        return None

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def display_date(value):

    parsed = parse_date(value)

    if parsed is None:
        return value or "Date unavailable"

    if parsed.hour or parsed.minute:
        return parsed.strftime("%d %b %Y, %H:%M")

    return parsed.strftime("%d %b %Y")


# ==================================================
# 4. NODE CLASSIFICATION
# ==================================================

def classify_node(identifier):

    identifier = clean(identifier)

    if ":" not in identifier:
        return "concept", identifier

    prefix, value = identifier.split(":", 1)

    groups = {
        "PATIENT": "patient",
        "NOTE": "note",
        "EVENT": "event",
        "SYMPTOM": "symptom",
        "DIAGNOSIS": "diagnosis",
        "MEDICATION": "medication",
        "TEST": "investigation",
        "PROCEDURE_TEST": "investigation",
        "BODY_PART": "bodypart"
    }

    return groups.get(prefix.upper(), "concept"), value.strip()


def make_node(identifier, evidence="", assertion=""):

    group, value = classify_node(identifier)

    label = value

    if group == "patient":
        label = "Patient"

    elif group == "note":
        label = "Clinical Note\n" + value[:8]

    elif group == "event":
        label = value.replace("_", " ").title()

    else:
        label = value.replace("_", " ").title()

    tooltip = (
        f"<b>{html.escape(label)}</b><br>"
        f"Type: {html.escape(group)}<br>"
        f"Identifier: {html.escape(identifier)}"
    )

    if assertion:
        tooltip += (
            f"<br>Assertion: {html.escape(assertion)}"
        )

    if evidence:
        tooltip += (
            f"<br>Evidence: {html.escape(evidence[:500])}"
        )

    return {
        "id": identifier,
        "label": label,
        "group": group,
        "title": tooltip,
        "identifier": identifier,
        "evidence": evidence,
        "assertion": assertion
    }


# ==================================================
# 5. HEALTH CHECK
# ==================================================

@app.get("/api/health")
def health_check():

    return {
        "status": "running",
        "application": "Clinical Timeline Intelligence",
        "data_file_exists": DATA_FILE.exists()
    }


# ==================================================
# 6. PATIENT LIST
# ==================================================

@app.get("/api/patients")
def get_patients():

    try:
        rows = load_triples()
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

    patients = {}

    for row in rows:

        patient_id = clean(row.get("patient_id"))

        if not patient_id:
            continue

        if patient_id not in patients:
            patients[patient_id] = {
                "patient_id": patient_id,
                "notes": set(),
                "admissions": set()
            }

        note_id = clean(row.get("clinical_note_id"))
        admission_id = clean(row.get("admission_id"))

        if note_id:
            patients[patient_id]["notes"].add(note_id)

        if admission_id:
            patients[patient_id]["admissions"].add(admission_id)

    result = []

    for patient in patients.values():

        result.append({
            "patient_id": patient["patient_id"],
            "total_notes": len(patient["notes"]),
            "total_admissions": len(patient["admissions"])
        })

    result.sort(key=lambda item: item["patient_id"])

    return {
        "total_patients": len(result),
        "patients": result
    }


# ==================================================
# 7. PATIENT TIMELINE
# ==================================================

@app.get("/api/patients/{patient_id}/timeline")
def get_patient_timeline(patient_id: str):

    try:
        rows = load_triples()
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

    patient_rows = [
        row for row in rows
        if clean(row.get("patient_id")) == patient_id
    ]

    if not patient_rows:
        raise HTTPException(
            status_code=404,
            detail="Patient not found."
        )

    notes = {}

    for row in patient_rows:

        note_id = clean(row.get("clinical_note_id"))

        if not note_id:
            continue

        if note_id not in notes:

            notes[note_id] = {
                "note_id": note_id,
                "admission_id": clean(row.get("admission_id")),
                "event_date": clean(row.get("event_date")),
                "parsed_date": parse_date(row.get("event_date")),
                "event_categories": set(),
                "concepts": defaultdict(dict),
                "additional_evidence": set()
            }

        note = notes[note_id]

        if not note["admission_id"]:
            note["admission_id"] = clean(row.get("admission_id"))

        row_date = clean(row.get("event_date"))

        if row_date and not note["event_date"]:
            note["event_date"] = row_date
            note["parsed_date"] = parse_date(row_date)

        predicate = clean(row.get("predicate"))
        object_value = clean(row.get("object"))
        evidence = clean(row.get("evidence"))
        assertion = clean(row.get("assertion")) or "PRESENT"
        event_type = clean(row.get("event_type"))

        if predicate == "HAS_EVENT_CATEGORY":

            category = event_type or object_value.replace("EVENT:", "")

            if category:
                note["event_categories"].add(category)

            if evidence:
                note["additional_evidence"].add(evidence)

            continue

        if predicate == "HAS_CLINICAL_NOTE":
            continue

        category_map = {
            "HAS_SYMPTOM": "Symptoms",
            "ABSENT_SYMPTOM": "Absent symptoms",
            "HAS_DIAGNOSIS": "Diagnoses",
            "MENTIONS_MEDICATION": "Medications",
            "MENTIONS_TEST": "Investigations and tests",
            "MENTIONS_BODY_PART": "Body parts mentioned"
        }

        if predicate not in category_map:
            continue

        category = category_map[predicate]

        concept = object_value

        if ":" in concept:
            concept = concept.split(":", 1)[1]

        concept = concept.strip()

        if not concept:
            continue

        if predicate == "MENTIONS_BODY_PART":
            assertion = "MENTIONED"

        concept_key = (concept.lower(), assertion)

        if concept_key not in note["concepts"][category]:

            note["concepts"][category][concept_key] = {
                "name": concept,
                "assertion": assertion,
                "evidence": set()
            }

        if evidence:
            note["concepts"][category][concept_key]["evidence"].add(
                evidence
            )

    timeline = []

    for note in notes.values():

        formatted_concepts = {}

        for category, concepts in note["concepts"].items():

            formatted_concepts[category] = []

            for concept in concepts.values():

                formatted_concepts[category].append({
                    "name": concept["name"],
                    "assertion": concept["assertion"],
                    "evidence": sorted(concept["evidence"])
                })

            formatted_concepts[category].sort(
                key=lambda item: item["name"].lower()
            )

        timeline.append({
            "note_id": note["note_id"],
            "admission_id": note["admission_id"],
            "event_date": note["event_date"],
            "display_date": display_date(note["event_date"]),
            "event_categories": sorted(note["event_categories"]),
            "concepts": formatted_concepts,
            "additional_evidence": sorted(note["additional_evidence"])
        })

    timeline.sort(
        key=lambda item: (
            parse_date(item["event_date"]) is None,
            parse_date(item["event_date"]) or datetime.max,
            item["note_id"]
        )
    )

    admission_ids = sorted({
        note["admission_id"]
        for note in timeline
        if note["admission_id"]
    })

    return {
        "patient_id": patient_id,
        "total_notes": len(timeline),
        "total_admissions": len(admission_ids),
        "admission_ids": admission_ids,
        "timeline": timeline
    }


# ==================================================
# 8. KNOWLEDGE GRAPH API
# ==================================================

@app.get("/api/patients/{patient_id}/graph")
def get_patient_graph(patient_id: str):

    try:
        rows = load_triples()
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

    patient_rows = [
        row for row in rows
        if clean(row.get("patient_id")) == patient_id
    ]

    if not patient_rows:
        raise HTTPException(
            status_code=404,
            detail="Patient not found."
        )

    nodes = {}
    edges = {}
    note_dates = {}

    # Collect timestamps for note nodes
    for row in patient_rows:

        note_id = clean(row.get("clinical_note_id"))

        if note_id and clean(row.get("event_date")):
            note_dates[note_id] = clean(row.get("event_date"))

    for row in patient_rows:

        subject = clean(row.get("subject"))
        object_value = clean(row.get("object"))
        predicate = clean(row.get("predicate"))
        evidence = clean(row.get("evidence"))
        assertion = clean(row.get("assertion"))

        note_id = clean(row.get("clinical_note_id"))

        if not subject or not object_value or not predicate:
            continue

        # Skip structural event-category nodes in the graph.
        # The clinical note and its clinical entities remain visible.
        if predicate == "HAS_EVENT_CATEGORY":
            continue

        if subject not in nodes:
            nodes[subject] = make_node(
                subject,
                evidence,
                assertion
            )

        if object_value not in nodes:
            nodes[object_value] = make_node(
                object_value,
                evidence,
                assertion
            )

        # Attach the recorded timestamp to note nodes
        if subject.startswith("NOTE:"):
            nodes[subject]["date"] = note_dates.get(
                note_id, ""
            )

        if object_value.startswith("NOTE:"):
            nodes[object_value]["date"] = note_dates.get(
                note_id, ""
            )

        # Preserve the strongest available evidence
        for node_id in [subject, object_value]:

            if evidence and not nodes[node_id].get("evidence"):
                nodes[node_id]["evidence"] = evidence

            if assertion and not nodes[node_id].get("assertion"):
                nodes[node_id]["assertion"] = assertion

        edge_key = (
            subject,
            object_value,
            predicate
        )

        if edge_key not in edges:

            edges[edge_key] = {
                "id": f"edge_{len(edges) + 1}",
                "from": subject,
                "to": object_value,
                "label": predicate.replace("_", " "),
                "title": predicate,
                "arrows": "to",
                "evidence": evidence,
                "assertion": assertion,
                "note_id": note_id
            }

    # Keep the selected patient connected to every graph relationship
    return {
        "patient_id": patient_id,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "nodes": list(nodes.values()),
        "edges": list(edges.values())
    }


# ==================================================
# 9. HOME PAGE
# ==================================================

@app.get("/")
def home():

    index_file = FRONTEND_DIR / "index.html"

    if not index_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Frontend index.html not found."
        )

    return FileResponse(index_file)
