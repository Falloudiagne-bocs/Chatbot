# chatbocs_app/services/agno_system.py
from __future__ import annotations
import os, time, shutil, tempfile
from typing import List, Dict, Any, Optional

import streamlit as st

# AGNO imports
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb
from agno.knowledge.embedder.fastembed import FastEmbedEmbedder
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.models.groq import Groq

from chatbocs_app.config import AppConfig

class AGNOChatSystem:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self.vector_db: Optional[LanceDb] = None
        self.knowledge: Optional[Knowledge] = None
        self.agent: Optional[Agent] = None
        self.initialized: bool = False

    def initialize(self, reset: bool = False) -> bool:
        try:
            # Si reset demandé, supprimer complètement la base de données
            if reset:
                try:
                    # Supprimer physiquement le répertoire de la base vectorielle
                    if os.path.exists(self.cfg.vector_db_path):
                        shutil.rmtree(self.cfg.vector_db_path)
                        st.toast("Base vectorielle supprimée physiquement", icon="🗑️")
                    
                    # Recréer le répertoire
                    os.makedirs(self.cfg.vector_db_path, exist_ok=True)
                    
                except Exception as e:
                    st.warning(f"Erreur lors de la suppression physique: {e}")

            self.vector_db = LanceDb(
                table_name=self.cfg.table_name,
                uri=self.cfg.vector_db_path,
                embedder=FastEmbedEmbedder(),
            )
            
            # Double vérification: vider la table si elle existe encore
            if reset:
                try:
                    self.vector_db.delete_all()
                    st.toast("Base vectorielle réinitialisée", icon="♻️")
                except Exception as e:
                    st.info(f"Table vide ou inexistante: {e}")

            self.knowledge = Knowledge(
                name=self.cfg.knowledge_name,
                description=self.cfg.knowledge_desc,
                vector_db=self.vector_db,
            )

            self.agent = Agent(
                model=Groq(id=self.cfg.model_id),
                knowledge=self.knowledge,
                search_knowledge=True,
                debug_mode=True,
                description=(
                    "Agent spécialisé dans la gestion des projets et programmes.\n"
                    "Il répond uniquement sur la base des documents officiels indexés."
                ),
                instructions=[
                    "Répondre uniquement sur la base des documents indexés dans la base de connaissances.",
                    "Toujours citer les sources utilisées.",
                    "Être précis et factuel.",
                    "Si l'information n'est pas trouvée, le dire clairement.",
                    "Utiliser la fonction de recherche de la base avant de répondre.",
                ],
            )

            self.initialized = True
            return True
        except Exception as e:
            st.error(f" Erreur d'initialisation AGNO: {e}")
            return False

    def force_cleanup(self) -> bool:
        """Force un nettoyage complet de la base vectorielle"""
        try:
            # Arrêter les connexions actuelles
            if self.vector_db:
                try:
                    self.vector_db.delete_all()
                except Exception:
                    pass
            
            # Supprimer physiquement tous les fichiers
            if os.path.exists(self.cfg.vector_db_path):
                shutil.rmtree(self.cfg.vector_db_path)
                
            # Recréer le répertoire
            os.makedirs(self.cfg.vector_db_path, exist_ok=True)
            
            # Réinitialiser les composants
            self.vector_db = None
            self.knowledge = None
            self.agent = None
            self.initialized = False
            
            # Réinitialiser
            return self.initialize(reset=False)
            
        except Exception as e:
            st.error(f"Erreur lors du nettoyage forcé: {e}")
            return False

    def reload_knowledge_base(self) -> bool:
        """Recharge dynamiquement la base de connaissances"""
        try:
            if not self.initialized:
                return self.initialize()
            
            # Reconnecter à la base vectorielle
            self.vector_db = LanceDb(
                table_name=self.cfg.table_name,
                uri=self.cfg.vector_db_path,
                embedder=FastEmbedEmbedder(),
            )
            
            # Recréer la base de connaissances avec la nouvelle connexion
            self.knowledge = Knowledge(
                name=self.cfg.knowledge_name,
                description=self.cfg.knowledge_desc,
                vector_db=self.vector_db,
            )
            
            # Recréer l'agent avec la nouvelle base de connaissances
            self.agent = Agent(
                model=Groq(id=self.cfg.model_id),
                knowledge=self.knowledge,
                search_knowledge=True,
                debug_mode=True,
                description=(
                    "Agent spécialisé dans la gestion des projets et programmes.\n"
                    "Il répond uniquement sur la base des documents officiels indexés."
                ),
                instructions=[
                    "Répondre uniquement sur la base des documents indexés dans la base de connaissances.",
                    "Toujours citer les sources utilisées.",
                    "Être précis et factuel.",
                    "Si l'information n'est pas trouvée, le dire clairement.",
                    "Utiliser la fonction de recherche de la base avant de répondre.",
                ],
            )
            
            st.toast("Base de connaissances rechargée", icon="🔄")
            return True
            
        except Exception as e:
            st.error(f"Erreur lors du rechargement: {e}")
            return False

    def auto_index_directory(self, directory_path: str = None) -> int:
        """Indexe automatiquement tous les PDFs d'un répertoire"""
        if not directory_path:
            directory_path = self.cfg.upload_dir
            
        if not os.path.exists(directory_path):
            st.warning(f"Répertoire introuvable: {directory_path}")
            return 0
            
        indexed_count = 0
        pdf_files = [f for f in os.listdir(directory_path) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            st.info(f"Aucun PDF trouvé dans {directory_path}")
            return 0
            
        try:
            for pdf_file in pdf_files:
                pdf_path = os.path.join(directory_path, pdf_file)
                doc_name = os.path.splitext(pdf_file)[0]
                
                if self.add_pdf(pdf_path, doc_name):
                    indexed_count += 1
                    st.success(f"✅ {pdf_file} indexé")
                else:
                    st.error(f"❌ Échec indexation: {pdf_file}")
                    
        except Exception as e:
            st.error(f"Erreur lors de l'indexation automatique: {e}")
            
            return indexed_count

    def check_for_new_documents(self, directory_path: str = None) -> List[str]:
        """Vérifie s'il y a de nouveaux documents dans le répertoire"""
        if not directory_path:
            directory_path = self.cfg.upload_dir
            
        if not os.path.exists(directory_path):
            return []
            
        # Obtenir tous les PDFs du répertoire
        current_pdfs = [f for f in os.listdir(directory_path) if f.lower().endswith('.pdf')]
        
        # Stocker la liste dans session_state pour comparaison
        if "indexed_pdfs" not in st.session_state:
            st.session_state.indexed_pdfs = set()
            
        # Trouver les nouveaux fichiers
        new_pdfs = [pdf for pdf in current_pdfs if pdf not in st.session_state.indexed_pdfs]
        
        return new_pdfs

    def mark_as_indexed(self, pdf_filename: str):
        """Marque un PDF comme indexé"""
        if "indexed_pdfs" not in st.session_state:
            st.session_state.indexed_pdfs = set()
        st.session_state.indexed_pdfs.add(pdf_filename)

    def add_pdf(self, path_or_file: str, doc_name: Optional[str] = None, auto_reload: bool = True) -> bool:
        if not self.initialized:
            ok = self.initialize()
            if not ok:
                return False
        try:
            if not doc_name:
                base = os.path.basename(path_or_file)
                doc_name = os.path.splitext(base)[0]

            self.knowledge.add_content(
                name=doc_name,
                path=path_or_file,
                reader=PDFReader(),
                metadata={
                    "doc_type": "NDT_document",
                    "source_type": "uploaded_pdf",
                    "doc_name": doc_name,
                },
            )
            
            # Rechargement automatique après ajout
            if auto_reload:
                self.reload_knowledge_base()
                
            return True
        except Exception as e:
            st.error(f" Erreur d'ajout PDF: {e}")
            return False

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not (self.initialized and self.vector_db):
            return []
        try:
            # Add some debugging information
            if st.session_state.get("debug_mode", False):
                st.info(f"🔍 Recherche pour: '{query}' (limite: {limit})")
            
            results = self.vector_db.search(query, limit=limit)
            formatted = []
            for r in results:
                # LanceDB typically returns distance (lower = more similar)
                distance = getattr(r, "distance", 0.0)
                # Convert distance to similarity score (0-1 range, higher = more similar)
                similarity = max(0.0, 1.0 - distance) if distance <= 1.0 else 1.0 / (1.0 + distance)
                
                if st.session_state.get("debug_mode", False):
                    st.write(f"Distance: {distance:.4f}, Similarity: {similarity:.4f}")
                
                formatted.append(
                    {
                        "score": distance,  # Keep original distance for debugging
                        "similarity": similarity,  # Add similarity score
                        "text": getattr(r, "content", ""),
                        "meta": getattr(r, "metadata", {}),
                    }
                )
            return formatted
        except Exception as e:
            st.error(f" Erreur de recherche: {e}")
            return []

    def chat(self, query: str, history: Optional[list], memory_k: int) -> Dict[str, Any]:
        if not self.initialized:
            ok = self.initialize()
            if not ok:
                return {"content": "Erreur d'initialisation AGNO", "duration": 0, "success": False}
        try:
            start = time.time()
            context_prompt = query
            if history:
                recent = history[-max(0, memory_k):]
                blocks = []
                for conv in recent:
                    u = (conv.get("user") or "").strip()
                    a = (conv.get("assistant") or "").strip()
                    if u and a:
                        blocks.append(f"Q: {u}\nR: {a}")
                if blocks:
                    context_prompt = "Historique récent (résumé):\n" + "\n\n".join(blocks) + f"\n\nQuestion actuelle: {query}"

            response = self.agent.run(context_prompt)
            duration = time.time() - start
            content = getattr(response, "content", None) or str(response)
            return {"content": content, "duration": duration, "success": True}
        except Exception as e:
            return {"content": f"Erreur lors de la génération: {e}", "duration": 0, "success": False}

@st.cache_resource(show_spinner=False)
def get_system(cfg: AppConfig) -> AGNOChatSystem:
    sys = AGNOChatSystem(cfg)
    sys.initialize(reset=False)
    return sys


