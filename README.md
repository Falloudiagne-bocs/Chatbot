# 📊 Chatbot IA – Pôle Suivi & Évaluation

## 📌 Introduction
Ce projet met en place un **chatbot intelligent** spécialisé dans la consultation de décrets, rapports, arrêtés, lois et autres textes réglementaires officiels.  
Il s'appuie sur une architecture **FastAPI + Socket.IO** et exploite des documents PDF stockés dans **MinIO** et indexés dans **Qdrant** pour la recherche vectorielle.

---

## 🗂 Fonctionnalités
- **Téléchargement automatique** de PDF depuis un bucket MinIO.
- **Vectorisation et recherche sémantique** via Qdrant.
- **Interaction temps réel** via Socket.IO.
- **Réponses contextuelles** basées uniquement sur les documents officiels.
- **Mémoire conversationnelle** grâce à Redis.
- **Frontend Angular** compatible via CORS.

---

## 📦 Technologies utilisées
- **[FastAPI](https://fastapi.tiangolo.com/)** – Backend API.
- **[Socket.IO](https://python-socketio.readthedocs.io/)** – Communication temps réel.
- **[MinIO](https://min.io/)** – Stockage d’objets (PDF).
- **[Qdrant](https://qdrant.tech/)** – Base vectorielle pour la recherche.
- **[Redis](https://redis.io/)** – Mémoire conversationnelle.
- **[AGNO](https://github.com/agno-ai)** – Gestion des agents et de la base de connaissances.
- **[OpenAI](https://platform.openai.com/)** – Génération de réponses.
- **Angular** – Frontend (non inclus ici).

---

## 📂 Structure du projet
