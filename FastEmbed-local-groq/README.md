# chatBOCS AGNO (modulaire)

## Lancement
```bash
pip install -r requirements.txt
export GROQ_API_KEY=...  # ou créer un fichier .env
streamlit run streamlit_app.py
```

## Structure
```text
.
├─ streamlit_app.py
└─ chatbocs_app/
   ├─ __init__.py
   ├─ config.py
   ├─ services/
   │  ├─ __init__.py
   │  └─ agno_system.py
   ├─ ui/
   │  ├─ __init__.py
   │  └─ layout.py
   └─ utils/
      ├─ __init__.py
      └─ persist.py
```
