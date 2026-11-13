
import pandas as pd
import re
from pathlib import Path


# ==================================================
# 1. FILE PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "processed" / "clinical_events.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "clinical_entities.csv"


# ==================================================
# 2. ENTITY PATTERNS
# ==================================================

ENTITY_PATTERNS = {
    "SYMPTOM": [
        "shortness of breath",
        "abdominal pain",
        "chest pain",
        "severe headache",
        "headache",
        "dizziness",
        "weakness",
        "vomiting",
        "nausea",
        "constipation",
        "fever",
        "fatigue",
        "cough"
    ],

    "DIAGNOSIS": [
        "hypertension",
        "dehydration",
        "constipation",
        "pneumonia",
        "infection",
        "stroke",
        "RCVS"
    ],

    "MEDICATION": [
        "sodium chloride",
        "ferrous sulfate",
        "paracetamol",
        "bisacodyl",
        "nimodipine",
        "macrogol",
        "ibuprofen",
        "aspirin",
        "antibiotic",
        "vitamin D",
        "calcium"
    ],

    "PROCEDURE_TEST": [
        "renal panel",
        "blood tests",
        "blood test",
        "CT head",
        "CT scan",
        "X-ray",
        "ultrasound",
        "MRI",
        "MRA",
        "FBC",
        "LFT"
    ],

    "BODY_PART": [
        "abdomen",
        "brain",
        "chest",
        "heart",
        "lung",
        "head"
    ]
}


# ==================================================
# 3. CLINICAL SECTION LABELS
# ==================================================

SECTION_PATTERN = re.compile(
    r"\b("
    r"History of Presenting Complaint|"
    r"Presenting Complaint|"
    r"Systems Review|System Review|"
    r"Gastrointestinal|Cardiovascular|"
    r"Respiratory|Genitourinary|"
    r"Neurological|Musculoskeletal|"
    r"Psychiatric|Constitutional|"
    r"On Examination|Examination|"
    r"Assessment|Investigations|"
    r"Impression|Diagnosis|Treatment|"
    r"Medication|Vital Signs|Plan|Skin"
    r")\s*:",
    re.IGNORECASE
)


# ==================================================
# 4. EVIDENCE SEGMENTATION
# ==================================================

def split_into_evidence_spans(text):

    if pd.isna(text):
        return []

    text = str(text)
    text = text.replace("\r", "\n")
    text = text.replace("\t", " ")

    # Normalize repeated spaces
    text = re.sub(r"[ ]+", " ", text)

    # Separate known clinical section labels
    text = SECTION_PATTERN.sub(
        lambda match: "\n" + match.group(0),
        text
    )

    lines = re.split(r"\n+", text)

    evidence_spans = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # Remove leading bullet symbols
        line = re.sub(r"^[\-\*\•\u2022]+\s*", "", line)

        # Split at sentence endings and semicolons
        sentences = re.split(
            r"(?<=[.!?])\s+|;\s*",
            line
        )

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            # Split comma-separated clauses when the next
            # clause starts with a clinical connector.
            clauses = re.split(
                r",\s*(?=(?:no\b|not\b|denies\b|denied\b|"
                r"without\b|reports?\b|complains?\b|"
                r"has\b|but\b|however\b))",
                sentence,
                flags=re.IGNORECASE
            )

            for clause in clauses:

                clause = clause.strip()

                if clause:
                    evidence_spans.append(clause)

    # Remove duplicate evidence while preserving order
    unique_spans = []
    seen = set()

    for span in evidence_spans:

        normalized = re.sub(
            r"\s+",
            " ",
            span
        ).strip()

        if normalized and normalized.lower() not in seen:
            seen.add(normalized.lower())
            unique_spans.append(normalized)

    return unique_spans


# ==================================================
# 5. NEGATION / ASSERTION DETECTION
# ==================================================

NEGATION_PATTERNS = [
    r"\bno\b",
    r"\bnot\b",
    r"\bdenies\b",
    r"\bdenied\b",
    r"\bwithout\b",
    r"\babsence of\b",
    r"\bnegative for\b",
    r"\bfree of\b",
    r"\bno evidence of\b",
    r"\bnot experiencing\b",
    r"\bdoes not have\b",
    r"\bdo not have\b",
    r"\bhas no\b",
    r"\bhas not\b",
    r"\babsent\b"
]


def detect_assertion(text, start, end):

    before = text[:start]
    after = text[end:]

    previous_words = before.split()[-8:]
    next_words = after.split()[:5]

    context_before = " ".join(previous_words).lower()
    context_after = " ".join(next_words).lower()

    # Avoid treating "not only" as negation
    if re.search(r"\bnot only\b", context_before):
        return "PRESENT"

    for pattern in NEGATION_PATTERNS:

        if re.search(pattern, context_before):
            return "ABSENT"

    # Check phrases such as "pain is absent"
    if re.search(
        r"\b(is|are|was|were)\s+absent\b",
        context_after
    ):
        return "ABSENT"

    return "PRESENT"


# ==================================================
# 6. ENTITY EXTRACTION FROM ONE EVIDENCE SPAN
# ==================================================

def extract_sentence_entities(sentence):

    extracted = []

    for entity_type, terms in ENTITY_PATTERNS.items():

        # Match longer phrases before shorter phrases
        sorted_terms = sorted(
            terms,
            key=len,
            reverse=True
        )

        occupied_positions = []

        for term in sorted_terms:

            pattern = re.compile(
                r"\b" + re.escape(term) + r"\b",
                re.IGNORECASE
            )

            for match in pattern.finditer(sentence):

                start = match.start()
                end = match.end()

                # Prevent overlapping entity matches
                overlap = any(
                    start < existing_end
                    and end > existing_start
                    for existing_start, existing_end
                    in occupied_positions
                )

                if overlap:
                    continue

                assertion = detect_assertion(
                    sentence,
                    start,
                    end
                )

                extracted.append({
                    "entity_type": entity_type,
                    "entity_text": match.group(0),
                    "evidence": sentence,
                    "assertion": assertion
                })

                occupied_positions.append((start, end))

    return extracted


# ==================================================
# 7. MAIN ENTITY EXTRACTION
# ==================================================

def extract_entities():

    print("Loading clinical event records...")

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"\nInput file not found: {INPUT_FILE}\n"
            "Check whether data/processed/clinical_events.csv exists."
        )

    events_df = pd.read_csv(INPUT_FILE)

    # IMPORTANT: admission_id is now included
    required_columns = [
        "person_id",
        "admission_id",
        "clinical_note_id",
        "event_text"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in events_df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing columns in clinical_events.csv: {missing_columns}"
        )

    print("Clinical event records:", len(events_df))

    all_entities = []

    # Process every clinical event
    for _, row in events_df.iterrows():

        person_id = row["person_id"]
        admission_id = row["admission_id"]
        clinical_note_id = row["clinical_note_id"]
        event_text = row["event_text"]

        evidence_spans = split_into_evidence_spans(
            event_text
        )

        for evidence in evidence_spans:

            extracted_entities = extract_sentence_entities(
                evidence
            )

            for entity in extracted_entities:

                all_entities.append({
                    "person_id": person_id,
                    "admission_id": admission_id,
                    "clinical_note_id": clinical_note_id,
                    "entity_type": entity["entity_type"],
                    "entity_text": entity["entity_text"],
                    "evidence": entity["evidence"],
                    "assertion": entity["assertion"]
                })

    # Create DataFrame with all required columns
    entities_df = pd.DataFrame(
        all_entities,
        columns=[
            "person_id",
            "admission_id",
            "clinical_note_id",
            "entity_type",
            "entity_text",
            "evidence",
            "assertion"
        ]
    )

    # Remove exact duplicate records
    if not entities_df.empty:

        entities_df.drop_duplicates(
            subset=[
                "person_id",
                "admission_id",
                "clinical_note_id",
                "entity_type",
                "entity_text",
                "evidence",
                "assertion"
            ],
            inplace=True
        )

    # Create output directory if necessary
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save output
    entities_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ==================================================
    # 8. RESULTS
    # ==================================================

    print("\n" + "=" * 50)
    print("ENTITY EXTRACTION COMPLETED")
    print("=" * 50)

    print("Clinical event records:", len(events_df))
    print("Extracted entity records:", len(entities_df))

    if not entities_df.empty:

        print("\nEntity type distribution:")
        print(
            entities_df["entity_type"].value_counts()
        )

        print("\nAssertion distribution:")
        print(
            entities_df["assertion"].value_counts()
        )

        print("\nSample extracted entities:")
        print(
            entities_df.head(10).to_string(index=False)
        )

    else:

        print("\nNo entities were extracted.")

    print("\nOutput saved at:")
    print(OUTPUT_FILE)


# ==================================================
# 9. EXECUTION
# ==================================================

if __name__ == "__main__":
    extract_entities()
