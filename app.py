import streamlit as st
from google import genai
from google.genai import types
import os
import tempfile
import zipfile

# 1. Cấu hình trang
st.set_page_config(
    page_title="Automation AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. CSS tùy chỉnh giao diện chuẩn Gemini
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}

    .block-container {
        max-width: 860px !important;
        padding-top: 2rem !important;
        padding-bottom: 6rem !important;
    }

    .gemini-greeting {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .gemini-sub {
        font-size: 1.3rem;
        color: #8e918f;
        margin-bottom: 2rem;
    }

    [data-testid="stChatMessage"] {
        border-radius: 18px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }

    /* Thẻ hiển thị file đính kèm gọn đẹp trong tin nhắn */
    .file-chip {
        display: inline-block;
        background: rgba(66, 133, 244, 0.15);
        border: 1px solid rgba(66, 133, 244, 0.35);
        border-radius: 10px;
        padding: 4px 10px;
        margin: 2px 6px 8px 0;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# 3. Kết nối API Key
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=API_KEY)
except Exception:
    st.error("⚠️ Chưa tìm thấy GEMINI_API_KEY trong phần Secrets của Streamlit.")
    st.stop()

# 4. Khởi tạo bộ nhớ: Lưu tin nhắn + Lưu toàn bộ file đã nạp trong đoạn chat
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_files" not in st.session_state:
    st.session_state.session_files = []  # Lưu danh sách file AI đang nhớ trong phiên chat

# 5. Sidebar: Hiển thị các tài liệu AI đang "nhớ" trong đầu
with st.sidebar:
    st.markdown("### ⚙️ Bảng điều khiển")
    study_mode = st.selectbox(
        "Chế độ chuyên môn:",
        [
            "Tổng hợp (Tự động hóa & Đại cương)",
            "PLC & Điện Công Nghiệp",
            "Vi điều khiển (STM32 / ESP32)",
            "Lý thuyết điều khiển & Toán/Xác suất"
        ]
    )
    
    st.divider()
    st.markdown(f"### 🧠 Dữ liệu đang nhớ ({len(st.session_state.session_files)} file)")
    if st.session_state.session_files:
        st.caption("AI đang ghi nhớ các file này cho toàn bộ cuộc trò chuyện:")
        for f_info in st.session_state.session_files:
            st.markdown(f"- 📄 `{f_info['display_name']}`")
    else:
        st.caption("Chưa có tài liệu nào được nạp. Hãy bấm nút kẹp giấy ở khung chat để tải file hoặc file .zip chứa cả folder!")

    st.divider()
    if st.button("🗑️ Làm mới cuộc trò chuyện & Xóa bộ nhớ", use_container_width=True):
        # Dọn dẹp file trên server Gemini trước khi reset
        for f_info in st.session_state.session_files:
            try:
                client.files.delete(name=f_info["gemini_obj"].name)
            except Exception:
                pass
        st.session_state.messages = []
        st.session_state.session_files = []
        st.rerun()

# 6. Màn hình chờ khi chưa có tin nhắn
if len(st.session_state.messages) == 0:
    st.markdown('<div class="gemini-greeting">Xin chào Quang Minh,</div>', unsafe_allow_html=True)
    st.markdown('<div class="gemini-sub">Đính kèm file bài giảng (PDF, Ảnh hoặc .ZIP cả thư mục) ngay tại thanh chat bên dưới nhé!</div>', unsafe_allow_html=True)

# 7. Hiển thị lịch sử chat (Kèm tên các file đã gửi ở từng lượt)
for msg in st.session_state.messages:
    avatar_icon = "🧑‍💻" if msg["role"] == "user" else "✨"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        if msg.get("attached_names"):
            chips_html = "".join([f'<span class="file-chip">📄 {name}</span>' for name in msg["attached_names"]])
            st.markdown(chips_html, unsafe_allow_html=True)
        st.markdown(msg["content"])

# Hàm phụ trợ: Upload 1 file lên Gemini và lưu vào bộ nhớ phiên chat
def upload_to_gemini_memory(file_bytes, filename):
    suffix = os.path.splitext(filename)[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    g_file = client.files.upload(file=tmp_path)
    os.remove(tmp_path)
    st.session_state.session_files.append({
        "display_name": filename,
        "gemini_obj": g_file
    })

# 8. Thanh Chat Input tích hợp nút đính kèm file (Gửi xong tự động mất file ở ô nhập!)
user_submission = st.chat_input(
    "Nhập câu hỏi và đính kèm file (PDF, Ảnh, hoặc nén cả folder thành .ZIP)...",
    accept_file="multiple",
    file_type=["pdf", "png", "jpg", "jpeg", "txt", "zip"]
)

if user_submission:
    prompt_text = user_submission.text or "Hãy phân tích và tóm tắt tài liệu đính kèm này."
    newly_uploaded_files = user_submission.files
    attached_names = []

    # Nếu người dùng có đính kèm file mới ở lượt chat này
    if newly_uploaded_files:
        with st.spinner("Đang nạp tài liệu vào bộ nhớ của AI..."):
            for uf in newly_uploaded_files:
                # Nếu là file .ZIP (nén cả folder), tự động giải nén và nạp từng file
                if uf.name.lower().endswith(".zip"):
                    with zipfile.ZipFile(uf) as z:
                        for sub_name in z.namelist():
                            if not sub_name.endswith("/") and sub_name.lower().endswith((".pdf", ".png", ".jpg", ".jpeg", ".txt")):
                                file_data = z.read(sub_name)
                                clean_name = os.path.basename(sub_name)
                                upload_to_gemini_memory(file_data, clean_name)
                                attached_names.append(clean_name)
                else:
                    upload_to_gemini_memory(uf.read(), uf.name)
                    attached_names.append(uf.name)

    # Lưu và hiển thị tin nhắn của người dùng
    st.session_state.messages.append({
        "role": "user",
        "content": prompt_text,
        "attached_names": attached_names
    })
    with st.chat_message("user", avatar="🧑‍💻"):
        if attached_names:
            chips_html = "".join([f'<span class="file-chip">📄 {name}</span>' for name in attached_names])
            st.markdown(chips_html, unsafe_allow_html=True)
        st.markdown(prompt_text)

    # AI xử lý với TOÀN BỘ file đã tích lũy trong đoạn chat + TOÀN BỘ lịch sử chat
    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("Đang tổng hợp kiến thức từ bộ nhớ phiên chat..."):
            contents = []
            
            # Đưa toàn bộ file trong bộ nhớ phiên chat vào để AI càng hỏi càng thông minh
            for f_info in st.session_state.session_files:
                contents.append(f_info["gemini_obj"])

            # Ghép toàn bộ lịch sử trò chuyện trong đoạn chat
            history = "\n".join([
                f"{'Người dùng' if m['role'] == 'user' else 'AI'}: {m['content']}"
                for m in st.session_state.messages[-15:]
            ])

            # System Prompt sửa lỗi lặp công thức LaTeX
            system_instruction = (
                f"Bạn là trợ lý AI học tập đại học (Chế độ: {study_mode}). "
                "Hãy kết hợp toàn bộ các tài liệu đã được tải lên trong phiên làm việc và lịch sử trò chuyện để trả lời sâu sắc, chính xác. "
                "QUY TẮC TOÁN HỌC QUAN TRỌNG: Khi viết công thức, chỉ viết 1 lần duy nhất trong cặp dấu $...$ (ví dụ: $\\bar{x} = \\frac{\\sum x_i}{n}$) "
                "hoặc $$...$$ cho công thức dòng riêng. Tuyệt đối KHÔNG viết lặp lại công thức ở dạng chữ thường bên cạnh LaTeX để tránh lỗi hiển thị lặp dòng."
            )

            contents.append(f"Lịch sử trao đổi trong phiên:\n{history}\n\nYêu cầu hiện tại: {prompt_text}")

            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                    )
                )
                reply = response.text
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"Lỗi phản hồi: {e}")
