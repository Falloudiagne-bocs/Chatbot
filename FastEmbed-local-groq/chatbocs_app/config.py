# chatbocs_app/config.py
from dataclasses import dataclass

@dataclass
class AppConfig:
    vector_db_path: str = "tmp/lancedb"
    table_name: str = "vectors"
    default_top_k: int = 5
    default_memory_k: int = 3
    upload_dir: str = "documents_pdf"
    model_id: str = "llama-3.3-70b-versatile"
    knowledge_name: str = "Streamlit BOCS Knowledge Base"
    knowledge_desc: str = "Base de connaissances BOCS intégrée à Streamlit"
