# DocuScout
> **The Intelligent Risk Radar for Your Contracts & Documents.**

## 1. Problem Statement

### The "Blind Spot" in Business
Small Businesses (SMBs), Freelancers, and Regular People frequently sign legal documents (Employment Offers, Rental Agreements, Vendor Contracts) without fully understanding the fine print.

### The Barrier
Hiring a lawyer to review a 10-page document costs $300-$1000. This is too expensive for everyday transactions.

### The Consequence
People "blind sign," agreeing to hidden traps like **Uncapped Liability**, **Predatory Termination Clauses**, or **Data Rights Forfeiture**. They don't need a lawyer to draft a new contract; they just need a "pair of eyes" to warn them before they sign.

---

## 2. Our Solution: DocuScout

DocuScout is an **Agentic AI Analysis Engine**. It acts as a 24/7 "Risk Radar." It does not write or alter documents. Instead, it reads them instantly, highlights potential dangers based on strict laws and safety rules, and answers your questions.

### Key Capabilities
*   **Visual Risk Mapping**: Ingests a PDF and highlights risky clauses in **Red/Yellow** directly on the UI.
*   **Dynamic Knowledge Injection**: Can learn new laws (e.g., "Article 44 of Indian Constitution") from a URL to instantly update its detection rules.
*   **Agentic Reflexion**: Uses a "Critic" agent to double-check risks, ensuring it doesn't scare the user with false alarms.
*   **Q&A Assistant**: A dedicated Chat Agent to answer specific user doubts about the document.

---

## 3. The Core Innovation: Dynamic Playbook

Most AI tools use hard-coded prompts. DocuScout features a **Self-Populating Knowledge Base**.

**The Problem**: Laws change. A contract valid in New York might be illegal in Bangalore.

**The "Researcher" Agent**:
1.  The user pastes a link (e.g., a government notification about new Labor Laws or a company policy page).
2.  The Researcher Agent scrapes the URL, understands the legal constraints, and updates the Playbook (JSON Rules).
3.  **Result**: DocuScout immediately knows that a clause violating this new link is "High Risk."

---

## 4. Architecture & Workflow

We use a **Multi-Agent System** tailored for "Read-only Analysis."

### Phase 1: Knowledge Setup (Optional)
*   **User Action**: "Here is a link to the Indian Contract Act updates."
*   **Researcher Agent**: 
    1. Scrapes URL
    2. Extracts Constraints
    3. Updates `Playbook.json` (e.g., "Non-competes are void in this region").

### Phase 2: The Analysis Loop (The Core)
1.  **Ingestion**: User uploads PDF. Text is extracted via OCR.
2.  **Orchestrator**: Determines doc type (e.g., "NDA") and selects the correct Playbook.
3.  **Agent A (Clause Hunter)**: Scans the document to find specific sections (e.g., "Find the Indemnity clause").
4.  **Agent B (Risk Auditor)**: Checks the text against the Playbook.
    *   *Logic*: "The Playbook says payment must be within 45 days. This clause says 90 days."
    *   *Output*: Flags as Risk Level: High.
5.  **Agent C (The Critic)**: Reflexion Layer.
    *   *Role*: The "Senior Partner."
    *   *Check*: "Agent B flagged this as high risk. Is it really? Or is this standard industry practice?"
    *   *Outcome*: Confirms the risk or dismisses it to prevent false alarms.

### Phase 3: The Interaction
*   **The Visualizer**: Displays the document with Highlighted Annotations. Hovering over a highlight explains why it is risky.
*   **The Q&A Agent**: An independent RAG module.
    *   *User*: "Does this contract say I lose my IP?"
    *   *Agent*: Searches the doc vector store -> "No, Clause 4.2 states you retain all IP rights."

---

## 5. Agent Roles Breakdown

| Agent Name | Role | Responsibility |
| :--- | :--- | :--- |
| **Orchestrator** | The Manager | Routes the document and manages the workflow state. |
| **Researcher** | The Student | **Dynamic Capability**. Fetches external web pages to learn new compliance rules on the fly. |
| **Clause Hunter** | The Scanner | Locates specific paragraphs relevant to the Playbook rules. |
| **Risk Auditor** | The Detective | Analyzes the text for deviations from safety standards. |
| **The Critic** | The Judge | Validates the Auditor's findings. Ensures we don't flag harmless things as "Dangerous." |
| **Q&A Bot** | The Consultant | Answers free-form user questions based solely on the document context. |

---

## 6. Generalizability (The "Universal Scout")

DocuScout is a **Compliance Analysis Engine**. You can use it for any industry by changing the Input and the Playbook.

| Domain | Project Adaptation | Input | The "Playbook" Source (URL) |
| :--- | :--- | :--- | :--- |
| **Legal** | **DocuScout** | Contracts | Contract Law / Company Policy |
| Healthcare | MediScout | Patient Discharge Summaries | Insurance Coverage Guidelines |
| Construction | SafetyScout | Site Inspection Reports | OSHA Safety Manuals |
| Education | ThesisScout | Research Papers | University Citation/Plagiarism Rules |
| Finance | AuditScout | Expense Reports | Company Travel & Expense Policy |

---

## 7. Hackathon Tech Stack

*   **Orchestration**: Custom Python Agents using **Google Gen AI SDK**.
*   **LLM**: `Gemini 1.5 Flash` (Fast & Multimodal) or `Gemini 1.5 Pro` (Reasoning).
*   **Knowledge Base**: `ChromaDB` (Vector Store for Q&A and Rules).
*   **Tools**: Native Python Tools (for the Researcher Agent).
*   **Frontend**: `Streamlit`.
*   **Key Library**: `streamlit-pdf-viewer` or `streamlit-annotation-tools` to show the Highlights.

---


