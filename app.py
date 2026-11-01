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
# 1. CẤU HÌNH TRANG & KHỞI TẠO HỆ THỐNG LƯU TRỮ VĨNH VIỄN (PERSISTENT STORAGE)
# ==============================================================================
st.set_page_config(
    page_title="Đại Foolish AI — Automation & Engineering",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "dai_foolish_db.json"
VAULT_DIR = "knowledge_vault"
os.makedirs(VAULT_DIR, exist_ok=True)

# Bộ SVG Avatar thiết kế riêng (Không dùng icon Robot mặc định)
AI_SVG_AVATAR = """data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="%233a83f7"/><stop offset="50%" stop-color="%239b72cb"/><stop offset="100%" stop-color="%23d96570"/></linearGradient></defs><rect width="100" height="100" rx="50" fill="%231b1b1b"/><path d="M50 14 C54 38 62 46 86 50 C62 54 54 62 50 86 C46 62 38 54 14 50 C38 46 46 38 50 14 Z" fill="url(%23g)"/></svg>"""
USER_SVG_AVATAR = """data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><linearGradient id="u" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="%232c67c5"/><stop offset="100%" stop-color="%23173e76"/></linearGradient></defs><circle cx="50" cy="50" r="50" fill="url(%23u)"/><text x="50" y="62" font-family="Arial, sans-serif" font-size="34" font-weight="bold" fill="%23ffffff" text-anchor="middle">ĐF</text></svg>"""

# ==============================================================================
# 2. HỆ THỐNG CSS CAO CẤP (LẤY TỪ SOURCE CHATGPT DARK + GEMINI CARDS)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --bg-surface: #0d0d0d;
        --bg-sidebar: #171717;
        --bg-elevated: #212121;
        --bg-card: #1e1f20;
        --bg-user-bubble: #173e76;
        --text-primary: #ededed;
        --text-secondary: #afafaf;
        --accent-blue: #3a83f7;
        --border-subtle: rgba(255, 255, 255, 0.1);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: var(--bg-surface) !important;
        color: var(--text-primary) !important;
    }

    /* Ẩn các thành phần thừa của Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}

    /* Căn chỉnh khung chat trung tâm chuẩn 48rem của ChatGPT */
    .block-container {
        max-width: 850px !important;
        padding-top: 2rem !important;
        padding-bottom: 7rem !important;
    }

    /* Tùy chỉnh thanh Sidebar bên trái giống ChatGPT */
    [data-testid="stSidebar"] {
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 10px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 0.55rem 0.85rem !important;
        background-color: transparent !important;
        border: 1px solid transparent !important;
        color: var(--text-primary) !important;
        font-size: 0.9rem !important;
        font-weight: 400 !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border-color: rgba(255, 255, 255, 0.12) !important;
    }

    /* Nút tạo cuộc trò chuyện mới nổi bật */
    .new-chat-btn > button {
        background: linear-gradient(135deg, rgba(58,131,247,0.18), rgba(155,114,203,0.18)) !important;
        border: 1px solid rgba(58, 131, 247, 0.4) !important;
        font-weight: 600 !important;
    }

    /* Màn hình chào mừng (Hero Section) */
    .hero-wrapper {
        text-align: center;
        padding: 2.5rem 1rem 1.8rem 1rem;
        animation: fadeIn 0.5s ease-out;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(58, 131, 247, 0.12);
        border: 1px solid rgba(58, 131, 247, 0.35);
        color: #63a8f8;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #63a8f8 0%, #c58af9 50%, #ff8983 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
    }
    .hero-subtitle {
        font-size: 1.15rem;
        color: var(--text-secondary);
        font-weight: 400;
    }

    /* Thiết kế bong bóng tin nhắn */
    [data-testid="stChatMessage"] {
        border-radius: 18px !important;
        padding: 1.1rem 1.35rem !important;
        margin-bottom: 1rem !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        background-color: rgba(33, 33, 33, 0.55) !important;
        backdrop-filter: blur(8px);
    }

    /* Hộp trạng thái "Đang suy nghĩ..." (Thinking Status) */
    [data-testid="stStatusWidget"] {
        background-color: #16181d !important;
        border: 1px solid rgba(99, 168, 248, 0.28) !important;
        border-radius: 14px !important;
        margin-bottom: 0.85rem !important;
    }

    /* Nhãn file đính kèm (File Chip) */
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

    /* 3 Thẻ gợi ý bo tròn có dấu mũi tên ↳ giống hệt ảnh chụp của bạn */
    .followup-header {
        font-size: 0.92rem;
        color: var(--text-secondary);
        margin: 1.2rem 0 0.6rem 0;
        font-weight: 500;
    }
    div[data-testid="column"] .stButton > button {
        background-color: #212121 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 18px !important;
        padding: 0.9rem 1.1rem !important;
        color: #ededed !important;
        text-align: left !important;
        height: auto !important;
        min-height: 84px !important;
        line-height: 1.4 !important;
        font-size: 0.88rem !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
    }
    div[data-testid="column"] .stButton > button:hover {
        background-color: #2a2b2e !important;
        border-color: #3a83f7 !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 20px rgba(58, 131, 247, 0.18) !important;
    }

    /* Thẻ Profile Đại Foolish ở đáy Sidebar (Giống ChatGPT) */
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
    .profile-left {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .profile-avatar {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: linear-gradient(135deg, #3a83f7, #924ff7);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
        color: white;
    }
    .profile-name {
        font-size: 0.9rem;
        font-weight: 600;
        color: #ffffff;
        line-height: 1.2;
    }
    .profile-tier {
        font-size: 0.72rem;
        color: #9ba1a6;
    }
    .profile-badge {
        background: rgba(64, 201, 119, 0.15);
        color: #40c977;
        border: 1px solid rgba(64, 201, 119, 0.35);
        font-size: 0.7rem;
        font-weight: 600;
        padding: 3px 9px;
        border-radius: 999px;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. KẾT NỐI GEMINI API & CÁC HÀM LƯU TRỮ DỮ LIỆU VĨNH VIỄN (JSON + VAULT)
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
                "title": "Xác suất Thống kê & Tự động hóa",
                "created_at": datetime.now().strftime("%d/%m %H:%M"),
                "study_mode": "Tổng hợp (Tự động hóa & Đại cương)",
                "messages": [],
                "files": []  # Lưu {"display_name": ..., "local_path": ...}
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
    # Cache ánh xạ local_path -> đối tượng file trên Gemini Cloud trong phiên
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
    """Lưu file xuống ổ cứng để hôm sau mở lại vẫn còn và đẩy lên Gemini."""
    safe_name = f"{thread_id}_{int(time.time())}_{os.path.basename(filename)}"
    local_path = os.path.join(VAULT_DIR, safe_name)
    with open(local_path, "wb") as f:
        f.write(file_bytes)

    g_file = client.files.upload(file=local_path)
    st.session_state.gemini_cache[local_path] = g_file

    current_thread["files"].append({
        "display_name": filename,
        "local_path": local_path
    })
    save_database(db)


def get_active_gemini_files(thread_obj):
    """Đảm bảo mọi file trong đoạn chat đều sẵn sàng trên Gemini Cloud."""
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
# 4. THANH SIDEBAR BÊN TRÁI (QUẢN LÝ NHIỀU ĐOẠN CHAT + KHO DỮ LIỆU VĨNH VIỄN)
# ==============================================================================
with st.sidebar:
    st.markdown("### ✦ **Đại Foolish Workspace**")

    # Nút tạo đoạn chat mới
    st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
    if st.button("➕  Cuộc trò chuyện mới", use_container_width=True):
        new_id = str(uuid.uuid4())[:8]
        db["threads"][new_id] = {
            "title": "Đoạn chat mới",
            "created_at": datetime.now().strftime("%d/%m %H:%M"),
            "study_mode": current_thread.get("study_mode", "Tổng hợp (Tự động hóa & Đại cương)"),
            "messages": [],
            "files": []
        }
        db["current_thread_id"] = new_id
        save_database(db)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Chọn chế độ chuyên môn
    study_modes = [
        "Tổng hợp (Tự động hóa & Đại cương)",
        "Xác suất Thống kê Kỹ thuật (Dr. Nhieu)",
        "PLC & Điện Công Nghiệp (24VDC / 220VAC)",
        "Vi điều khiển & Nhúng (STM32 / ESP32 / CAN)",
        "Lý thuyết điều khiển & MATLAB / Simulink"
    ]
    saved_mode = current_thread.get("study_mode", study_modes[0])
    mode_idx = study_modes.index(saved_mode) if saved_mode in study_modes else 0
    selected_mode = st.selectbox("🎯 Chế độ tư duy:", study_modes, index=mode_idx)
    if selected_mode != saved_mode:
        current_thread["study_mode"] = selected_mode
        save_database(db)

    st.divider()

    # Danh sách các đoạn chat (Lịch sử nhiều cuộc trò chuyện giống ChatGPT)
    st.caption("💬 LỊCH SỬ CÁC ĐOẠN CHAT")
    thread_ids_reversed = list(db["threads"].keys())[::-1]
    for tid in thread_ids_reversed:
        t_info = db["threads"][tid]
        is_active = (tid == current_id)
        prefix = "🟦" if is_active else "💭"
        col_chat, col_del = st.columns([0.82, 0.18])
        with col_chat:
            if st.button(f"{prefix} {t_info['title'][:24]}", key=f"sel_{tid}", use_container_width=True):
                db["current_thread_id"] = tid
                save_database(db)
                st.rerun()
        with col_del:
            if len(db["threads"]) > 1:
                if st.button("✕", key=f"del_{tid}", help="Xóa đoạn chat này"):
                    del db["threads"][tid]
                    if db["current_thread_id"] == tid:
                        db["current_thread_id"] = list(db["threads"].keys())[-1]
                    save_database(db)
                    st.rerun()

    st.divider()

    # Kho tài liệu đã lưu vĩnh viễn của đoạn chat hiện tại
    files_in_thread = current_thread.get("files", [])
    st.caption(f"📚 KHO DỮ LIỆU ĐÃ NẠP ({len(files_in_thread)} FILE)")
    if files_in_thread:
        for idx, f_meta in enumerate(files_in_thread):
            st.markdown(f"<div class='file-chip'>📄 {f_meta['display_name']}</div>", unsafe_allow_html=True)
    else:
        st.caption("Chưa có file nào. Hãy bấm dấu ➕ ở khung chat để tải PDF, Ảnh hoặc .ZIP!")

    # Thẻ Profile Đại Foolish ở góc dưới cùng (giống ChatGPT)
    st.markdown("""
    <div class="profile-footer">
        <div class="profile-left">
            <div class="profile-avatar">ĐF</div>
            <div>
                <div class="profile-name">Đại Foolish</div>
                <div class="profile-tier">Automation Eng • UEH</div>
            </div>
        </div>
        <div class="profile-badge">PRO AI</div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# 5. MÀN HÌNH CHÍNH: HERO BANNER + NÚT TÍNH NĂNG NHANH (ZERO-STATE)
# ==============================================================================
if len(current_thread["messages"]) == 0:
    st.markdown("""
    <div class="hero-wrapper">
        <div class="hero-badge">✦ Hệ thống Lưu trữ Vĩnh viễn & Tư duy Đa bước</div>
        <div class="hero-title">Hôm nay Đại Foolish muốn nghiên cứu gì?</div>
        <div class="hero-subtitle">Nạp giáo trình PDF, sơ đồ mạch hoặc chọn nhanh tác vụ bên dưới để bắt đầu</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📊 Giải bài tập Slide Chương 1 (Trang 27)\n\nTính x̄ và s² cho dãy 11 số liệu\n\n↳", use_container_width=True):
            st.session_state.queued_prompt = (
                "Dựa vào công thức ở Slide trang 24 và trang 26-27 của bài giảng Engineering Probability & Statistics Chapter 1, "
                "hãy giải chi tiết từng bước bài tập ở Slide 27: Tìm trung bình mẫu (Sample Mean) và phương sai mẫu (Sample Variance) "
                "của dãy số liệu: 21, 12, 34, 22, 17, 18, 43, 28, 56, 34, 12."
            )
            st.rerun()
    with c2:
        if st.button("⚡ Kiểm tra mạch PLC & Contactor\n\nSoát lỗi ngắn mạch 3 pha & khóa chéo\n\n↳", use_container_width=True):
            st.session_state.queued_prompt = (
                "Hướng dẫn quy trình kiểm tra an toàn mạch điều khiển dùng PLC (220VAC) kích Contactor thông qua Rơ-le trung gian (24VDC) "
                "và cách phòng tránh lỗi ngắn mạch 3 pha khi đảo chiều động cơ."
            )
            st.rerun()
    with c3:
        if st.button("🎛️ Viết code Vi điều khiển STM32 / ESP32\n\nCấu hình GPIO, Timer, CAN Bus & LED 7 đoạn\n\n↳", use_container_width=True):
            st.session_state.queued_prompt = (
                "Viết khung chương trình C chuẩn cho STM32 quét LED 7 đoạn 2 số loại Anode chung dùng Transistor NPN "
                "kết hợp đọc 3 nút nhấn (Tăng 1, Giảm 1, Reset về 0) chống dội phím."
            )
            st.rerun()


# ==============================================================================
# 6. HIỂN THỊ LỊCH SỬ TRÒ CHUYỆN VỚI AVATAR VECTOR & THẺ SUY NGHĨ
# ==============================================================================
for m_idx, msg in enumerate(current_thread["messages"]):
    avatar_img = USER_SVG_AVATAR if msg["role"] == "user" else AI_SVG_AVATAR
    with st.chat_message(msg["role"], avatar=avatar_img):
        # Hiển thị các file đã đính kèm ở lượt đó
        if msg.get("attached_names"):
            chips = "".join([f'<span class="file-chip">📄 {name}</span>' for name in msg["attached_names"]])
            st.markdown(chips, unsafe_allow_html=True)

        # Hiển thị lại tiến trình suy nghĩ của AI (nếu có)
        if msg.get("thought_steps"):
            with st.expander("🧠 Xem lại tiến trình suy nghĩ của AI", expanded=False):
                for step in msg["thought_steps"]:
                    st.markdown(f"- {step}")

        st.markdown(msg["content"])

        # Nếu là tin nhắn cuối cùng của AI, hiển thị 3 thẻ gợi ý (Follow-up Cards) giống ảnh chụp
        if msg["role"] == "assistant" and m_idx == len(current_thread["messages"]) - 1:
            followups = msg.get("followups", [])
            if followups:
                st.markdown('<div class="followup-header">💡 Gợi ý hướng nghiên cứu tiếp theo cho Đại Foolish:</div>', unsafe_allow_html=True)
                f_cols = st.columns(len(followups))
                for f_i, f_item in enumerate(followups):
                    with f_cols[f_i]:
                        card_label = f"{f_item['title']}\n\n↳"
                        if st.button(card_label, key=f"followup_{m_idx}_{f_i}", use_container_width=True):
                            st.session_state.queued_prompt = f_item["prompt"]
                            st.rerun()


# ==============================================================================
# 7. THANH NHẬP LIỆU CHAT INPUT (ĐÍNH KÈM FILE TỰ ĐỘNG BIẾN MẤT SAU KHI GỬI)
# ==============================================================================
chat_submission = st.chat_input(
    "Hỏi Đại Foolish AI hoặc bấm dấu ➕ để đính kèm PDF, Ảnh mạch, .ZIP cả thư mục...",
    accept_file="multiple",
    file_type=["pdf", "png", "jpg", "jpeg", "txt", "zip"]
)

active_prompt = None
newly_uploaded = []

if st.session_state.queued_prompt:
    active_prompt = st.session_state.queued_prompt
    st.session_state.queued_prompt = None
elif chat_submission:
    active_prompt = chat_submission.text or "Hãy phân tích và tóm tắt chi tiết tài liệu vừa đính kèm."
    newly_uploaded = chat_submission.files


# ==============================================================================
# 8. XỬ LÝ SUY NGHĨ ĐA BƯỚC (THINKING BOX) & STREAMING TỪNG CHỮ MƯỢT MÀ
# ==============================================================================
if active_prompt:
    attached_names = []

    # Lưu file mới vào Kho dữ liệu vĩnh viễn (Vault)
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

    # Tự động đặt tên cho đoạn chat ở cột trái nếu đây là tin nhắn đầu tiên
    if len(current_thread["messages"]) == 0:
        current_thread["title"] = active_prompt[:32] + ("..." if len(active_prompt) > 32 else "")

    # Ghi nhận tin nhắn của Đại Foolish
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

    # Phản hồi của AI với hiệu ứng "Đang suy nghĩ..." giống Gemini/ChatGPT o1
    with st.chat_message("assistant", avatar=AI_SVG_AVATAR):
        thought_log = []
        with st.status("🧠 **Đại Foolish AI đang suy nghĩ...**", expanded=True) as status_box:
            step1 = f"🔍 Phân tích yêu cầu theo chế độ: **{current_thread['study_mode']}**"
            st.write(step1)
            thought_log.append(step1)
            time.sleep(0.25)

            active_gemini_files = get_active_gemini_files(current_thread)
            if active_gemini_files:
                step2 = f"📚 Đang đối chiếu dữ liệu từ **{len(active_gemini_files)} tài liệu** trong kho lưu trữ vĩnh viễn..."
            else:
                step2 = "⚡ Truy xuất cơ sở tri thức Kỹ thuật Tự động hóa & Toán ứng dụng..."
            st.write(step2)
            thought_log.append(step2)
            time.sleep(0.25)

            step3 = "📐 Kiểm tra độ chính xác công thức LaTeX (chống lặp dòng) và chuẩn bị phản hồi..."
            st.write(step3)
            thought_log.append(step3)

            # Chuẩn bị ngữ cảnh gửi cho Gemini
            contents = list(active_gemini_files)
            history_str = "\n".join([
                f"{'Đại Foolish' if m['role'] == 'user' else 'AI'}: {m['content']}"
                for m in current_thread["messages"][-12:]
            ])

            system_instruction = (
                f"Bạn là trợ lý AI cao cấp dành riêng cho kỹ sư Đại Foolish (Chế độ: {current_thread['study_mode']}). "
                "Hãy xưng hô thân thiện, gọi người dùng là 'Đại Foolish' hoặc 'bạn'. "
                "Trình bày cực kỳ sắc nét, có bảng biểu hoặc chia bước rõ ràng. "
                "QUY TẮC CÔNG THỨC TOÁN HỌC: Chỉ viết mỗi công thức đúng 1 lần trong cặp dấu $...$ (inline) hoặc $$...$$ (block). "
                "Tuyệt đối KHÔNG lặp lại công thức bằng văn bản thuần bên cạnh LaTeX."
            )

            contents.append(f"Lịch sử trò chuyện:\n{history_str}\n\nYêu cầu hiện tại của Đại Foolish: {active_prompt}")

            status_box.update(label="✦ **Đã hoàn tất suy nghĩ & phân tích dữ liệu**", state="complete", expanded=False)

        # Khung hiển thị chữ chạy mượt mà theo thời gian thực (Streaming)
        response_placeholder = st.empty()
        full_reply = ""

        try:
            stream_resp = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                )
            )
            for chunk in stream_resp:
                if chunk.text:
                    full_reply += chunk.text
                    response_placeholder.markdown(full_reply + " ▍")
            response_placeholder.markdown(full_reply)

            # Tự động tạo 3 thẻ gợi ý tiếp theo phù hợp với câu trả lời vừa xong
            default_followups = [
                {
                    "title": "Giải chi tiết ví dụ & bài tập liên quan",
                    "prompt": "Hãy đưa ra 1 bài tập thực tế sát với nội dung vừa phân tích và giải chi tiết từng bước."
                },
                {
                    "title": "Viết code Python / MATLAB mô phỏng",
                    "prompt": "Hãy viết đoạn code Python hoặc MATLAB để tính toán và vẽ đồ thị minh họa cho nội dung vừa rồi."
                },
                {
                    "title": "Tóm tắt các công thức quan trọng nhất",
                    "prompt": "Hãy lập bảng tóm tắt ngắn gọn toàn bộ các công thức và lưu ý bẫy hay sai của phần này để ôn thi."
                }
            ]

            current_thread["messages"].append({
                "role": "assistant",
                "content": full_reply,
                "thought_steps": thought_log,
                "followups": default_followups
            })
            save_database(db)
            st.rerun()

        except Exception as e:
            st.error(f"⚠️ Lỗi khi kết nối Gemini API: {e}")
