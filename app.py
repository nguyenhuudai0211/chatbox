import streamlit as st
from google import genai
from google.genai import types
import os
import json
import uuid
import time
import zipfile
from datetime import datetime

# ==============================================================================
# 1. CẤU HÌNH TRANG & KHO LƯU TRỮ VĨNH VIỄN (PERSISTENT JSON DATABASE)
# ==============================================================================
st.set_page_config(
    page_title="Đại Foolish AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "dai_foolish_db.json"
VAULT_DIR = "knowledge_vault"
os.makedirs(VAULT_DIR, exist_ok=True)

AI_SVG_AVATAR = """data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="%233a83f7"/><stop offset="50%" stop-color="%239b72cb"/><stop offset="100%" stop-color="%23d96570"/></linearGradient></defs><rect width="100" height="100" rx="50" fill="%231b1b1b"/><path d="M50 14 C54 38 62 46 86 50 C62 54 54 62 50 86 C46 62 38 54 14 50 C38 46 46 38 50 14 Z" fill="url(%23g)"/></svg>"""
USER_SVG_AVATAR = """data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><linearGradient id="u" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="%232c67c5"/><stop offset="100%" stop-color="%23173e76"/></linearGradient></defs><circle cx="50" cy="50" r="50" fill="url(%23u)"/><text x="50" y="62" font-family="Arial, sans-serif" font-size="34" font-weight="bold" fill="%23ffffff" text-anchor="middle">ĐF</text></svg>"""

# ==============================================================================
# 2. GIAO DIỆN CSS DARK MODE CHUẨN CHATGPT & GEMINI
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --bg-surface: #0d0d0d;
        --bg-sidebar: #171717;
        --bg-elevated: #212121;
        --text-primary: #ededed;
        --text-secondary: #afafaf;
        --accent-blue: #3a83f7;
        --border-subtle: rgba(255, 255, 255, 0.1);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif !important;
        background-color: var(--bg-surface) !important;
        color: var(--text-primary) !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}

    .block-container {
        max-width: 860px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 7rem !important;
    }

    [data-testid="stSidebar"] {
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 10px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 0.5rem 0.75rem !important;
        background-color: transparent !important;
        border: 1px solid transparent !important;
        color: var(--text-primary) !important;
        font-size: 0.88rem !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border-color: rgba(255, 255, 255, 0.12) !important;
    }

    .new-chat-btn > button {
        background: linear-gradient(135deg, rgba(58,131,247,0.2), rgba(155,114,203,0.2)) !important;
        border: 1px solid rgba(58, 131, 247, 0.45) !important;
        font-weight: 600 !important;
    }

    .hero-wrapper {
        text-align: center;
        padding: 1.8rem 1rem 1.2rem 1rem;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #63a8f8 0%, #c58af9 50%, #ff8983 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: var(--text-secondary);
    }

    [data-testid="stChatMessage"] {
        border-radius: 18px !important;
        padding: 1.1rem 1.35rem !important;
        margin-bottom: 0.9rem !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        background-color: rgba(33, 33, 33, 0.55) !important;
    }

    .file-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(58, 131, 247, 0.15);
        border: 1px solid rgba(58, 131, 247, 0.4);
        color: #a8c7fa;
        border-radius: 10px;
        padding: 4px 12px;
        margin: 0 6px 8px 0;
        font-size: 0.82rem;
        font-weight: 500;
    }

    div[data-testid="column"] .stButton > button {
        background-color: #212121 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 0.85rem !important;
        color: #ededed !important;
        text-align: left !important;
        height: auto !important;
        min-height: 78px !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="column"] .stButton > button:hover {
        background-color: #2a2b2e !important;
        border-color: #3a83f7 !important;
        transform: translateY(-2px) !important;
    }

    .profile-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #212121;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 10px 12px;
        margin-top: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. QUẢN LÝ DATABASE VÀ PHIÊN LÀM VIỆC VĨNH VIỄN
# ==============================================================================
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=API_KEY)
except Exception:
    st.error("⚠️ Chưa tìm thấy `GEMINI_API_KEY` trong phần Secrets của Streamlit.")
    st.stop()


def create_default_db():
    first_id = str(uuid.uuid4())[:8]
    return {
        "current_thread_id": first_id,
        "threads": {
            first_id: {
                "title": "Nghiên cứu Tự động hóa & Thống kê",
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


if "db" not in st.session_state:
    st.session_state.db = load_database()
if "gemini_cache" not in st.session_state:
    st.session_state.gemini_cache = {}
if "queued_prompt" not in st.session_state:
    st.session_state.queued_prompt = None

db = st.session_state.db
current_id = db["current_thread_id"]
if current_id not in db["threads"]:
    current_id = list(db["threads"].keys())[0]
    db["current_thread_id"] = current_id
current_thread = db["threads"][current_id]


def save_file_to_vault(file_bytes, filename, thread_id):
    safe_name = f"{thread_id}_{int(time.time())}_{os.path.basename(filename)}"
    local_path = os.path.join(VAULT_DIR, safe_name)
    with open(local_path, "wb") as f:
        f.write(file_bytes)
    g_file = client.files.upload(file=local_path)
    st.session_state.gemini_cache[local_path] = g_file
    current_thread["files"].append({"display_name": filename, "local_path": local_path})
    save_database(db)


def get_active_gemini_files(thread_obj):
    ready_files = []
    for f_meta in thread_obj.get("files", []):
        lpath = f_meta["local_path"]
        if lpath in st.session_state.gemini_cache:
            ready_files.append(st.session_state.gemini_cache[lpath])
        elif os.path.exists(lpath):
            try:
                g_file = client.files.upload(file=lpath)
                st.session_state.gemini_cache[lpath] = g_file
                ready_files.append(g_file)
            except Exception:
                pass
    return ready_files


# ==============================================================================
# 4. SIDEBAR BÊN TRÁI: QUẢN LÝ LỊCH SỬ CHAT (ĐÃ FIX LỖI XEM LẠI CHAT CŨ)
# ==============================================================================
with st.sidebar:
    st.markdown("### ✦ **Đại Foolish Workspace**")

    st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
    if st.button("➕  Cuộc trò chuyện mới", use_container_width=True):
        new_id = str(uuid.uuid4())[:8]
        db["threads"][new_id] = {
            "title": "Đoạn chat mới",
            "created_at": datetime.now().strftime("%d/%m %H:%M"),
            "messages": [],
            "files": []
        }
        db["current_thread_id"] = new_id
        save_database(db)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    st.caption("💬 LỊCH SỬ CÁC ĐOẠN CHAT")

    # Hiển thị danh sách các đoạn chat và xử lý chuyển đổi qua lại mượt mà
    thread_ids_reversed = list(db["threads"].keys())[::-1]
    for tid in thread_ids_reversed:
        t_info = db["threads"][tid]
        is_active = (tid == current_id)
        prefix = "🟦" if is_active else "💭"
        
        col_c, col_d = st.columns([0.82, 0.18])
        with col_c:
            if st.button(f"{prefix} {t_info['title'][:22]}", key=f"nav_{tid}", use_container_width=True):
                db["current_thread_id"] = tid
                save_database(db)
                st.rerun()
        with col_d:
            if len(db["threads"]) > 1:
                if st.button("✕", key=f"del_{tid}", help="Xóa chat"):
                    del db["threads"][tid]
                    if db["current_thread_id"] == tid:
                        db["current_thread_id"] = list(db["threads"].keys())[-1]
                    save_database(db)
                    st.rerun()

    st.divider()
    files_in_thread = current_thread.get("files", [])
    st.caption(f"📚 TÀI LIỆU TRONG CHAT NÀY ({len(files_in_thread)})")
    if files_in_thread:
        for f_meta in files_in_thread:
            st.markdown(f"<div class='file-chip'>📄 {f_meta['display_name']}</div>", unsafe_allow_html=True)
    else:
        st.caption("Chưa có tài liệu đính kèm.")

    st.markdown("""
    <div class="profile-footer">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 32px; height: 32px; border-radius: 50%; background: #3a83f7; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.8rem; color: white;">ĐF</div>
            <div>
                <div style="font-size: 0.88rem; font-weight: 600;">Đại Foolish</div>
                <div style="font-size: 0.7rem; color: #9ba1a6;">Automation Engineer</div>
            </div>
        </div>
        <div style="background: rgba(64,201,119,0.15); color: #40c977; font-size: 0.68rem; padding: 2px 8px; border-radius: 99px; font-weight: 600;">PRO</div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# 5. ĐẶT CHẾ ĐỘ & MỨC ĐỘ SUY LUẬN NGAY NGOÀI KHUNG CHAT CHÍNH
# ==============================================================================
col_mode, col_reasoning = st.columns([1.3, 1])
with col_mode:
    study_modes = [
        "🤖 Tổng hợp thông minh (Đa năng)",
        "📊 Xác suất Thống kê Kỹ thuật (Dr. Nhieu)",
        "⚡ PLC & Điện Công Nghiệp (24VDC / 220VAC)",
        "🎛️ Vi điều khiển & Nhúng (STM32 / ESP32 / CAN)",
        "📈 Lý thuyết điều khiển & MATLAB / Simulink"
    ]
    selected_mode = st.selectbox("🎯 Chọn chuyên môn:", study_modes, label_visibility="collapsed")

with col_reasoning:
    reasoning_levels = {
        "⚡ Thấp (Nhanh - Code gọn, trực tiếp)": 0.1,
        "⚖️ Trung bình (Cân bằng - Chi tiết, chuẩn xác)": 0.3,
        "🧠 Cao (Siêu thông minh - Suy luận sâu, giải thích kỹ)": 0.7
    }
    selected_level = st.selectbox("⚙️ Mức độ suy luận:", list(reasoning_levels.keys()), index=1, label_visibility="collapsed")
    current_temperature = reasoning_levels[selected_level]

st.divider()


# ==============================================================================
# 6. MÀN HÌNH CHÀO MỪNG (ZERO-STATE) & CÁC NÚT TÁC VỤ NHANH
# ==============================================================================
if len(current_thread["messages"]) == 0:
    st.markdown("""
    <div class="hero-wrapper">
        <div class="hero-title">Chào Đại Foolish, ta có thể giúp gì cho bạn?</div>
        <div class="hero-subtitle">Chọn nhanh tác vụ bên dưới hoặc tải lên tài liệu để bắt đầu nghiên cứu</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📊 Giải bài tập Slide Chương 1\n\nTính x̄ và s² cho dãy 11 số liệu\n\n↳", use_container_width=True):
            st.session_state.queued_prompt = (
                "Dựa vào công thức ở Slide trang 24 và trang 26-27 của bài giảng Engineering Probability & Statistics Chapter 1, "
                "hãy giải chi tiết từng bước bài tập ở Slide 27: Tìm trung bình mẫu và phương sai mẫu của dãy số: 21, 12, 34, 22, 17, 18, 43, 28, 56, 34, 12."
            )
            st.rerun()
    with c2:
        if st.button("⚡ Kiểm tra mạch PLC & Contactor\n\nSoát lỗi ngắn mạch 3 pha & khóa chéo\n\n↳", use_container_width=True):
            st.session_state.queued_prompt = (
                "Hướng dẫn quy trình kiểm tra an toàn mạch điều khiển dùng PLC (220VAC) kích Contactor qua Rơ-le trung gian (24VDC) "
                "và cách phòng tránh lỗi ngắn mạch 3 pha khi đảo chiều động cơ."
            )
            st.rerun()
    with c3:
        if st.button("🎛️ Viết code Vi điều khiển STM32\n\nCấu hình GPIO, Timer, CAN Bus & LED 7 đoạn\n\n↳", use_container_width=True):
            st.session_state.queued_prompt = (
                "Viết khung chương trình C chuẩn cho STM32 quét LED 7 đoạn 2 số loại Anode chung dùng Transistor NPN "
                "kết hợp đọc 3 nút nhấn (Tăng 1, Giảm 1, Reset về 0) chống dội phím."
            )
            st.rerun()


# ==============================================================================
# 7. HIỂN THỊ LỊCH SỬ TRÒ CHUYỆN TRONG ĐOẠN CHAT HIỆN TẠI
# ==============================================================================
for m_idx, msg in enumerate(current_thread["messages"]):
    avatar_img = USER_SVG_AVATAR if msg["role"] == "user" else AI_SVG_AVATAR
    with st.chat_message(msg["role"], avatar=avatar_img):
        if msg.get("attached_names"):
            chips = "".join([f'<span class="file-chip">📄 {name}</span>' for name in msg["attached_names"]])
            st.markdown(chips, unsafe_allow_html=True)

        if msg.get("thought_steps"):
            with st.expander(f"🧠 Tiến trình suy luận (Mức độ: {msg.get('reasoning_label', 'Trung bình')})", expanded=False):
                for step in msg["thought_steps"]:
                    st.markdown(f"- {step}")

        st.markdown(msg["content"])

        # Thẻ gợi ý tiếp theo (Follow-up Cards) ở cuối câu trả lời AI
        if msg["role"] == "assistant" and m_idx == len(current_thread["messages"]) - 1:
            followups = msg.get("followups", [])
            if followups:
                st.markdown("<div style='font-size: 0.88rem; color: #afafaf; margin: 1rem 0 0.5rem 0;'>💡 Gợi ý tiếp theo cho Đại Foolish:</div>", unsafe_allow_html=True)
                f_cols = st.columns(len(followups))
                for f_i, f_item in enumerate(followups):
                    with f_cols[f_i]:
                        if st.button(f"{f_item['title']}\n\n↳", key=f"fu_{m_idx}_{f_i}", use_container_width=True):
                            st.session_state.queued_prompt = f_item["prompt"]
                            st.rerun()


# ==============================================================================
# 8. KHUNG NHẬP LỆNH NGẮN GỌN & THỰC THI TRUY VẤN AI (STREAMING)
# ==============================================================================
chat_submission = st.chat_input(
    "Hỏi Đại Foolish bất cứ điều gì hoặc bấm dấu ➕ để đính kèm PDF, Ảnh, .ZIP...",
    accept_file="multiple",
    file_type=["pdf", "png", "jpg", "jpeg", "txt", "zip"]
)

active_prompt = None
newly_uploaded = []

if st.session_state.queued_prompt:
    active_prompt = st.session_state.queued_prompt
    st.session_state.queued_prompt = None
elif chat_submission:
    active_prompt = chat_submission.text or "Hãy phân tích chi tiết tài liệu đính kèm."
    newly_uploaded = chat_submission.files

if active_prompt:
    attached_names = []
    if newly_uploaded:
        for uf in newly_uploaded:
            if uf.name.lower().endswith(".zip"):
                with zipfile.ZipFile(uf) as z:
                    for sub_name in z.namelist():
                        if not sub_name.endswith("/") and sub_name.lower().endswith((".pdf", ".png", ".jpg", ".jpeg", ".txt")):
                            clean_name = os.path.basename(sub_name)
                            save_file_to_vault(z.read(sub_name), clean_name, current_id)
                            attached_names.append(clean_name)
            else:
                save_file_to_vault(uf.read(), uf.name, current_id)
                attached_names.append(uf.name)

    if len(current_thread["messages"]) == 0:
        current_thread["title"] = active_prompt[:28] + ("..." if len(active_prompt) > 28 else "")

    current_thread["messages"].append({
        "role": "user",
        "content": active_prompt,
        "attached_names": attached_names
    })
    save_database(db)

    with st.chat_message("user", avatar=USER_SVG_AVATAR):
        if attached_names:
            chips = "".join([f'<span class="file-chip">📄 {name}</span>' for name in attached_names])
            st.markdown(chips, unsafe_allow_html=True)
        st.markdown(active_prompt)

    with st.chat_message("assistant", avatar=AI_SVG_AVATAR):
        thought_log = []
        with st.status(f"🧠 **Đang xử lý (Chế độ: {selected_mode} | Mức độ: {selected_level.split()[0]})**", expanded=True) as status_box:
            st.write(f"🔍 Chuyên môn kích hoạt: `{selected_mode}`")
            st.write(f"⚙️ Thiết lập mức nhiệt độ suy luận: `Temperature = {current_temperature}`")
            thought_log.append(f"Chuyên môn: {selected_mode} | Nhiệt độ: {current_temperature}")
            time.sleep(0.2)

            active_gemini_files = get_active_gemini_files(current_thread)
            if active_gemini_files:
                st.write(f"📚 Đã nạp thành công `{len(active_gemini_files)}` file tài liệu vào ngữ cảnh AI.")
            
            st.write("📐 Đang tổng hợp tri thức kỹ thuật và tối ưu hóa định dạng LaTeX...")
            thought_log.append("Đã đối chiếu kho lưu trữ vĩnh viễn và chuẩn bị phản hồi.")

            contents = list(active_gemini_files)
            history_str = "\n".join([
                f"{'Đại Foolish' if m['role'] == 'user' else 'AI'}: {m['content']}"
                for m in current_thread["messages"][-12:]
            ])

            system_instruction = (
                f"Bạn là trợ lý AI chuyên môn cao dành cho kỹ sư Đại Foolish. "
                f"Lĩnh vực hiện tại: {selected_mode}. "
                "Hãy xưng hô thân thiện, trình bày cực kỳ sắc bén, mạch lạc, dùng bảng biểu hoặc chia bước chi tiết. "
                "QUY TẮC TOÁN HỌC: Chỉ viết mỗi công thức đúng 1 lần duy nhất trong cặp dấu $...$ hoặc $$...$$. "
                "Tuyệt đối không lặp lại công thức bằng chữ thường bên cạnh LaTeX."
            )

            contents.append(f"Lịch sử:\n{history_str}\n\nYêu cầu hiện tại: {active_prompt}")

            status_box.update(label="✦ **Hoàn tất phân tích — Đang xuất kết quả...**", state="complete", expanded=False)

        response_placeholder = st.empty()
        full_reply = ""

        try:
            stream_resp = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=current_temperature,
                )
            )
            for chunk in stream_resp:
                if chunk.text:
                    full_reply += chunk.text
                    response_placeholder.markdown(full_reply + " ▍")
            response_placeholder.markdown(full_reply)

            default_followups = [
                {
                    "title": "Giải chi tiết ví dụ tính toán khác",
                    "prompt": "Hãy cho thêm một bài tập tương tự và hướng dẫn cách bấm máy tính hoặc giải chi tiết từng bước."
                },
                {
                    "title": "Viết mã nguồn minh họa bằng Python",
                    "prompt": "Hãy viết đoạn code Python ngắn gọn để tự động hóa hoặc kiểm chứng lại kết quả bài toán này."
                },
                {
                    "title": "Lập bảng tóm tắt kiến thức cốt lõi",
                    "prompt": "Hãy tổng hợp lại các công thức và các điểm cần chú ý nhất thành một bảng Markdown ngắn gọn."
                }
            ]

            current_thread["messages"].append({
                "role": "assistant",
                "content": full_reply,
                "thought_steps": thought_log,
                "reasoning_label": selected_level.split()[0],
                "followups": default_followups
            })
            save_database(db)
            st.rerun()

        except Exception as e:
            st.error(f"⚠️ Lỗi kết nối Gemini API: {e}")
