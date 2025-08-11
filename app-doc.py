from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import socketio
import asyncio
from minio import Minio
from minio.error import S3Error
from datetime import timedelta
from agno.agent import Agent
from agno.knowledge.pdf import PDFKnowledgeBase, PDFReader
from agno.vectordb.qdrant import Qdrant
from agno.storage.redis import RedisStorage
from agno.memory.v2.db.redis import RedisMemoryDb
from agno.memory.v2.memory import Memory
from agno.document.chunking.agentic import AgenticChunking 
import openai
# Chargement des variables d'environnement
import os
from dotenv import load_dotenv
load_dotenv()

# Chargement des variables d'environnement
load_dotenv()
openai.api_key = os.getenv("OPEN  AI_API_KEY")
openai.project = os.getenv("OPENAI_PROJECT_ID")


# Configuration MinIO
client = Minio(
    os.getenv("ENDPOINT"),
    access_key=os.getenv("ACCESS_KEY"),
    secret_key=os.getenv("SECRET_KEY"),
    secure=False
)

bucket_name = "iachatbotbocs"
  
# Initialisation Qdrant
vector_db = Qdrant(
    collection="decret-collection-from-minio",
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# Initialize Redis storage with default local connection
storage = RedisStorage(
    prefix="agno_test", 
    host="localhost",       
    port=6379,            
)
# Create memory storage
memory_db = RedisMemoryDb(
        prefix="agno_test",
        host="localhost",
        port=6379,
        )
memory = Memory(db=memory_db)


# Télécharger tous les PDF du dossier 'pole-suivi' du bucket
decret_prefix = "pole-suivi/"
pdf_objects = client.list_objects(bucket_name, prefix=decret_prefix, recursive=True)
local_decret_dir = "data/pdfs"
os.makedirs(local_decret_dir, exist_ok=True)

for obj in pdf_objects:
    if obj.object_name.endswith(".pdf"):
        local_path = os.path.join(local_decret_dir, os.path.basename(obj.object_name))
        if not os.path.exists(local_path):
            client.fget_object(bucket_name, obj.object_name, local_path)

# Charger tous les PDF du dossier dans la base de connaissance
knowledge_base = PDFKnowledgeBase(
    path=local_decret_dir, 
    reader=PDFReader(chunk=True),
    vector_db=vector_db,
    chunking_strategy=AgenticChunking(),
)

agent = Agent(
     knowledge=knowledge_base,
      search_knowledge=True, 
      debug_mode=False,
      description="Spécialiste des décrets, rapports, arrêtés, lois et textes réglementaires officiels.",
      instructions=[
        "Réponds aux questions concernant les décrets, rapports, arrêtés, lois ou tout texte réglementaire officiel et soyez acceuillant et repondez aux salutations.",
        "Utilise exclusivement les informations extraites des documents PDF officiels.",
        "Si la question ne concerne pas ces documents ou si l’information n’est pas présente,  essayez de repondre selon votre connaissance."
    ],
      storage=storage,
      add_history_to_messages=True,
      memory=memory
      )

# Vérifier si la collection Qdrant contient déjà des points
def is_collection_indexed(vector_db):
    try:
        info = vector_db.client.count(collection_name=vector_db.collection)
        return info.count > 0
    except Exception:
        return False
 

# Création de l'app FastAPI
app = FastAPI()

# Middleware CORS pour autoriser Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modèle de requête
class QueryRequest(BaseModel):
    question: str

# Chargement de la base de connaissances au démarrage
@app.on_event("startup")
async def startup_event():
    # Chargement base web
    if not await vector_db.async_exists():
        print("Collection pdf absente, chargement de la base de connaissances...")
        await knowledge_base.aload(recreate=True)
    else:
        print("Collection pdf déjà présente, pas de rechargement nécessaire.")

   
# Endpoint HTTP classique
@app.post("/ask")
async def ask(request: QueryRequest):
    try:
        result = agent.run(request.question, stream=True)
        final_answer = getattr(result, "content", str(result))
        return JSONResponse(content={"response": final_answer})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- Partie Socket.IO ---
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

@sio.event
async def connect(sid, environ):
    print('Client connecté:', sid)

@sio.event
async def ask(sid, data):
    print('Question reçue via Socket.IO:', data)
    try:
        result = agent.run(data.get("question", ""))
        final_answer = getattr(result, "content", str(result))
        await sio.emit('response', {'response': final_answer}, to=sid)
    except Exception as e:
        await sio.emit('response', {'error': str(e)}, to=sid)

# Emballage de l'app FastAPI avec Socket.IO 
app_with_socketio = socketio.ASGIApp(sio, app)

# Lancement de l'application
if __name__ == "__main__":
    uvicorn.run("app-doc:app_with_socketio", host="0.0.0.0", port=8000, reload=True)