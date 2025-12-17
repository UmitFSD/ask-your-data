ask-your-data
Azure Enterprise RAG Chatbot (OCR Enabled)
This project is a Streamlit-based “Ask Your Data” chatbot that allows users to ask questions over PDF documents using a Retrieval-Augmented Generation (RAG) approach.

Documents are processed with Azure AI Document Intelligence for OCR and layout-aware text extraction, indexed into Azure AI Search as vectors, and queried using Azure OpenAI (GPT-4o).

What This Application Does
Uploads a PDF document via a Streamlit UI
Extracts text using Azure AI Document Intelligence (prebuilt-layout)
Splits text into chunks for retrieval
Generates embeddings using Azure OpenAI
Stores vectors in Azure AI Search
Retrieves relevant chunks and answers questions using GPT-4o
Refuses to hallucinate when the answer is not present in the document
High-Level Architecture
PDF upload via Streamlit
OCR & layout extraction with Azure AI Document Intelligence
Text chunking
Vector indexing in Azure AI Search
Retrieval of top-k relevant chunks
Answer generation with Azure OpenAI (RAG)
Tech Stack
Python
Streamlit
Azure OpenAI (GPT-4o)
Azure OpenAI Embeddings (text-embedding-3-large)
Azure AI Search (Vector Store)
Azure AI Document Intelligence
LangChain
Design Notes
The system uses a strict prompt to avoid hallucinations.
If the answer is not found in the retrieved context, the model responds accordingly.
Chunk size and retrieval parameters are intentionally simple and can be tuned further.
Current Limitations
Single PDF ingestion at a time
No citation display in the UI
No automated evaluation or monitoring
Index lifecycle management is manual
Future Improvements
Show retrieved chunks and citations in the UI
Add evaluation metrics for answer quality
Improve index management and deduplication
Add latency and token usage tracking
Author
Umit
