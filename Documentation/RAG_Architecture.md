# DocuScout RAG Architecture

This document explains the Retrieval-Augmented Generation (RAG) pipeline implemented in DocuScout using **Google File Search**.

## Workflow Overview

The system consists of two main agents:
1.  **FileReader Agent**: Handles document ingestion.
2.  **Consultor Agent**: Handles Q&A by querying the ingested documents.


#### NOTE : we are using the same DB for ingestion -> reingestion will cause appending to the existing store the files

### Visual Flow

**Ingestion Phase:**
👤 **User** ──(Ingest)──> 📂 **FileReader Agent** ──(Upload)──> ☁️ **Google File Search**

**Q&A Phase:**
👤 **User** ──(Ask)──> 🧐 **Consultor Agent** ──(Query)──> ☁️ **Google File Search** ──(Retrieve)──> 🗣️ **Answer**

## Agent Details

### 1. FileReader Agent
*   **Role**: Checks the `DB/` folder for PDF documents.
*   **Mechanism**:
    *   Connects to Google GenAI.
    *   Checks if a File Search Store named **"DocuScout Store"** exists.
    *   If yes, it reuses it; if no, it creates one.
    *   Uploads valid PDFs to this store.
*   **Key Feature**: **Incremental Ingestion**. New files are added to the existing store, allowing the database to grow over time without re-processing old files.

### 2. Consultor Agent
*   **Role**: Answers user queries based on valid facts from the documents.
*   **Mechanism**:
    *   Accesses the shared **"DocuScout Store"**.
    *   Uses Google's semantic search to find relevant passages.
    *   Synthesizes an answer using the `gemini-2.5-flash` model.

## Example Query

**Question:**
> "What is the purchase price for the AgroBox in the Rubicon Agriculture agreement?"

**Answer (retrieved from actual ingested contract):**
> The purchase price is **$77,000.00**.
> *   Base Price: $80,000.00
> *   Transportation: +$2,000.00
> *   Discount: -$5,000.00
