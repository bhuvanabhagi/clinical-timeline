from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data" / "processed"

TIMELINE_PATH = DATA_DIR / "patient_timelines.csv"


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Clinical Timeline API",
    description="API for querying patient clinical timelines",
    version="1.0.0",
)


# ============================================================
# LOAD TIMELINE DATA
# ============================================================

def load_timelines():
    """Load patient timeline data from CSV."""

    if not TIMELINE_PATH.exists():
        raise FileNotFoundError(
            f"Timeline file not found: {TIMELINE_PATH}"
        )

    df = pd.read_csv(TIMELINE_PATH)

    # Convert timestamp column if present
    if "event_timestamp" in df.columns:
        df["event_timestamp"] = pd.to_datetime(
            df["event_timestamp"],
            errors="coerce"
        )

    return df


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Clinical Timeline API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    try:
        df = load_timelines()

        return {
            "status": "healthy",
            "total_events": len(df),
            "patients": int(df["person_id"].nunique())
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# GET PATIENT TIMELINE
# ============================================================

@app.get("/patient/{patient_id}/timeline")
def get_patient_timeline(patient_id: str):

    try:
        df = load_timelines()

        patient_df = df[
            df["person_id"].astype(str) == str(patient_id)
        ].copy()

        if patient_df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No timeline found for patient: {patient_id}"
            )

        # Sort chronologically
        if "event_timestamp" in patient_df.columns:
            patient_df = patient_df.sort_values(
                by=["event_timestamp", "event_order"],
                na_position="last"
            )

        # Convert timestamps to strings for JSON
        if "event_timestamp" in patient_df.columns:
            patient_df["event_timestamp"] = (
                patient_df["event_timestamp"]
                .dt.strftime("%Y-%m-%d %H:%M:%S")
            )

        # Replace NaN with None
        patient_df = patient_df.where(
            pd.notna(patient_df),
            None
        )

        events = patient_df.to_dict(orient="records")

        return {
            "patient_id": patient_id,
            "total_events": len(events),
            "timeline": events
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# GET PATIENTS
# ============================================================

@app.get("/patients")
def get_patients():

    try:
        df = load_timelines()

        patients = (
            df["person_id"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        return {
            "total_patients": len(patients),
            "patients": patients
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# GET EVENTS BY TYPE
# ============================================================

@app.get("/patient/{patient_id}/events/{event_type}")
def get_patient_events(
    patient_id: str,
    event_type: str
):

    try:
        df = load_timelines()

        patient_df = df[
            (df["person_id"].astype(str) == str(patient_id))
            &
            (
                df["event_type"]
                .astype(str)
                .str.lower()
                == event_type.lower()
            )
        ].copy()

        if patient_df.empty:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No '{event_type}' events found "
                    f"for patient: {patient_id}"
                )
            )

        if "event_timestamp" in patient_df.columns:
            patient_df["event_timestamp"] = (
                patient_df["event_timestamp"]
                .dt.strftime("%Y-%m-%d %H:%M:%S")
            )

        patient_df = patient_df.where(
            pd.notna(patient_df),
            None
        )

        events = patient_df.to_dict(orient="records")

        return {
            "patient_id": patient_id,
            "event_type": event_type,
            "total_events": len(events),
            "events": events
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )