
const API_BASE = "";

// ======================================================
// 1. ELEMENTS
// ======================================================

const patientSelect = document.getElementById("patient-select");
const loadButton = document.getElementById("load-patient");
const patientMessage = document.getElementById("patient-message");
const connectionStatus = document.getElementById("connection-status");

const totalNotes = document.getElementById("total-notes");
const totalAdmissions = document.getElementById("total-admissions");
const totalEntries = document.getElementById("total-entries");

const patientIdDisplay = document.getElementById("patient-id-display");
const admissionIdDisplay = document.getElementById("admission-id-display");

const timelineCount = document.getElementById("timeline-count");
const timelineContainer = document.getElementById("timeline-container");

const graphContainer = document.getElementById("knowledge-graph");
const graphStatus = document.getElementById("graph-status");
const graphNodeCount = document.getElementById("graph-node-count");
const graphEdgeCount = document.getElementById("graph-edge-count");
const graphPatientLabel = document.getElementById("graph-patient-label");
const graphDetails = document.getElementById("graph-node-details");

const graphFitButton = document.getElementById("graph-fit");
const graphResetButton = document.getElementById("graph-reset");


// ======================================================
// 2. STATE
// ======================================================

let currentTimeline = [];
let selectedPatientId = null;
let selectedNoteIndex = null;


// ======================================================
// 3. CATEGORY DEFINITIONS
// ======================================================

const CATEGORIES = [
    "Symptoms",
    "Absent symptoms",
    "Diagnoses",
    "Medications",
    "Investigations and tests",
    "Body parts mentioned"
];

const CATEGORY_COLORS = {
    "Symptom": "#d58b35",
    "Symptoms": "#d58b35",
    "Diagnosis": "#c65b70",
    "Diagnoses": "#c65b70",
    "Treatment": "#218b6b",
    "Medication": "#218b6b",
    "Medications": "#218b6b",
    "Investigation": "#258fa8",
    "Investigations": "#258fa8",
    "Monitoring": "#7770bd",
    "Follow-up": "#7770bd",
    "Discharge": "#43866b",
    "Other": "#718096"
};


// ======================================================
// 4. SAFE HTML
// ======================================================

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[character]);
}


// ======================================================
// 5. API
// ======================================================

async function apiRequest(endpoint) {
    const response = await fetch(`${API_BASE}${endpoint}`);

    if (!response.ok) {
        let message = "Something went wrong.";

        try {
            const data = await response.json();
            message = data.detail || message;
        } catch {}

        throw new Error(message);
    }

    return response.json();
}


// ======================================================
// 6. BACKEND CONNECTION
// ======================================================

async function checkBackend() {
    try {
        await apiRequest("/api/health");

        connectionStatus.textContent = "Connected";
        connectionStatus.style.color = "#35d49a";

    } catch (error) {
        connectionStatus.textContent = "Disconnected";
        connectionStatus.style.color = "#ff7d88";

        showMessage(
            "Cannot connect to backend. Start the FastAPI server.",
            true
        );
    }
}


// ======================================================
// 7. LOAD PATIENTS
// ======================================================

async function loadPatients() {
    patientSelect.innerHTML =
        `<option value="">Loading patients...</option>`;

    try {
        const data = await apiRequest("/api/patients");

        patientSelect.innerHTML =
            `<option value="">Choose a patient</option>`;

        data.patients.forEach((patient, index) => {
            const option = document.createElement("option");

            option.value = patient.patient_id;
            option.textContent =
                `Patient ${index + 1} — ${patient.patient_id}`;

            patientSelect.appendChild(option);
        });

        showMessage(
            `${data.total_patients} patients loaded successfully.`
        );

        if (data.patients.length > 0) {
            patientSelect.selectedIndex = 1;

            await loadPatientJourney(
                data.patients[0].patient_id
            );
        }

    } catch (error) {
        patientSelect.innerHTML =
            `<option value="">Unable to load patients</option>`;

        showMessage(error.message, true);
    }
}


// ======================================================
// 8. LOAD PATIENT JOURNEY
// ======================================================

async function loadPatientJourney(patientId) {
    if (!patientId) {
        showMessage("Please select a patient.", true);
        return;
    }

    selectedPatientId = patientId;
    selectedNoteIndex = null;

    loadButton.disabled = true;
    loadButton.textContent = "Loading...";

    resetGraphDisplay();

    try {
        const encodedId = encodeURIComponent(patientId);

        const data = await apiRequest(
            `/api/patients/${encodedId}/timeline`
        );

        currentTimeline = data.timeline || [];

        renderPatientSummary(data);
        renderTimeline(currentTimeline);
        renderJourneyGraph(currentTimeline);

        showMessage(
            "Patient journey loaded successfully."
        );

    } catch (error) {
        showMessage(error.message, true);

        timelineContainer.innerHTML = `
            <div class="empty-state">
                <h3>Unable to load patient data</h3>
                <p>${escapeHTML(error.message)}</p>
            </div>
        `;

        graphStatus.textContent = "Graph unavailable";

    } finally {
        loadButton.disabled = false;
        loadButton.innerHTML =
            `View patient journey <span>→</span>`;
    }
}


// ======================================================
// 9. PATIENT SUMMARY
// ======================================================

function renderPatientSummary(data) {
    totalNotes.textContent = data.total_notes;
    totalAdmissions.textContent = data.total_admissions;
    totalEntries.textContent = data.timeline.length;

    patientIdDisplay.textContent = data.patient_id;

    admissionIdDisplay.textContent =
        data.admission_ids?.length
            ? data.admission_ids.join(", ")
            : "Not available";
}


// ======================================================
// 10. TIMELINE
// ======================================================

function renderTimeline(timeline) {
    timelineCount.textContent = `${timeline.length} notes`;

    if (!timeline.length) {
        timelineContainer.innerHTML = `
            <div class="empty-state">
                <h3>No timeline records</h3>
                <p>No clinical notes were found.</p>
            </div>
        `;
        return;
    }

    timelineContainer.innerHTML = timeline.map((note, index) => {
        const eventTags = (note.event_categories || [])
            .map(category => `
                <span class="event-tag">
                    ${escapeHTML(category)}
                </span>
            `).join("");

        const categorySections = CATEGORIES.map(category =>
            renderCategory(
                category,
                note.concepts?.[category] || []
            )
        ).join("");

        const extraEvidence = note.additional_evidence || [];

        return `
            <article class="timeline-card">

                <div class="note-header">
                    <div>
                        <p class="note-date">
                            ${escapeHTML(note.display_date)}
                        </p>

                        <p class="note-id">
                            Note ID: ${escapeHTML(note.note_id)}
                        </p>
                    </div>

                    <span class="note-number">
                        CLINICAL NOTE ${index + 1}
                    </span>
                </div>

                <div class="note-content">

                    <div class="event-tags">
                        ${eventTags}
                    </div>

                    ${categorySections}

                    ${
                        extraEvidence.length
                        ? `
                            <details class="additional-evidence">
                                <summary>
                                    Additional evidence (${extraEvidence.length})
                                </summary>

                                <ul class="evidence-list">
                                    ${extraEvidence.map(item =>
                                        `<li>${escapeHTML(item)}</li>`
                                    ).join("")}
                                </ul>
                            </details>
                        `
                        : ""
                    }

                </div>
            </article>
        `;
    }).join("");
}


// ======================================================
// 11. TIMELINE CATEGORY
// ======================================================

function renderCategory(category, concepts) {
    if (!concepts.length) {
        return `
            <div class="category-block">
                <h4 class="category-title">
                    ${escapeHTML(category)}
                </h4>
                <p class="empty-category">No extracted concepts.</p>
            </div>
        `;
    }

    return `
        <div class="category-block">

            <h4 class="category-title">
                ${escapeHTML(category)}
            </h4>

            ${concepts.map(concept => `
                <div class="concept-card">

                    <div class="concept-heading">
                        <span class="concept-name">
                            ${escapeHTML(concept.name)}
                        </span>

                        <span class="assertion ${escapeHTML(concept.assertion)}">
                            ${escapeHTML(concept.assertion)}
                        </span>
                    </div>

                    ${
                        concept.evidence?.length
                        ? `
                            <p class="evidence-label">
                                Supporting evidence
                            </p>

                            <ul class="evidence-list">
                                ${concept.evidence.map(item =>
                                    `<li>${escapeHTML(item)}</li>`
                                ).join("")}
                            </ul>
                        `
                        : ""
                    }

                </div>
            `).join("")}

        </div>
    `;
}


// ======================================================
// 12. GET SHORT DESCRIPTION FOR EACH NOTE
// ======================================================

function getNoteConcepts(note) {
    const concepts = [];

    CATEGORIES.forEach(category => {
        const items = note.concepts?.[category] || [];

        items.forEach(item => {
            const name = item.name;

            if (name && !concepts.includes(name)) {
                concepts.push(name);
            }
        });
    });

    return concepts;
}


function getNoteDescription(note) {
    const concepts = getNoteConcepts(note);

    if (concepts.length) {
        return concepts.slice(0, 5).join(" · ");
    }

    const categories = note.event_categories || [];

    if (categories.length) {
        return categories.slice(0, 3).join(" · ");
    }

    return "Clinical information recorded";
}


function getNoteEvidence(note) {
    for (const category of CATEGORIES) {
        const concepts = note.concepts?.[category] || [];

        for (const concept of concepts) {
            if (concept.evidence?.length) {
                return concept.evidence[0];
            }
        }
    }

    return note.additional_evidence?.[0] || "";
}


// ======================================================
// 13. DETERMINE NODE CATEGORY
// ======================================================

function getNodeCategory(note) {
    const categories = note.event_categories || [];

    const priority = [
        "Admission",
        "Investigation",
        "Diagnosis",
        "Treatment",
        "Monitoring",
        "Follow-up",
        "Discharge",
        "Symptom",
        "Other"
    ];

    for (const preferred of priority) {
        const found = categories.find(category =>
            category.toLowerCase().includes(preferred.toLowerCase())
        );

        if (found) return found;
    }

    return categories[0] || "Clinical note";
}


// ======================================================
// 14. RENDER CHRONOLOGICAL GRAPH
// ======================================================

function renderJourneyGraph(timeline) {
    graphContainer.innerHTML = "";

    if (!timeline.length) {
        graphStatus.textContent = "No journey available";
        return;
    }

    graphStatus.textContent = "Chronological patient journey";

    graphPatientLabel.textContent =
        selectedPatientId.substring(0, 8) + "...";

    // One starting patient node and one node per clinical note.
    graphNodeCount.textContent = timeline.length + 1;
    graphEdgeCount.textContent = timeline.length;

    const patientStart = `
        <div class="journey-start-node">

            <div class="journey-start-icon">P</div>

            <div>
                <div class="journey-start-title">
                    PATIENT JOURNEY
                </div>

                <div class="journey-start-subtitle">
                    ${escapeHTML(selectedPatientId)}
                </div>
            </div>

        </div>
    `;

    const noteBlocks = timeline.map((note, index) => {
        const category = getNodeCategory(note);

        const color =
            CATEGORY_COLORS[category] || "#64748b";

        const description = getNoteDescription(note);

        const evidence = getNoteEvidence(note);

        const concepts = getNoteConcepts(note);

        const isSelected = selectedNoteIndex === index;

        return `
            <div class="journey-step">

                <div class="journey-edge">
                    <div class="journey-edge-line"></div>
                    <div class="journey-edge-arrow">↓</div>
                </div>

                <button
                    type="button"
                    class="journey-node ${isSelected ? "selected" : ""}"
                    data-note-index="${index}"
                    style="--node-color:${color}"
                >

                    <div class="journey-node-top">

                        <span class="journey-node-number">
                            ${String(index + 1).padStart(2, "0")}
                        </span>

                        <span class="journey-node-category">
                            ${escapeHTML(category)}
                        </span>

                    </div>

                    <div class="journey-node-title">
                        Clinical Note ${index + 1}
                    </div>

                    <div class="journey-node-date">
                        ${escapeHTML(note.display_date)}
                    </div>

                    <div class="journey-node-description">
                        ${escapeHTML(description)}
                    </div>

                    ${
                        concepts.length
                        ? `
                            <div class="journey-concepts">
                                ${concepts.slice(0, 4).map(concept => `
                                    <span>
                                        ${escapeHTML(concept)}
                                    </span>
                                `).join("")}
                            </div>
                        `
                        : ""
                    }

                    <div class="journey-node-footer">
                        Click to inspect evidence →
                    </div>

                </button>

            </div>
        `;
    }).join("");

    graphContainer.innerHTML = `
        <div class="journey-graph">

            ${patientStart}

            <div class="journey-edge journey-start-edge">
                <div class="journey-edge-line"></div>
                <div class="journey-edge-arrow">↓</div>
            </div>

            ${noteBlocks}

        </div>
    `;

    // Click a node to inspect its evidence.
    graphContainer.querySelectorAll(".journey-node")
        .forEach(button => {

            button.addEventListener("click", () => {

                const index = Number(button.dataset.noteIndex);

                selectJourneyNode(index);

            });

        });

    // Restore inspector if a note was previously selected.
    if (selectedNoteIndex !== null) {
        showJourneyNodeDetails(selectedNoteIndex);
    } else {
        showJourneyStartDetails();
    }
}


// ======================================================
// 15. SELECT A JOURNEY NODE
// ======================================================

function selectJourneyNode(index) {
    selectedNoteIndex = index;

    graphContainer.querySelectorAll(".journey-node")
        .forEach(button => {
            const buttonIndex = Number(button.dataset.noteIndex);

            button.classList.toggle(
                "selected",
                buttonIndex === index
            );
        });

    showJourneyNodeDetails(index);
}


// ======================================================
// 16. NODE INSPECTOR
// ======================================================

function showJourneyNodeDetails(index) {
    const note = currentTimeline[index];

    if (!note) return;

    const concepts = getNoteConcepts(note);

    const evidence = getNoteEvidence(note);

    graphDetails.innerHTML = `
        <div class="journey-inspector">

            <div class="inspector-heading">
                <div>
                    <span>SELECTED JOURNEY NODE</span>
                    <h3>Clinical Note ${index + 1}</h3>
                </div>

                <span class="inspector-date">
                    ${escapeHTML(note.display_date)}
                </span>
            </div>

            <div class="inspector-grid">

                <div>
                    <span>Event category</span>
                    <strong>
                        ${escapeHTML((note.event_categories || []).join(", ") || "Clinical note")}
                    </strong>
                </div>

                <div>
                    <span>Clinical concepts</span>
                    <strong>${concepts.length}</strong>
                </div>

                <div>
                    <span>Note identifier</span>
                    <strong>${escapeHTML(note.note_id)}</strong>
                </div>

                <div>
                    <span>Admission identifier</span>
                    <strong>${escapeHTML(note.admission_id || "Not available")}</strong>
                </div>

            </div>

            <div class="inspector-section">
                <h4>Extracted clinical concepts</h4>

                ${
                    concepts.length
                    ? `
                        <div class="journey-concepts inspector-concepts">
                            ${concepts.map(concept => `
                                <span>${escapeHTML(concept)}</span>
                            `).join("")}
                        </div>
                    `
                    : `<p>No concepts extracted for this note.</p>`
                }
            </div>

            <div class="inspector-section">
                <h4>Supporting evidence</h4>

                <p>
                    ${escapeHTML(evidence || "No supporting evidence available.")}
                </p>
            </div>

            <div class="inspector-section">
                <h4>All note evidence</h4>

                ${
                    note.additional_evidence?.length
                    ? `
                        <ul class="evidence-list">
                            ${note.additional_evidence.map(item => `
                                <li>${escapeHTML(item)}</li>
                            `).join("")}
                        </ul>
                    `
                    : `<p>See the extracted concept evidence in the clinical timeline.</p>`
                }
            </div>

        </div>
    `;

    graphDetails.scrollIntoView({
        behavior: "smooth",
        block: "nearest"
    });
}


// ======================================================
// 17. PATIENT START NODE INSPECTOR
// ======================================================

function showJourneyStartDetails() {
    graphDetails.innerHTML = `
        <div class="journey-inspector">

            <div class="inspector-heading">
                <div>
                    <span>JOURNEY OVERVIEW</span>
                    <h3>Patient Clinical Journey</h3>
                </div>
            </div>

            <div class="inspector-grid">

                <div>
                    <span>Patient ID</span>
                    <strong>${escapeHTML(selectedPatientId)}</strong>
                </div>

                <div>
                    <span>Clinical notes</span>
                    <strong>${currentTimeline.length}</strong>
                </div>

            </div>

            <div class="inspector-section">
                <p>
                    Each node represents a clinical note in chronological order.
                    Select a node to view its extracted concepts and supporting evidence.
                </p>
            </div>

        </div>
    `;
}


// ======================================================
// 18. GRAPH CONTROLS
// ======================================================

function scrollGraphToStart() {
    graphContainer.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}

if (graphFitButton) {
    graphFitButton.addEventListener("click", scrollGraphToStart);
}

if (graphResetButton) {
    graphResetButton.addEventListener("click", () => {
        selectedNoteIndex = null;

        renderJourneyGraph(currentTimeline);

        scrollGraphToStart();
    });
}


// ======================================================
// 19. RESET GRAPH
// ======================================================

function resetGraphDisplay() {
    currentTimeline = [];
    selectedNoteIndex = null;

    graphNodeCount.textContent = "0";
    graphEdgeCount.textContent = "0";
    graphPatientLabel.textContent = "None";
    graphStatus.textContent = "Loading patient journey";

    graphContainer.innerHTML = `
        <div class="graph-empty">
            <h3>Loading patient journey...</h3>
        </div>
    `;

    graphDetails.innerHTML = "";
}


// ======================================================
// 20. MESSAGE
// ======================================================

function showMessage(message, isError = false) {
    patientMessage.textContent = message;
    patientMessage.classList.toggle("error", isError);
}


// ======================================================
// 21. BUTTON EVENTS
// ======================================================

loadButton.addEventListener("click", () => {
    loadPatientJourney(patientSelect.value);
});

patientSelect.addEventListener("change", () => {
    if (patientSelect.value) {
        showMessage(
            "Patient selected. Click View patient journey."
        );
    }
});


// ======================================================
// 22. APPLICATION START
// ======================================================

async function initializeApplication() {
    await checkBackend();
    await loadPatients();
}

initializeApplication();
