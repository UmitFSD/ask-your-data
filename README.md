# Azure Enterprise RAG Assistant (OCR-Enabled) — PoC

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat&logo=python)
![Azure](https://img.shields.io/badge/Azure%20OpenAI-GPT--4o-0078D4?style=flat&logo=microsoftazure)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit)
![Status](https://img.shields.io/badge/Status-Proof%20of%20Concept-orange)

This project is a forward-deployed style proof of concept (PoC) that demonstrates how large language models can be applied to enterprise PDF documents using a **Retrieval-Augmented Generation (RAG)** approach.

The focus of this PoC is not full production scalability, but validating **retrieval quality, explainability, and user experience** under real-world enterprise constraints such as scanned documents, complex layouts, and hallucination risk.

---

## 📸 Interface Preview



---<img width="1167" height="689" alt="dashboard" src="https://github.com/user-attachments/assets/291c6cd7-9814-4358-9228-6298c051b848" />


## 🎯 Problem Statement

Enterprise knowledge is often stored in PDF documents that are difficult to work with using LLMs:

*   **Scanned Content:** Documents may be partially or fully scanned.
*   **Complex Layouts:** Content often includes tables, long sections, and academic formatting.
*   **Trust Issues:** Ungrounded LLM responses can introduce hallucination risk and reduce trust.

This PoC explores how to safely enable “ask your data” scenarios while preserving traceability, context integrity, and controlled model behaviour.

---

## 🚀 What This PoC Demonstrates

*   **Hybrid PDF Processing:** A fast text extraction path (PyMuPDF) with an automatic **OCR fallback** (Azure AI Document Intelligence) for scanned pages.
*   **Context-Preserving Chunking:** Avoids breaking tables and structured content across chunks.
*   **Semantic Retrieval:** Uses vector search for deep understanding of queries.
*   **Grounded Generation:** Answers are generated using *only* the retrieved context.
*   **Transparent Citations:** Page-level citation visibility for user verification.
*   **Smart Conversation Routing:** Distinguishes between conversational follow-ups (chat) and document search requests (RAG).
*   **Security Persona:** Controlled prompt persona to handle sensitive academic topics without false refusals.

---

## 🏗 High-Level Architecture

1.  **Upload:** The user uploads a PDF through the Streamlit interface.
2.  **Processing:**
    *   Digital text is extracted using **PyMuPDF**.
    *   If insufficient text is found (scanned page), **OCR** is applied using **Azure AI Document Intelligence**.
3.  **Indexing:** Extracted text is split into large overlapping chunks, embedded using `text-embedding-ada-002`, and stored in **Azure AI Search**.
4.  **Routing:** User queries are classified as either *conversational follow-ups* or *document search requests*.
5.  **Retrieval & Generation:** Relevant chunks are retrieved and passed to **GPT-4o** for answer generation.
6.  **Display:** Answers are displayed along with expandable references showing source text and page numbers.

---

## 🛠 Technology Stack

*   **Python 3.10+**
*   **Streamlit:** User Interface
*   **Azure OpenAI:** GPT-4o (Reasoning) & text-embedding-ada-002 (Embeddings)
*   **Azure AI Search:** Vector Store
*   **Azure AI Document Intelligence:** OCR Fallback
*   **PyMuPDF:** Fast PDF Parsing
*   **LangChain:** Orchestration & Chains

---

## ⚖️ Design Decisions and Trade-Offs

### Fixed Index Strategy (V1)
The PoC uses a single, fixed Azure AI Search index. New documents are appended to the same index rather than creating a new index per upload.
*   *Why:* To avoid routing ambiguity during conversational retrieval and keep the PoC focused on retrieval quality/UX rather than index orchestration.
*   *Future:* Index versioning (V2, V3) or tenant isolation would be introduced for production.

### Hybrid Parsing Strategy
OCR is used only when necessary to control cost and latency.
*   *Why:* A simple text-length threshold determines when OCR is triggered. This reflects a common enterprise trade-off between accuracy and performance.

### Conversation Routing
A lightweight router distinguishes between conversational follow-ups and new search queries.
*   *Why:* This reduces unnecessary retrieval calls (cost saving) and improves response relevance (better UX).

### Explainability First
The PoC prioritizes transparency.
*   *Why:* Source documents and page numbers are always visible via "Reference Tabs". The system favours explainability over aggressive automation to build user trust.

---

## ⚠️ PoC Scope and Known Limitations

This PoC intentionally **does not** include:
*   Multi-tenant isolation
*   Concurrent user handling
*   Index lifecycle automation
*   Full observability and telemetry
*   Authentication and authorization
*   Persistent chat history (Session based only)

---

## 🔮 Production-Oriented Next Steps

If extended beyond PoC, the following areas would be addressed:
*   Microservices decomposition for ingestion, retrieval, and chat.
*   Tenant-aware index strategies.
*   Structured logging and monitoring.
*   Evaluation frameworks (RAGAS or TruLens).
*   Persistent conversation storage (CosmosDB/PostgreSQL).
*   Fine-grained access control (RBAC).

---

## Quick Start & How to Use

Follow these steps to set up and run the project locally on your machine.

### 1. Clone the Repository
Open your terminal and clone the repo:
```bash
git clone https://github.com/UmitFSD/ask-your-data.git
cd ask-your-data

2. Install Dependencies
Make sure you have Python 3.10+ installed. Then install the required libraries: pip install -r requirements.txt

3. Configure Azure Credentials
Since this project uses Azure services, you need to provide your API keys.
Create a folder named .streamlit in the root directory.
Inside that folder, create a file named secrets.toml.
Paste your Azure keys into the file like this:

# .streamlit/secrets.toml

AZURE_OPENAI_KEY = "your-openai-key-here"
AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"

AZURE_SEARCH_KEY = "your-search-key-here"
AZURE_SEARCH_ENDPOINT = "https://your-search-service.search.windows.net"

AZURE_DOCUMENT_INTELLIGENCE_KEY = "your-doc-intel-key-here"
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = "https://your-form-recognizer.cognitiveservices.azure.com/"

4. Run the Application
Start the Streamlit app: streamlit run azure_rag.py

The application will open automatically in your browser at http://localhost:8501.

## 👨‍💻 Author

**Ümit Şener**  
Senior Cloud & AI Specialist
