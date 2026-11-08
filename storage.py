import os
import json
import uuid
import time
import zipfile
from datetime import datetime
import streamlit as st

DB_FILE = "dai_foolish_db.json"
VAULT_DIR = "knowledge_vault"
os.makedirs(VAULT_DIR, exist_ok=True)


def create_default_db():
    first_id = str(uuid.uuid4())[:8]
    return {
        "current_thread_id": first_id,
        "total_requests": 0,
        "threads": {
            first_id: {
                "title": "Nghiên cứu Tự động hóa",
                "created_at": datetime.now().strftime("%d/%m %H:%M"),
                "messages": [],
                "files": []
            }
        }
    }


def load_database():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "threads" in data and data["threads"]:
                    if "total_requests" not in data:
                        data["total_requests"] = 0
                    return data
        except Exception:
            pass
    default_db = create_default_db()
    save_database(default_db)
    return default_db


def save_database(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def init_session_storage():
    if "db" not in st.session_state:
        st.session_state.db = load_database()
    if "gemini_cache" not in st.session_state:
        st.session_state.gemini_cache = {}
    if "queued_prompt" not in st.session_state:
        st.session_state.queued_prompt = None
    if "key_index" not in st.session_state:
        st.session_state.key_index = 0

    db = st.session_state.db
    if db["current_thread_id"] not in db["threads"]:
        db["current_thread_id"] = list(db["threads"].keys())[-1]
        save_database(db)


def create_new_thread():
    db = st.session_state.db
    # Nếu đoạn chat hiện tại đang trống hoàn toàn thì không tạo đoạn chat rác mới
    curr = db["threads"].get(db["current_thread_id"])
    if curr and len(curr["messages"]) == 0 and len(curr["files"]) == 0:
        return

    new_id = str(uuid.uuid4())[:8]
    db["threads"][new_id] = {
        "title": f"Chat mới ({datetime.now().strftime('%H:%M')})",
        "created_at": datetime.now().strftime("%d/%m %H:%M"),
        "messages": [],
        "files": []
    }
    db["current_thread_id"] = new_id
    save_database(db)


def switch_thread(thread_id):
    db = st.session_state.db
    if thread_id in db["threads"]:
        db["current_thread_id"] = thread_id
        save_database(db)


def delete_thread(thread_id):
    db = st.session_state.db
    if len(db["threads"]) > 1 and thread_id in db["threads"]:
        del db["threads"][thread_id]
        if db["current_thread_id"] == thread_id:
            db["current_thread_id"] = list(db["threads"].keys())[-1]
        save_database(db)


def process_and_save_uploads(uploaded_files, client, current_id, current_thread):
    attached_names = []
    db = st.session_state.db

    def _save_single(file_bytes, fname):
        safe_name = f"{current_id}_{int(time.time())}_{os.path.basename(fname)}"
        local_path = os.path.join(VAULT_DIR, safe_name)
        with open(local_path, "wb") as f:
            f.write(file_bytes)
        g_file = client.files.upload(file=local_path)
        st.session_state.gemini_cache[local_path] = g_file
        current_thread["files"].append({"display_name": fname, "local_path": local_path})

    for uf in uploaded_files:
        if uf.name.lower().endswith(".zip"):
            with zipfile.ZipFile(uf) as z:
                for sub_name in z.namelist():
                    if not sub_name.endswith("/") and sub_name.lower().endswith((".pdf", ".png", ".jpg", ".jpeg", ".txt")):
                        clean_name = os.path.basename(sub_name)
                        _save_single(z.read(sub_name), clean_name)
                        attached_names.append(clean_name)
        else:
            _save_single(uf.read(), uf.name)
            attached_names.append(uf.name)

    save_database(db)
    return attached_names
