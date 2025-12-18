# Azure Enterprise RAG Assistant (OCR-Enabled) — PoC

This project is a forward-deployed style proof of concept (PoC) that demonstrates how large language models can be applied to enterprise PDF documents using a Retrieval-Augmented Generation (RAG) approach.

The focus of this PoC is not full production scalability, but validating retrieval quality, explainability, and user experience under real-world enterprise constraints such as scanned documents, complex layouts, and hallucination risk.

---

## Problem Statement

Enterprise knowledge is often stored in PDF documents that are difficult to work with using LLMs:

- Documents may be partially or fully scanned
- Content often includes tables, long sections, and academic formatting
- Ungrounded LLM responses can introduce hallucination risk and reduce trust

This PoC explores how to safely enable “ask your data” scenarios while preserving traceability, context integrity, and controlled model behaviour.

---

## What This PoC Demonstrates

- Hybrid PDF processing with a fast text extraction path and an OCR fallback
- Context-preserving chunking to avoid breaking tables and structured content
- Semantic retrieval using vector search
- Grounded answer generation using retrieved context only
- Page-level citation visibility for verification
- Conversation-aware routing between chat and document search
- Controlled prompt persona to handle sensitive academic topics without false refusals

---

## High-Level Architecture

1. The user uploads a PDF through the Streamlit interface.
2. The document is processed page by page:
   - Digital text is extracted using PyMuPDF.
   - If insufficient text is found, OCR is applied using Azure AI Document Intelligence.
3. Extracted text is split into large overlapping chunks.
4. Chunks are embedded using text-embedding-ada-002 and stored in Azure AI Search.
5. User queries are classified as either conversational follow-ups or document search requests.
6. Relevant chunks are retrieved and passed to GPT-4o for answer generation.
7. Answers are displayed along with expandable references showing source text and page numbers.

---

## Technology Stack

- Python 3.10+
- Streamlit for the user interface
- Azure OpenAI (GPT-4o)
- Azure OpenAI Embeddings (text-embedding-ada-002)
- Azure AI Search as the vector store
- Azure AI Document Intelligence for OCR fallback
- PyMuPDF for fast PDF parsing
- LangChain for orchestration and prompt chaining

---

## Design Decisions and Trade-Offs

### Fixed Index Strategy (V1)

The PoC uses a single, fixed Azure AI Search index. New documents are appended to the same index rather than creating a new index per upload.

This decision was made deliberately to:
- Avoid routing ambiguity during conversational retrieval
- Keep the PoC focused on retrieval quality and UX rather than index orchestration
- Simplify demo and workshop scenarios

Index versioning (V2, V3, etc.) would be introduced only for breaking changes such as schema evolution, retrieval strategy changes, or tenant isolation requirements.

---

### Hybrid Parsing Strategy

OCR is used only when necessary to control cost and latency. A simple text-length threshold determines when OCR is triggered. This reflects a common enterprise trade-off between accuracy and performance.

---

### Conversation Routing

A lightweight router distinguishes between:
- Conversational follow-ups that rely on chat history
- Questions that require document retrieval

This reduces unnecessary retrieval calls and improves response relevance.

---

### Explainability First

The PoC prioritizes transparency:
- Source documents and page numbers are always visible
- Raw retrieved text can be inspected
- The system favours explainability over aggressive automation

---

## PoC Scope and Known Limitations

This PoC intentionally does not include:

- Multi-tenant isolation
- Concurrent user handling
- Index lifecycle automation
- Full observability and telemetry
- Authentication and authorization
- Persistent chat history

The system assumes:
- A single user
- A single active document corpus
- Interactive demo or workshop usage

---

## Production-Oriented Next Steps

If extended beyond PoC, the following areas would be addressed:

- Service decomposition for ingestion, retrieval, and chat
- Tenant-aware index strategies
- Structured logging and monitoring
- Evaluation frameworks such as RAGAS or TruLens
- Persistent conversation storage
- Fine-grained access control
- Cost and latency optimisation

---

## Author

Ümit Şener  
Senior Cloud & AI Specialist  
Dublin, Ireland
