# DocuScout Project Analysis

## Project Overview
DocuScout is an **Intelligent Risk Radar for Contracts & Documents** built using Google ADK (Agent Development Kit). It's a multi-agent system that analyzes legal documents to identify risks, extract clauses, and provide compliance checking.

## Architecture: Multi-Agent System

### Main Orchestrator (`Agent/agent.py`)
- **Role**: Routes user requests to appropriate subagents
- **Model**: Gemini 2.5 Flash via LiteLLM proxy
- **Subagents**: 7 specialized agents

### Agent Breakdown

#### 1. **Greeter Agent** (`Subagents/Greeter/`)
- **Purpose**: Welcomes users and explains DocuScout capabilities
- **Tools**: None (pure LLM agent)
- **Function**: Provides initial user interaction

#### 2. **FileReader Agent** (`Subagents/FileReader/`)
- **Purpose**: Ingests PDF documents into Google File Search Store
- **Tools**: `ingest_documents()`
- **Function**: 
  - Creates/finds "DocuScout Store" in Google File Search
  - Uploads PDFs from `DB/` folder
  - Makes documents available for RAG queries

#### 3. **ClauseHunter Agent** (`Subagents/ClauseHunter/`) ⚠️ **COMPLEX STRUCTURE**
- **Purpose**: Extracts legal clauses and entities from documents to build a "Dynamic Playbook"
- **Architecture**: Multi-layered with parallel and sequential execution
  - **Layer 1**: `ClauseDataHarvester` (ParallelAgent) - Runs 4 extraction tools concurrently
  - **Layer 2**: `ClauseFinder` (LlmAgent) - Aggregates and curates results
  - **Layer 3**: `PlaybookPipeline` (SequentialAgent) - Orchestrates the flow
  - **Layer 4**: `ClauseHunter` (LlmAgent) - Main interface

**Subagents of ClauseHunter:**
  - **Gliner**: Zero-shot NER using GLiNER model (`urchade/gliner_large-v2.1`)
    - Extracts: statute, act, provision, section, article, clause, regulation, rule, code, law, ordinance, amendment
  - **LexNLP**: Regex-based extraction
    - Extracts: Acts, monetary amounts, dates, case citations
  - **OpenNyAI**: Spacy model for Indian/Commonwealth legal documents
    - Model path: `/home/shtlp_0107/Desktop/LawModels/OpenNyAI/en_legal_ner_model/...`
    - Extracts: STATUTE and PROVISION entities
  - **RAG**: Semantic search using Google File Search
    - Extracts: Complex legal concepts and clauses via LLM synthesis

**Tools:**
  - `fetch_raw_extraction_results()`: Collects results from all 4 subagents
  - `save_curated_playbook()`: Saves processed playbook to session state
  - `export_playbook_to_disk()`: Writes playbook to `dynamic_playbook.json`

#### 4. **Researcher Agent** (`Subagents/Researcher/`)
- **Purpose**: Researches legal updates and amendments for laws found in playbook
- **Tools**:
  - `read_playbook_entities()`: Reads entities from dynamic_playbook.json
  - `batch_search_legal_updates()`: Parallel searches using Tavily API (whitelisted Indian gov domains)
  - `save_compliance_updates()`: Saves results to `compliance_updates.json`
- **Function**: Keeps playbook updated with 2024-2025 legal amendments

#### 5. **RiskAuditor Agent** (`Subagents/RiskAuditor/`)
- **Purpose**: Analyzes documents for deviations from Playbook safety standards
- **Tools**: None (pure LLM agent)
- **Function**: Flags violations and assigns risk levels (High, Medium, Low)

#### 6. **Critic Agent** (`Subagents/Critic/`)
- **Purpose**: Cross-references Contract Playbook against Legal Updates (Gap Analysis)
- **Tools**:
  - `fetch_audit_context()`: Loads playbook and compliance updates
  - `fetch_law_context_from_document()`: Extracts specific law mentions from PDFs
  - `save_audit_report()`: Saves final report to `risk_audit_report.md`
- **Function**: Performs compliance verification and generates audit reports

#### 7. **Consultor Agent** (`Subagents/Consultor/`)
- **Purpose**: Q&A agent for document content
- **Tools**: `query_docs()` - Uses Google File Search to answer questions
- **Function**: Answers user questions based on ingested documents

## Workflow

### Phase 1: Document Ingestion
1. User uploads PDFs to `DB/` folder
2. **FileReader** ingests documents into Google File Search Store

### Phase 2: Clause Extraction (ClauseHunter)
1. **ClauseDataHarvester** runs 4 extraction tools in parallel:
   - Gliner (NER)
   - LexNLP (Regex)
   - OpenNyAI (Spacy)
   - RAG (Semantic Search)
2. **ClauseFinder** aggregates results, deduplicates, and formats
3. Playbook saved to `dynamic_playbook.json`

### Phase 3: Legal Research (Researcher)
1. Reads entities from playbook
2. Batch searches for 2024-2025 updates via Tavily
3. Saves compliance updates to `compliance_updates.json`

### Phase 4: Risk Analysis (Critic)
1. Loads playbook and compliance updates
2. Performs gap analysis
3. Generates audit report in `risk_audit_report.md`

### Phase 5: Q&A (Consultor)
- Users can query documents anytime using semantic search

## Technical Stack

### Core Libraries
- **Google ADK**: Agent orchestration framework
- **LiteLLM**: LLM proxy (using Gemini 2.5 Flash)
- **Google GenAI**: File Search API
- **GLiNER**: Zero-shot NER model
- **LexNLP**: Legal text extraction library
- **Spacy**: NLP framework (for OpenNyAI)
- **Tavily**: Web search API for legal research
- **PyPDF2**: PDF text extraction

### Environment Variables Required
- `LITELLM_PROXY_API_BASE`
- `LITELLM_PROXY_GEMINI_API_KEY`
- `GEMINI_API_KEY`
- `TAVILY_API_KEY`

## Potential Issues Identified

### 1. **FileReader Tool Not Async** ⚠️
- `ingest_documents()` in `FileReader/tools.py` is a regular function, not async
- But it's used in an async agent context
- **Impact**: May cause blocking issues

### 2. **Consultor Tool Not Async** ⚠️
- `query_docs()` in `Consultor/tools.py` is a regular function, not async
- **Impact**: May cause blocking issues

### 3. **OpenNyAI Model Path Hardcoded** ✅ FIXED
- ~~Hardcoded path: `/home/shtlp_0107/Desktop/LawModels/OpenNyAI/...`~~
- **Solution**: Now uses `OPENNYAI_MODEL_PATH` environment variable with multiple fallback locations
- **Status**: Configurable via environment variable, with automatic fallback to common locations

### 4. **Error Handling in ClauseHunter**
- Multiple async operations that could fail
- Need to verify error propagation through ParallelAgent → SequentialAgent chain

### 5. **State Management**
- Heavy reliance on `tool_context.state` for data passing
- Keys used: `clausehunter:gliner`, `clausehunter:lexnlp`, `clausehunter:opennyai`, `clausehunter:rag`, `clausehunter:playbook`, `researcher:targets`
- **Risk**: State could be lost between agent calls if not properly managed

## File Structure

```
DocuScout/
├── Agent/
│   ├── agent.py (Main Orchestrator)
│   └── Subagents/
│       ├── Greeter/
│       ├── FileReader/
│       ├── ClauseHunter/ (Complex nested structure)
│       │   ├── agent.py
│       │   ├── tools.py
│       │   └── Subagents/
│       │       ├── Gliner/
│       │       ├── LexNLP/
│       │       ├── OpenNyAI/
│       │       └── RAG/
│       ├── RiskAuditor/
│       ├── Critic/
│       ├── Researcher/
│       └── Consultor/
├── DB/ (PDF storage)
├── requirements.txt
└── README.md
```

## Testing Recommendations

1. **Test ClauseHunter Pipeline**:
   - Verify all 4 subagents execute successfully
   - Check state persistence between agents
   - Validate playbook JSON structure

2. **Test Async Functions**:
   - Convert FileReader and Consultor tools to async
   - Test error handling in parallel execution

3. **Test Model Loading**:
   - Verify GLiNER model downloads correctly
   - Check OpenNyAI model path exists
   - Test with sample PDFs

4. **Test State Management**:
   - Verify data flows correctly through agent chain
   - Test with multiple documents

## Next Steps for Debugging

1. Check if ClauseHunter errors are related to:
   - Async/await issues
   - Model loading failures
   - State management problems
   - Import errors in subagents

2. Review error logs to identify specific failure point

3. Test each subagent independently before testing full pipeline

