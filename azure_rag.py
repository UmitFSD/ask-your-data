import streamlit as st
import os
import tempfile
import io
import time

# --- Azure & PDF Libraries ---
import fitz  # PyMuPDF
from PIL import Image
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

# --- LangChain Libraries ---
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

# ==========================================
# 1. UI CONFIGURATION & CSS (GRAYSCALE / NO RED)
# ==========================================
st.set_page_config(
    page_title="Ask Your Data",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kırmızıyı Yok Eden ve Gri Temayı Zorlayan CSS
st.markdown("""
<style>
    /* --- 1. ANA DEĞİŞKENLERİ EZ (Kırmızıyı Kaynağında Kurut) --- */
    :root {
        --primary-color: #555555;
    }

    /* --- 2. SLIDER: KIRMIZIYI BUL VE GRİ YAP --- */
    
    /* Slider Çubuğu (Dolu Kısım) */
    div.stSlider > div[data-baseweb="slider"] > div > div {
        background-color: #555555 !important;
    }
    
    /* Slider Yuvarlağı (Handle) */
    div.stSlider > div[data-baseweb="slider"] > div > div > div[role="slider"] {
        background-color: #555555 !important;
        border-color: #555555 !important;
        box-shadow: none !important;
    }
    
    /* Slider Yuvarlağı (Focus/Tıklanmış Hali) */
    div.stSlider > div[data-baseweb="slider"] > div > div > div[role="slider"]:focus-visible {
        box-shadow: 0 0 0 2px rgba(85, 85, 85, 0.3) !important;
    }

    /* Rakamlar (0.00, 5 vs.) */
    div[data-testid="stSlider"] div[data-testid="stMarkdownContainer"] p {
        color: #555555 !important; 
        font-weight: 600;
    }
    
    /* Min/Max Değerleri (Slider altındaki küçük sayılar) */
    div[data-testid="stTickBar"] > div {
        color: #555555 !important;
    }

    /* --- 3. BUTONLAR (Gri Tema) --- */
    div.stButton > button:first-child {
        background-color: #555555 !important; /* Antrasit Gri */
        color: white !important;
        border-radius: 6px;
        border: none;
        box-shadow: none !important;
    }
    div.stButton > button:hover {
        background-color: #333333 !important; /* Daha Koyu Gri */
        color: white !important;
    }
    div.stButton > button:focus {
        background-color: #555555 !important;
        color: white !important;
    }

    /* --- 4. GENEL UI DÜZELTMELERİ --- */
    
    /* Linkler */
    a {
        color: #555555 !important;
        text-decoration: underline;
    }

    /* Başlık Rengi */
    .main-header {
        font-size: 2.2rem;
        color: #333333; /* Koyu Gri */
        font-weight: 700;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-top: -5px;
    }
    
    /* Chat Balonları */
    .stChatMessage {
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        padding: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Main Header
col1, col2 = st.columns([0.6, 9])
with col1:
    st.markdown("# 🤖") 
with col2:
    st.markdown('<div class="main-header">Ask Your Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Enterprise RAG Assistant | Powered by Azure OpenAI</div>', unsafe_allow_html=True)

st.divider()

# ==========================================
# 2. SETTINGS & SECRETS
# ==========================================
AZURE_INDEX_NAME = "umit-rag-production-v1"

try:
    OPENAI_API_KEY = st.secrets["AZURE_OPENAI_KEY"]
    OPENAI_ENDPOINT = st.secrets["AZURE_OPENAI_ENDPOINT"]
    SEARCH_KEY = st.secrets["AZURE_SEARCH_KEY"]
    SEARCH_ENDPOINT = st.secrets["AZURE_SEARCH_ENDPOINT"]
    DOC_INTEL_KEY = st.secrets["AZURE_DOCUMENT_INTELLIGENCE_KEY"]
    DOC_INTEL_ENDPOINT = st.secrets["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"]
except Exception as e:
    st.error(f"⚠️ Configuration Error: Missing keys in `.streamlit/secrets.toml`.\n\nError Details: {e}")
    st.stop()

# ==========================================
# 3. SIDEBAR (CONTROL PANEL)
# ==========================================
with st.sidebar:
    st.markdown("### 🎛️ Control Panel")
    
    with st.expander("⚙️ Model Parameters", expanded=True):
        temperature = st.slider("Creativity (Temperature)", 0.0, 1.0, 0.0, 0.1, help="0: Deterministic.\n1: Creative.")
        top_k = st.slider("Retrieval Count (Top-K)", 3, 10, 5, help="Documents to retrieve.")
    
    st.divider()
    
    st.subheader("📂 Data Ingestion")
    uploaded_file = st.file_uploader("Upload PDF Document", type="pdf")
    
    process_btn = st.button("Analyze & Index Document", type="primary")

    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# ==========================================
# 4. MODEL INITIALIZATION
# ==========================================
llm = AzureChatOpenAI(
    azure_deployment="GPT-4o",
    api_version="2024-02-15-preview",
    temperature=temperature,
    api_key=OPENAI_API_KEY,
    azure_endpoint=OPENAI_ENDPOINT,
    streaming=True 
)

embeddings = AzureOpenAIEmbeddings(
    azure_deployment="ada002",
    api_version="2023-05-15",
    api_key=OPENAI_API_KEY,
    azure_endpoint=OPENAI_ENDPOINT
)

# ==========================================
# 5. PROCESSING FUNCTIONS (HYBRID PARSING)
# ==========================================
def ocr_image_bytes(img_bytes: bytes, client) -> str:
    """Fallback: Extract text from images using Azure Document Intelligence"""
    try:
        poller = client.begin_analyze_document(
            model_id="prebuilt-read", 
            document=img_bytes, 
            content_type="image/jpeg"
        )
        result = poller.result()
        return "\n".join([line.content for page in result.pages for line in page.lines])
    except Exception:
        return ""

def load_and_process_pdf(uploaded_file):
    """
    Strategy:
    1. Try fast text extraction with PyMuPDF.
    2. If text density is low (scanned PDF), fallback to Azure OCR.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        pdf_path = tmp.name

    client = DocumentIntelligenceClient(
        endpoint=DOC_INTEL_ENDPOINT,
        credential=AzureKeyCredential(DOC_INTEL_KEY)
    )

    try:
        pdf = fitz.open(pdf_path)
        docs = []
        
        my_bar = st.progress(0, text="Scanning pages...")

        for i in range(len(pdf)):
            my_bar.progress((i + 1) / len(pdf), text=f"Processing Page {i+1}/{len(pdf)}...")
            page = pdf[i]
            text = ""

            # 1. Fast Path: PyMuPDF
            extracted_text = page.get_text()
            # If page has >50 chars, assume it's digital text
            if len(extracted_text.strip()) > 50:
                text = extracted_text
            else:
                # 2. Slow Path: Azure OCR (Fallback)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Zoom for quality
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=75)
                text = ocr_image_bytes(buf.getvalue(), client)

            if not text.strip(): text = " "
            docs.append(Document(page_content=text, metadata={"page": i + 1, "source": uploaded_file.name}))
        
        my_bar.empty()
        pdf.close()
        
        # Large chunk size to keep tables intact
        splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
        return splitter.split_documents(docs)

    finally:
        if os.path.exists(pdf_path): os.remove(pdf_path)

# ==========================================
# 6. INDEXING PROCESS
# ==========================================
if uploaded_file and process_btn:
    with st.status("🚀 Processing document...", expanded=True) as status:
        st.write("📄 Parsing PDF pages (Hybrid Strategy)...")
        chunks = load_and_process_pdf(uploaded_file)
        
        st.write(f"🧩 Split into {len(chunks)} semantic chunks.")
        
        st.write("🧠 Indexing into Azure AI Search...")
        vector_store = AzureSearch(
            azure_search_endpoint=SEARCH_ENDPOINT,
            azure_search_key=SEARCH_KEY,
            index_name=AZURE_INDEX_NAME,
            embedding_function=embeddings.embed_query
        )
        vector_store.add_documents(chunks)
        
        status.update(label="✅ Indexing Complete!", state="complete", expanded=False)
        time.sleep(1)
        st.rerun()

# ==========================================
# 7. CHAT INTERFACE (SMART ROUTER & MULTILINGUAL)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- HERO SCREEN (EMPTY STATE) ---
if not st.session_state.messages:
    st.info("👋 Hello! I am your enterprise knowledge assistant. I speak all languages. Upload a document to start.")

# --- DISPLAY CHAT HISTORY ---
for m in st.session_state.messages:
    avatar_icon = "👤" if m["role"] == "user" else "🤖"
    with st.chat_message(m["role"], avatar=avatar_icon):
        st.markdown(m["content"])
        if "sources" in m and m["sources"]:
            with st.expander("📚 References & Citations"):
                tabs = st.tabs([f"Ref {i+1}" for i in range(len(m["sources"]))])
                for i, tab in enumerate(tabs):
                    doc = m["sources"][i]
                    with tab:
                        st.caption(f"Page: {doc.metadata.get('page', '?')}")
                        st.markdown(f"```text\n{doc.page_content}...\n```")

# --- USER INPUT & PROCESSING ---
if user_input := st.chat_input("Type your question here (any language)..."):
    
    # 1. Display User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🤖"):
        
        # --- STEP 1: ROUTER (DECISION MAKER) ---
        search_decision = "SEARCH" # Default
        
        # If history exists, ask LLM: Chat or Search?
        if len(st.session_state.messages) > 0: 
            with st.status("🧠 Thinking...", expanded=False) as status:
                router_prompt = f"""
                Analyze the user's last message: "{user_input}"
                
                Decide:
                1. "SEARCH": If the user is asking for information (e.g., "What are the risks?", "Summarize").
                2. "CHAT": If the user is just chatting, greeting (hello, merhaba), thanking, or asking for clarification.
                
                Reply with only one word: SEARCH or CHAT.
                """
                decision_chain = ChatPromptTemplate.from_template(router_prompt) | llm | StrOutputParser()
                search_decision = decision_chain.invoke({}).strip()
                
                label_text = "Searching knowledge base..." if "SEARCH" in search_decision else "Chat mode..."
                status.update(label=label_text, state="complete")

        # --- STEP 2: EXECUTION ---
        full_response = ""
        source_docs = []

        # SCENARIO A: CHAT MODE (Greetings & Chit-chat)
        if "CHAT" in search_decision:
            system_prompt = """
            You are a helpful enterprise assistant. 
            You do NOT need to search the documents.
            
            IMPORTANT:
            - Answer in the SAME LANGUAGE as the user's input. 
            - If user says "Merhaba", reply in Turkish. If "Hello", reply in English.
            - Be professional and polite.
            """
            
            history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages[-5:]])
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("system", f"Chat History:\n{history_text}"),
                ("user", "{question}")
            ])
            chain = prompt | llm | StrOutputParser()
            response_stream = chain.stream({"question": user_input})
            full_response = st.write_stream(response_stream)

# SCENARIO B: RAG MODE (Search)
        else:
            # 1. Query Rewriting (Optimized for Summarization)
            refined_query = user_input
            if len(st.session_state.messages) > 0: 
                last_history = st.session_state.messages[-3:]
                history_str = "\n".join([f"{m['role']}: {m['content']}" for m in last_history])
                
                # BURASI GÜNCELLENDİ: Özet isteklerini daha iyi yakalamak için prompt güçlendirildi.
                rewrite_prompt = f"""
                Act as a search query optimizer.
                1. Look at the chat history and the user's new question.
                2. Rewrite it into a standalone search query.
                3. SPECIAL RULE: If the user asks to "Summarize", "Overview", or "What is this document about?", rewrite the query to target key sections like: "Executive summary abstract conclusion main findings introduction".
                4. If non-English, translate the query to English.
                5. Output ONLY the English search query.
                
                History: {history_str}
                User Question: {user_input}
                
                Search Query (English):
                """
                refined_query = (ChatPromptTemplate.from_template(rewrite_prompt) | llm | StrOutputParser()).invoke({})

            # 2. Azure Search Retrieval
            with st.status(f"🔍 Searching...", expanded=False) as status:
                vector_store = AzureSearch(
                    azure_search_endpoint=SEARCH_ENDPOINT,
                    azure_search_key=SEARCH_KEY,
                    index_name=AZURE_INDEX_NAME,
                    embedding_function=embeddings.embed_query
                )
                retriever = vector_store.as_retriever(search_type="similarity", k=top_k)
                source_docs = retriever.invoke(refined_query)
                status.update(label=f"✅ Found {len(source_docs)} relevant contexts.", state="complete")

            # 3. Answer Generation (Multilingual & Summarization Friendly)
            context_text = "\n\n".join([doc.page_content for doc in source_docs])
            
            # BURASI GÜNCELLENDİ: Modele "Yok deme, elindekini özetle" yetkisi verildi.
            system_prompt = """
            You are a professional enterprise assistant. Answer using the provided Context only.
            
            CRITICAL RULES:
            1. Language: Answer in the SAME LANGUAGE as the User's Question.
            2. Summarization: If the user asks for a summary and the context contains partial information (like Abstract, Introduction, or specific sections), generate the best possible summary from those parts. Do NOT say "I can't find specific info" unless the context is completely irrelevant/empty.
            3. Accuracy: Be professional and accurate.
            4. Fallback: If absolutely no relevant info is found, say (in user's language): "I couldn't find specific information in the documents, but..."
            
            Context:
            {context}
            """
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", "{question}")
            ])
            
            chain = prompt | llm | StrOutputParser()
            response_stream = chain.stream({"context": context_text, "question": user_input})
            full_response = st.write_stream(response_stream)

            # Display Sources in Tabs
            if source_docs:
                st.markdown("### 📚 Sources")
                tabs = st.tabs([f"Ref {i+1}" for i in range(len(source_docs))])
                for i, tab in enumerate(tabs):
                    with tab:
                        doc = source_docs[i]
                        st.info(f"📄 Page: {doc.metadata.get('page', '?')}")
                        st.text(doc.page_content[:400] + "...")

    # Save to History
    st.session_state.messages.append({
        "role": "assistant", 
        "content": full_response,
        "sources": source_docs
    })