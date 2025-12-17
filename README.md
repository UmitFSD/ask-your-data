# 🤖 Azure Enterprise RAG Chatbot (OCR Enabled)

This project is a Streamlit-based **"Ask Your Data"** chatbot that allows users to ask questions over complex PDF documents (including academic papers and tables) using a Retrieval-Augmented Generation (RAG) approach.

The system uses a **hybrid parsing strategy**: it extracts digital text instantly using local libraries and falls back to **Azure AI Document Intelligence** for OCR only when necessary. Data is indexed into **Azure AI Search** and queried using **Azure OpenAI (GPT-4o)** with a security-aware prompt.

## 🚀 What This Application Does

*   **Hybrid PDF Processing:** Detects if a PDF is digital or scanned. Uses `PyMuPDF` for sub-second text extraction and falls back to `Azure AI Document Intelligence` for images.
*   **Smart Chunking:** Uses page-based or large-window chunking to keep tables and academic contexts intact.
*   **Vector Search:** Stores embeddings in **Azure AI Search** for semantic retrieval.
*   **Citation & Sources:** Displays the exact source document and **page numbers** used to generate the answer.
*   **Security Persona:** Includes a "Security Researcher" system prompt to allow analysis of sensitive academic topics (e.g., "jailbreak studies") without triggering false refusals.
*   **Chat Interface:** Provides a conversational interface via Streamlit.

## 🏗 High-Level Architecture

1.  **PDF Upload:** User uploads a file via Streamlit.
2.  **Processing:** 
    *   *Fast Path:* Extract text via PyMuPDF.
    *   *Slow Path:* OCR via Azure AI Document Intelligence (if text < 50 chars).
3.  **Indexing:** Text is split into chunks and embedded using `text-embedding-ada-002`, then stored in Azure AI Search.
4.  **Retrieval:** Top-k (`k=10`) relevant chunks are retrieved based on the user query.
5.  **Generation:** GPT-4o generates an answer using the retrieved context.
6.  **UI Display:** Answer + Expandable "References" section.

## 🛠 Tech Stack

*   **Python** (3.10+)
*   **Streamlit** (UI)
*   **Azure OpenAI** (`GPT-4o`)
*   **Azure OpenAI Embeddings** (`text-embedding-ada-002`)
*   **Azure AI Search** (Vector Store)
*   **Azure AI Document Intelligence** (OCR Fallback)
*   **PyMuPDF** (Fast Text Extraction)
*   **LangChain** (Orchestration & Chains)

## 📝 Design Notes

*   **Index Management:** Uses a fixed index name to ensure consistency between ingestion and retrieval.
*   **Prompt Engineering:** The prompt is tuned to handle academic papers containing sensitive keywords (like "attacks" or "malware") by framing the AI as a researcher.
*   **Reference Visibility:** The UI includes an expander to show the raw text chunks and page numbers for verification (anti-hallucination).

## ⚠️ Current Limitations

*   Single PDF ingestion at a time.
*   Chat history is session-based (clears on refresh).
*   No multi-modal support (images/graphs in PDF are not yet analyzed, only text/tables).

## 🔮 Future Improvements

*   Support for multi-file upload.
*   Add evaluation metrics (RAGAS or TruLens) for answer quality.
*   Implement "Chat with Images" using GPT-4o Vision for graph analysis.
*   Add persistent database for chat history.

## 👤 Author
**Umit**
