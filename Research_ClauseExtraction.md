# Research Report: Legal Clause Extraction

To implement the `ClauseHunter` agent, I have researched various methods for accurately extracting clauses from legal documents.

## 1. LLM-Based Extraction (Recommended for Agentic Workflow)
Given we are already using `google-genai` and `Gemini`, this is the most flexible and "agentic" approach.

*   **Method**: Zero-shot or Few-shot prompting.
*   **Strategy**:
    *   **Direct Extraction**: "Extract the 'Termination', 'Indemnity', and 'Confidentiality' clauses from this text."
    *   **Structured Output**: Ask for JSON output to easily parse the results (e.g., `[{"name": "Termination", "text": "..."}]`).
    *   **RAG**: Since contracts can be long, we can use the existing File Search Store to retrieve relevant chunks first (e.g., "Find sections discussing termination") and then extract the precise clause text from those chunks.
*   **Pros**: No extra infrastructure; handles varied language well; integrates naturally with existing `Consultor` style logic.
*   **Cons**: Can hallucinate if not grounded; context window limits (mitigated by File Search).

## 2. Google Cloud Document AI (Contract Parser)
*   **Tool**: Google Cloud [Document AI - Contract Processor](https://cloud.google.com/document-ai/docs/processors-list#contract-processor).
*   **Capabilities**: Automatically extracts entities like "Termination Date", "Governing Law", "Contract Amount", etc.
*   **Pros**: highly accurate, purpose-built model by Google.
*   **Cons**: Separate API usage/pricing; strictly defined schema (might miss custom clause types unless trained).

## 3. NLP Libraries (Python) - Open Source & Free

To build a "Dynamic Playbook" without paying for Google Document AI, we can use these free libraries:

*   **LexNLP** (Best Standard Option)
    *   **Features**: Specifically designed for "real-world" unstructured legal text. Excellent at cleaning, segmentation, and extracting specific entities (dates, money, citations).
    *   **Pros**: Free, python-native, handles messy text well.
    *   **Use Case**: Pre-processing and cleaning text from the DB before sending specific chunks to the LLM.

*   **HuggingFace Models (CUAD Fine-Tuned)**
    *   **Models**: `OthmaneAbder2303/legalbert-cuad-clauses`, `nlpaueb/legal-bert-base-uncased`.
    *   **Dataset**: Trained on **CUAD** (Contract Understanding Atticus Dataset), which has 41 types of legal clauses labeled by experts.
    *   **Pros**: Runs locally (free), highly specific to clauses like "Governing Law", "Anti-Assignment", etc.
    *   **Cons**: Heavier to run (requires PyTorch/Transformers); might be slow on CPU.

*   **OpenContracts** (Framework level)
    *   An entire open-source pipeline for extracting data from contracts. It uses a mix of layout parsers and LLMs. We can borrow its "schema definition" concepts for our dynamic playbook key-value pairs.

## 4. Proposed Hybrid "ClauseHunter" Approach

The user requested a **Dynamic Playbook** (merging clauses into a JSON). Here is the proposed architecture:

1.  **Step 1: Rough Retrieval (Google File Search)**
    *   Use `Gemini` with File Search to identify *where* in the document likely clauses exist (e.g., "Find the Liability section"). This creates high-relevance "chunks".

2.  **Step 2: Precise Extraction (LLM + Structured Output)**
    *   Feed those chunks to `Flash-2.5` with a **structured prompt** asking it to output JSON matching our desired schema.
    *   *Prompt*: "Analyze this text. Extract the 'Termination Clause' text exactly. Return JSON: `{ 'clause_type': 'Termination', 'text': '...', 'confidence': 'High' }`."

3.  **Step 3 (Optional Enhancement): Local Verification**
    *   If specific regex/rules are needed (e.g., finding all money amounts), use **LexNLP** on the extracted text to validate it.

### Why this finding?
This "Assembler" pattern allows us to:
1.  **Avoid cost** of Document AI.
2.  **Ensure accuracy** by using RAG (File Search) to find the needle, and LLM (Flash) to thread it.
3.  **Result**: A `dynamic_playbook.json` file containing all extracted clauses key-value pairs.

## 5. Statistical & Rule-Based Legal NER (For Acts & Statutes)

If the goal is specifically **Legal Named Entity Recognition (Legal-NER)** to extract Statutes, Acts, and Provisions (e.g., "Minimum Wages Act, 1948"), here are the best specific tools:

### A. OpenNyAI (Best for Indian/Commonwealth Law)
*   **Focus**: Built specifically for **Indian Legal Text**.
*   **Detection**: Extracts `STATUTE` (The Act) and `PROVISION` (The Section).
*   **Tech**: Spacy + Transformers.
*   **License**: MIT (Free).

### B. Blackstone (Best for General English Law)
*   **Focus**: Specialized spaCy model for legal texts (unmaintained but effective).
*   **Detection**: `INSTRUMENT` (Legislative instrument) and `PROVISION` (Section).
*   **Tech**: Spacy.

### C. Legal-BERT (Hugging Face)
*   **Focus**: High-accuracy token classification.
*   **Models**: `nlpaueb/legal-bert-base-uncased` (Global) or `law-ai/InLegalBERT` (Indian).
*   **Tech**: Transformers (Heavy).

### D. The "Hybrid" Approach (Recommended for Speed)
*   **Focus**: Rule-based Spacy EntityRuler.
*   **Why**: Legal acts usually follow a strict Capitalized Pattern ("The [Name] Act, [Year]").
*   **Pros**: Fast, free, accurate for standard formats.
*   **Implementation**:
    ```python
    # Example Spacy EntityRuler Pattern
    patterns = [
        {"label": "LEGAL_ACT", "pattern": [
            {"LOWER": "the", "OP": "?"},
            {"IS_TITLE": True, "OP": "+"},
            {"LOWER": "act"},
            {"SHAPE": "dddd", "OP": "?"} # Year
        ]}
    ]
    ```


## We can use some of the above tools and then combine the results to a Playbook.json file for the clauses which can be used by the research agent to update the Playbook.json file