import streamlit as st
from google import genai
from google.genai import types
import os
import tempfile

# 1. Cấu hình trang
st.set_page_config(
    page_title="Automation AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed" # Ẩn bớt sidebar lúc mới vào cho thoáng giống Gemini
)

# 2. Chèn CSS tùy chỉnh để lột xác giao diện giống Gemini
st.markdown("""
<style>
    /* Ẩn header và footer mặc định của Streamlit cho giống web app thật */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}

    /* Căn giữa khu vực chat giống bố cục Gemini (không bị bè ngang toàn màn hình) */
    .block-container {
        max-width: 860px !important;
        padding-top: 2rem !important;
        padding-bottom: 6rem !important;
    }

    /* Hiệu ứng chữ Gradient đặc trưng của Google Gemini */
    .gemini-greeting {
        font-size: 2.6rem;
        font-weight: 700;
        background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        line-height: 1.2;
    }
    .gemini-sub {
        font-size: 1.35rem;
        color: #8e918f;
        margin-bottom: 2rem;
        font-weight: 400;
    }

    /* Tinh chỉnh khung tin nhắn bo tròn mềm mại */
    [data-testid="stChatMessage"] {
        border-radius: 18px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }

    /* Bo tròn thanh nhập câu hỏi (Chat Input) */
    [data-testid="stChatInput"] {
        border-radius: 999px !important;
    }

    /* Nút bấm gợi ý (Suggestion Chips) ở màn hình chờ */
    .stButton > button {
        border-radius: 16px !important;
        border: 1px solid rgba(128, 128, 128, 0.25) !important;
        padding: 0.85rem 1rem !important;
        text-align: left !important;
        height: auto !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        border-color: #4285f4 !important;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# 3. Kết nối API Key từ Streamlit Secrets
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=API_KEY)
except Exception:
    st.error("⚠️ Chưa tìm thấy GEMINI_API_KEY trong phần Secrets của Streamlit.")
    st.stop()

# 4. Khởi tạo bộ nhớ hội thoại
if "messages" not in st.session_state:
    st.session_state.messages = []

# 5. Thanh công cụ bên trái (Sidebar)
with st.sidebar:
    st.markdown("### ⚙️ Bảng điều khiển")
    study_mode = st.selectbox(
        "Chế độ chuyên môn:",
        [
            "Tổng hợp (Tự động hóa)",
            "PLC & Điện Công Nghiệp",
            "Vi điều khiển (STM32 / ESP32)",
            "Lý thuyết điều khiển & MATLAB"
        ]
    )
    
    st.divider()
    st.markdown("### 📂 Đính kèm tài liệu")
    st.caption("Tải lên Datasheet (PDF) hoặc ảnh sơ đồ mạch điện")
    uploaded_files = st.file_uploader(
        "Chọn file",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    st.divider()
    if st.button("🗑️ Cuộc trò chuyện mới", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 6. Màn hình chào mừng (Zero-State) giống hệt Gemini khi chưa có tin nhắn
selected_prompt = None
if len(st.session_state.messages) == 0:
    st.markdown('<div class="gemini-greeting">Xin chào Kỹ sư Tự động hóa,</div>', unsafe_allow_html=True)
    st.markdown('<div class="gemini-sub">Hôm nay chúng ta sẽ giải quyết bài toán hay sơ đồ mạch nào?</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚡ Kiểm tra an toàn mạch đảo chiều động cơ 3 pha dùng Contactor", use_container_width=True):
            selected_prompt = "Hãy hướng dẫn nguyên lý và kiểm tra các điểm cần lưu ý (khóa chéo điện, cơ khí) của mạch đảo chiều động cơ không đồng bộ 3 pha dùng 2 Contactor."
        if st.button("🎛️ Viết code STM32 đọc Encoder bằng Timer", use_container_width=True):
            selected_prompt = "Hướng dẫn cấu hình STM32CubeMX và viết code C HAL đọc xung Encoder 2 kênh A, B bằng chế độ Encoder Mode của Timer."
    with col2:
        if st.button("📈 Giải thích ý nghĩa vật lý 3 khâu P, I, D và cách chỉnh thông số", use_container_width=True):
            selected_prompt = "Giải thích trực quan tác dụng của Kp, Ki, Kd lên độ vọt lố, thời gian xác lập và sai số xác lập kèm ví dụ code MATLAB."
        if st.button("🔌 Phân biệt đấu dây ngõ vào PLC kiểu Sink và Source", use_container_width=True):
            selected_prompt = "Phân biệt cách đấu nối cảm biến NPN và PNP vào ngõ vào PLC Mitsubishi/Siemens theo kiểu Sink và Source."

# 7. Hiển thị lịch sử trò chuyện với Avatar đẹp
for msg in st.session_state.messages:
    avatar_icon = "🧑‍💻" if msg["role"] == "user" else "✨"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])

# 8. Nhận câu hỏi từ thanh chat hoặc từ nút bấm gợi ý
chat_input = st.chat_input("Hỏi Gemini Tự Động Hóa (hoặc mở thanh bên trái ❯ để tải ảnh mạch/PDF)...")
prompt = selected_prompt or chat_input

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("Đang phân tích kỹ thuật..."):
            contents = []
            uploaded_gemini_files = []

            if uploaded_files:
                for uf in uploaded_files:
                    suffix = os.path.splitext(uf.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uf.read())
                        tmp_path = tmp.name
                    g_file = client.files.upload(file=tmp_path)
                    uploaded_gemini_files.append(g_file)
                    contents.append(g_file)
                    os.remove(tmp_path)

            history = "\n".join([
                f"{'Người dùng' if m['role'] == 'user' else 'AI'}: {m['content']}"
                for m in st.session_state.messages[-10:]
            ])
            
            system_instruction = (
                f"Bạn là trợ lý AI chuyên ngành Kỹ thuật Tự động hóa (Chế độ: {study_mode}). "
                "Trình bày cực kỳ rõ ràng, dùng công thức LaTeX chuẩn xác, giải thích cặn kẽ nguyên lý phần cứng "
                "và luôn kiểm tra kỹ an toàn điện (ngắn mạch, khóa chéo) khi đọc bản vẽ."
            )
            
            contents.append(f"Lịch sử:\n{history}\n\nCâu hỏi hiện tại: {prompt}")

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
                
                for gf in uploaded_gemini_files:
                    client.files.delete(name=gf.name)
                
                # Nếu người dùng bấm nút gợi ý ở màn hình chờ, tải lại nhẹ để ẩn 4 nút gợi ý đi
                if selected_prompt:
                    st.rerun()
            except Exception as e:
                st.error(f"Lỗi phản hồi: {e}")
