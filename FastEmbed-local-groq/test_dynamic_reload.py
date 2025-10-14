#!/usr/bin/env python3
"""
Script de test pour valider les fonctionnalités de rechargement dynamique
"""

import os
import sys
sys.path.append('.')

from chatbocs_app.config import AppConfig
from chatbocs_app.services.agno_system import AGNOChatSystem

def test_dynamic_reload():
    """Test des fonctionnalités de rechargement dynamique"""
    print("🧪 Test du rechargement dynamique de la base de connaissances")
    
    # Configuration
    cfg = AppConfig()
    print(f"📁 Chemin de la base vectorielle: {cfg.vector_db_path}")
    print(f"📂 Répertoire des documents: {cfg.upload_dir}")
    
    # Créer le système
    system = AGNOChatSystem(cfg)
    
    # Test d'initialisation
    print("\n1️⃣ Test d'initialisation...")
    if system.initialize():
        print("✅ Système initialisé avec succès")
    else:
        print("❌ Échec d'initialisation")
        return False
    
    # Test de vérification des nouveaux documents
    print("\n2️⃣ Test de détection des nouveaux documents...")
    new_docs = system.check_for_new_documents()
    if new_docs:
        print(f"🆕 {len(new_docs)} nouveaux documents détectés:")
        for doc in new_docs:
            print(f"   📄 {doc}")
    else:
        print("ℹ️ Aucun nouveau document détecté")
    
    # Test de rechargement
    print("\n3️⃣ Test de rechargement de la base...")
    if system.reload_knowledge_base():
        print("✅ Base de connaissances rechargée avec succès")
    else:
        print("❌ Échec du rechargement")
        return False
    
    # Test d'indexation automatique
    print("\n4️⃣ Test d'indexation automatique...")
    count = system.auto_index_directory()
    print(f"📥 {count} document(s) indexé(s)")
    
    print("\n🎉 Tous les tests terminés avec succès!")
    return True

if __name__ == "__main__":
    test_dynamic_reload()
