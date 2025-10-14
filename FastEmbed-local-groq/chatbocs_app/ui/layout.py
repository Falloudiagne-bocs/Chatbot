# chatbocs_app/ui/layout.py
import os, shutil
import streamlit as st
from chatbocs_app.utils.persist import persist_uploaded_file

def render_sidebar(system, cfg):
    st.sidebar.header("⚙️ Paramètres AGNO")
    top_k = st.sidebar.number_input("Top k retrieval", value=cfg.default_top_k, min_value=1, max_value=50)
    memory_k = st.sidebar.number_input("Mémoire conversation", value=cfg.default_memory_k, min_value=0, max_value=20)
    
    # Add debug mode toggle
    debug_mode = st.sidebar.checkbox("🐛 Mode debug", value=st.session_state.get("debug_mode", False))
    st.session_state.debug_mode = debug_mode

    c1, c2 = st.sidebar.columns(2)
    with c1:
        if system.initialized:
            st.success("✅ Initialisé")
            # Afficher le chemin de la DB
            db_name = os.path.basename(cfg.vector_db_path) if hasattr(cfg, 'vector_db_path') else "lancedb"
            st.caption(f"DB: {db_name}")
        else:
            st.warning("⚠️ Non initialisé")
    with c2:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("♻️ Reset", help="Réinitialiser la base vectorielle"):
                if system.initialize(reset=True):
                    st.toast("Réinitialisation effectuée", icon="♻️")
        with col2:
            if st.button("🗑️ Purge", help="Nettoyage complet et forcé de la base"):
                if system.force_cleanup():
                    st.toast("Nettoyage complet effectué", icon="🗑️")
                    st.rerun()

    st.sidebar.divider()
    
    # Section de rechargement dynamique
    st.sidebar.subheader("🔄 Rechargement dynamique")
    
    # Vérifier s'il y a de nouveaux documents
    new_docs = system.check_for_new_documents()
    if new_docs:
        st.sidebar.warning(f"🆕 {len(new_docs)} nouveau(x) PDF détecté(s)")
        for doc in new_docs[:3]:  # Afficher max 3 noms
            st.sidebar.caption(f"📄 {doc}")
        if len(new_docs) > 3:
            st.sidebar.caption(f"... et {len(new_docs) - 3} autre(s)")
    
    col_reload1, col_reload2 = st.sidebar.columns(2)
    
    with col_reload1:
        if st.button("🔄 Recharger", help="Recharger la base de connaissances"):
            if system.reload_knowledge_base():
                st.toast("Base rechargée", icon="🔄")
    
    with col_reload2:
        auto_index_label = f"📂 Auto-index ({len(new_docs)})" if new_docs else "📂 Auto-index"
        if st.button(auto_index_label, help="Indexer automatiquement tous les nouveaux PDFs"):
            with st.spinner("Indexation en cours..."):
                count = system.auto_index_directory()
                if count > 0:
                    st.success(f"✅ {count} PDF(s) indexé(s)")
                    # Marquer les fichiers comme indexés
                    for pdf in new_docs:
                        system.mark_as_indexed(pdf)
                    # Recharger après indexation
                    system.reload_knowledge_base()
                    st.rerun()
                else:
                    st.info("Aucun nouveau PDF à indexer")

    st.sidebar.divider()
    st.sidebar.subheader("📁 Gestion des documents")
    uploads = st.sidebar.file_uploader(
        "Ajouter des PDF", type=["pdf"], accept_multiple_files=True,
        help="Les fichiers seront indexés dans LanceDB via AGNO"
    )
    if uploads and st.sidebar.button("🔄 Indexer", type="primary"):
        if not system.initialized:
            st.sidebar.error("Veuillez initialiser AGNO")
        else:
            ok_count = 0
            total = len(uploads)
            prog = st.sidebar.progress(0)
            
            for i, uf in enumerate(uploads, start=1):
                try:
                    doc_name = os.path.splitext(uf.name)[0]
                    tmp_dir, fpath = persist_uploaded_file(uf, cfg.upload_dir)
                    ok = system.add_pdf(fpath, doc_name=doc_name)
                    if ok:
                        ok_count += 1
                        st.sidebar.success(f"✅ {uf.name} indexé")
                    else:
                        st.sidebar.error(f"❌ Échec indexation: {uf.name}")
                except Exception as e:
                    st.sidebar.error(f"❌ {uf.name}: {e}")
                finally:
                    try:
                        shutil.rmtree(tmp_dir, ignore_errors=True)
                    except Exception:
                        pass
                prog.progress(i / total)
            st.sidebar.info(f"📥 {ok_count}/{total} PDF indexé(s)")
    st.sidebar.divider()
    st.sidebar.info("🤖 Powered by AGNO + Groq + FastEmbed + LanceDB")
    return top_k, memory_k

def render_chat_panel(system, top_k: int, memory_k: int):
    st.subheader("💬 Chat avec l'Assistant BOCS AGNO")
    q = st.text_area(
        "Posez votre question sur les projets BOCS…",
        height=120,
        placeholder="Ex: Quels sont les 4 axes stratégiques du New Deal Technologique ?",
    )

    c1, c2 = st.columns([1, 1])
    send_clicked = False
    with c1:
        if st.button("📤 Envoyer", type="primary"):
            send_clicked = True
    with c2:
        if st.button("🗑️ Vider l'historique"):
            st.session_state.conversations = []
            st.rerun()

    if send_clicked:
        if not q.strip():
            st.warning("Veuillez écrire une question.")
            send_clicked = False
        elif not system.initialized:
            st.error("Veuillez initialiser AGNO dans la sidebar.")
            send_clicked = False
        else:
            with st.spinner("🔎 Recherche des passages pertinents…"):
                retrieved = system.search(q, limit=top_k)
            with st.spinner("🤖 Génération de la réponse…"):
                answer = system.chat(q, st.session_state.conversations, memory_k)

            st.session_state.conversations.append(
                {
                    "user": q,
                    "assistant": answer.get("content"),
                    "retrieved": retrieved,
                    "duration": answer.get("duration", 0.0),
                    "success": answer.get("success", False),
                }
            )

    # Display latest answer + sources
    if st.session_state.conversations:
        last = st.session_state.conversations[-1]
        st.markdown("### 🤖 Réponse AGNO")
        if last.get("success") and last.get("assistant"):
            st.write(last["assistant"])
            dur = float(last.get("duration", 0.0))
            badge = "🟢" if dur < 3 else ("🟡" if dur < 8 else "🔴")
            st.caption(f"{badge} Temps AGNO: {dur:.2f}s")
        else:
            st.error("❌ Erreur dans la réponse AGNO")
        
        # Display sources
        st.markdown("### 📚 Sources utilisées")
        sources = last.get("retrieved", [])
        if sources:
            with st.expander("📖 Sources utilisées"):
                for i, doc in enumerate(sources, start=1):
                    meta = doc.get("meta", {})
                    # Use the new similarity score if available, otherwise convert distance
                    similarity_score = doc.get("similarity", 0.0)
                    if similarity_score == 0.0:
                        distance = float(doc.get("score", 0.0))
                        similarity_score = max(0.0, 1.0 - distance) if distance <= 1.0 else 1.0 / (1.0 + distance)
                    
                    st.markdown(f"**🔗 Source {i}:** {meta.get('doc_name','Inconnu')} (Score: {similarity_score:.3f})")
                    preview_text = doc.get("text", "")
                    if preview_text:
                        # Show first part of the text
                        preview = preview_text[:300] + ("..." if len(preview_text) > 300 else "")
                        st.text_area(f"Extrait source {i}", preview, height=100, disabled=True)
        else:
            st.warning("Aucune source pertinente trouvée.")    

    return send_clicked, q

def render_history():
    st.divider()
    st.subheader("📜 Historique AGNO")
    if not st.session_state.conversations:
        st.info("Aucune conversation. Posez votre première question !")
    else:
        for idx, conv in enumerate(reversed(st.session_state.conversations), start=1):
            st.markdown(f"#### 👤 Question {len(st.session_state.conversations) - idx + 1}")
            st.write(f"**{conv.get('user','')}**")
            st.markdown("**Réponse AGNO :**")
            if conv.get("success") and conv.get("assistant"):
                st.write(conv.get("assistant"))
                dur = float(conv.get("duration", 0.0))
                badge = "🟢" if dur < 3 else ("🟡" if dur < 8 else "🔴")
                st.caption(f"{badge} Temps AGNO: {dur:.2f}s")
            else:
                st.error("Réponse indisponible")

            with st.expander("📖 Sources utilisées"):
                sources = conv.get("retrieved", [])
                if sources:
                    for i, s in enumerate(sources, start=1):
                        meta = s.get("meta", {})
                        # Use the new similarity score if available, otherwise convert distance
                        similarity_score = s.get("similarity", 0.0)
                        if similarity_score == 0.0:
                            distance = float(s.get("score", 0.0))
                            similarity_score = max(0.0, 1.0 - distance) if distance <= 1.0 else 1.0 / (1.0 + distance)
                        
                        st.markdown(
                            f"**🔗 Source {i}:** {meta.get('doc_name','Inconnu')} (Score: {similarity_score:.3f})"
                        )
                        preview = (s.get("text") or "")[:400]
                        st.text(f"<start page {meta.get('page', '0')}> " + preview + ("…" if len((s.get('text') or '')) > 400 else ""))
                else:
                    st.info("Aucune source trouvée pour cette question.")
            st.divider()

def render_footer():
    st.divider()
    st.markdown(
        """

        <div style='text-align: center; color: #666; padding: 12px;'>

            <p>🇸🇳 <strong>chatBOCS AGNO</strong> - Assistant IA Génération</p>

            <p>🚀 Powered by AGNO Framework + Groq + FastEmbed + LanceDB</p>

            <p>Développé pour le Bureau Opérationnel de Coordination et de Suivi (BOCS)</p>

        </div>

        """,

        unsafe_allow_html=True,

    )
