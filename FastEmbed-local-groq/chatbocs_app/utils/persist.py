# chatbocs_app/utils/persist.py
import os, tempfile

def persist_uploaded_file(uploaded_file, upload_root: str):
    os.makedirs(upload_root, exist_ok=True)
    tmp_dir = tempfile.mkdtemp(dir=upload_root)
    fpath = os.path.join(tmp_dir, uploaded_file.name)
    with open(fpath, "wb") as f:
        f.write(uploaded_file.getvalue())
    return tmp_dir, fpath
