"""
RAG Service — Retrieval-Augmented Generation over academic regulations.
Uses PyMuPDF for Arabic PDF extraction, ChromaDB for vector storage,
Cross-Encoder reranking for precision, and OpenAI for generation.
LangSmith tracing is enabled via environment variables.
"""

import os
import shutil
import logging
from typing import List, Tuple, Optional

import fitz  # PyMuPDF
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import CrossEncoder

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ── Configuration ───────────────────────────────────────────────────

REGULATIONS_PDF = os.path.join(
    os.path.dirname(__file__), "..", "important_pdf", "RAG", "اللائحة الجديدة.pdf"
)
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

RERAN_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
RETRIEVE_K = 15
RERAN_TOP_K = 6

RAG_SYSTEM_PROMPT = """You are the Smart Academic Advisor for the Faculty of Artificial Intelligence at the Egyptian Russian University (ERU).

Your role is to answer student questions about academic regulations, policies, and procedures based ONLY on the retrieved context from the official regulations document (اللائحة الجديدة).

## Key Facts:
- Faculty programs: Artificial Intelligence, Data Science, Cybersecurity, Software Engineering
- Graduation: 144 credit hours minimum
- Study system: Credit hours, Fall + Spring semesters + optional Summer
- Teaching language: English (some courses in Arabic)
- GPA scale: 4.0 (A+ = 4.0, A = 3.7, A- = 3.4 ... F = 0)

## STRICT Language Rules:
- If the student writes in **English** → respond ONLY in **English**
- If the student writes in **Arabic (فصحى or عامية مصرية)** → respond ONLY in **Arabic**
- NEVER mix languages in one response

## [Arabic Rules] قواعد الرد بالعربية:
- جاوب دايماً باللغة اللي الطالب بيستخدمها (فصحى أو عامية).
- استخدم السياق (Context) المرفق فقط للإجابة. لو مش لاقي الإجابة قول "مش لاقي المعلومة دي في اللائحة".
- خليك محدد ودقيق في الأرقام (ساعات، معدل تراكمي، نسب مئوية).
- حافظ على المصطلحات الأكاديمية بالإنجليزية لو ده بيسهل الفهم (زي Credit Hours, GPA).

## Egyptian Arabic Understanding:
Students may use Egyptian slang. Map terms like:
- "عايز اتخرج" -> Graduation
- "كام ساعة" -> Credit Hours
- "معدلي وقع" -> Low GPA
- "سابها" / "مش طايق" -> Drop/Withdraw
- "هيفصلوني" -> Dismissal

## Answer Rules:
1. Answer ONLY from the retrieved context. Do NOT invent regulations.
2. Be precise with numbers.
3. If not found, say:
   - English: "I couldn't find this specific regulation in the document..."
   - Arabic: "مش لاقي المعلومة دي في اللائحة..."
4. Format answers with bullet points.
5. Cite page numbers if available.

## Context:
{context}

## Student Question:
{question}

## Your Answer:"""


# ── Service ─────────────────────────────────────────────────────────

class RAGService:
    """Handles regulation queries using Retrieval-Augmented Generation."""

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        )
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini"),
            temperature=0.2,
        )
        try:
            self.reranker = CrossEncoder(RERAN_MODEL)
            logger.info(f"Cross-Encoder reranker loaded: {RERAN_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load reranker: {e}")
            self.reranker = None

        self.vectorstore = None
        self.chain = None
        self._load_or_build_vectorstore()

    def query(self, question: str) -> str:
        """Answer a regulation-related question using RAG."""
        if not self.chain:
            return "RAG service is not initialized."

        try:
            return self.chain.invoke(question)
        except Exception as e:
            logger.error(f"Error querying RAG: {e}")
            return f"Error querying regulations: {str(e)}"

    def rebuild(self):
        """Force rebuild the vectorstore from PDF."""
        if os.path.exists(CHROMA_DIR):
            shutil.rmtree(CHROMA_DIR)
            logger.info("Cleared old vectorstore")
        
        self._build_vectorstore()
        self._build_chain()
        logger.info("Vectorstore rebuilt successfully")

    def _load_or_build_vectorstore(self):
        """Load existing vectorstore or build from PDF."""
        if os.path.exists(CHROMA_DIR) and os.listdir(CHROMA_DIR):
            self.vectorstore = Chroma(
                persist_directory=CHROMA_DIR,
                embedding_function=self.embeddings,
            )
            logger.info("Loaded existing vectorstore from chroma_db/")
        else:
            self._build_vectorstore()

        self._build_chain()

    def _build_vectorstore(self):
        """Extract PDF, split into chunks, and create ChromaDB vectorstore."""
        logger.info("Building vectorstore from regulations PDF...")

        pages = self._extract_pdf_text()
        if not pages:
            logger.warning("No text extracted from PDF!")
            return

        documents = [
            Document(page_content=text, metadata={"source": "regulations", "page": page_num})
            for page_num, text in pages
        ]

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", "،", "•", " "],
        )
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} chunks")

        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=CHROMA_DIR,
        )
        logger.info("Vectorstore built and persisted to chroma_db/")

    def _extract_pdf_text(self) -> List[Tuple[int, str]]:
        """Extract text from PDF using PyMuPDF (fitz)."""
        if not os.path.exists(REGULATIONS_PDF):
            raise FileNotFoundError(f"Regulations PDF not found at: {REGULATIONS_PDF}")

        doc = fitz.open(REGULATIONS_PDF)
        pages = []

        for i, page in enumerate(doc):
            text = page.get_text("text")
            if not text:
                continue
            
            # Clean text (remove sidebar noise) but PRESERVE empty lines for structure
            lines = []
            for line in text.split("\n"):
                stripped = line.strip()
                if len(stripped) > 2 or stripped == "":
                    lines.append(stripped)
            cleaned = "\n".join(lines)
            
            if cleaned.strip():
                pages.append((i + 1, cleaned))

        doc.close()
        logger.info(f"Extracted {len(pages)} pages from PDF")
        return pages

    def _build_chain(self):
        """Build the RAG chain."""
        if not self.vectorstore:
            logger.error("Cannot build chain: Vectorstore not initialized")
            return

        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": RETRIEVE_K},
        )

        prompt = ChatPromptTemplate.from_template(RAG_SYSTEM_PROMPT)

        self.chain = (
            {
                "context": RunnableLambda(self._retrieve_and_rerank),
                "question": RunnablePassthrough(),
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        logger.info(f"RAG chain built: retrieve({RETRIEVE_K}) -> rerank({RERAN_TOP_K}) -> LLM")

    def _retrieve_and_rerank(self, question: str) -> str:
        """Retrieve docs, rerank them, and format for context."""
        # 1. Retrieve
        docs = self.vectorstore.as_retriever(search_kwargs={"k": RETRIEVE_K}).invoke(question)
        
        # 2. Rerank
        reranked = self._rerank(question, docs)
        
        # 3. Format
        return self._format_docs(reranked)

    def _rerank(self, query: str, docs: List[Document]) -> List[Document]:
        """Rerank documents using Cross-Encoder."""
        if not docs or not self.reranker:
            return docs[:RERAN_TOP_K]

        pairs = [(query, doc.page_content) for doc in docs]
        scores = self.reranker.predict(pairs)

        # Sort by score
        scored_docs = sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)
        top_docs = [doc for _, doc in scored_docs[:RERAN_TOP_K]]
        
        logger.debug(f"Rerank top score: {scored_docs[0][0]:.3f}")
        return top_docs

    @staticmethod
    def _format_docs(docs: List[Document]) -> str:
        """Format documents into a single context string."""
        return "\n\n---\n\n".join(
            f"[Page {d.metadata.get('page', '?')}]\n{d.page_content}"
            for d in docs
        )
