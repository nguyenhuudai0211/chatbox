import streamlit as st
from google import genai
from google.genai import types
import os
import tempfile

# 1. Cấu hình giao diện
st.set_page_config(page_title="AI Tự Động Hóa UEH", page_icon="⚙️", layout="wide")
st.title("🤖 Trợ Lý AI: Tự Động Hóa & Nhúng")

# 2. Lấy API Key từ Secrets của Streamlit
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=API_KEY)
except Exception:
    st.error("⚠️ Lỗi: Chưa cấu hình GEMINI_API_KEY trong Streamlit Secrets. Vui lòng thêm vào phần Advanced Settings trên Streamlit Cloud.")
    st.stop()

# 3. Khởi tạo bộ nhớ chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. Cột công cụ bên trái (Sidebar)
with st.sidebar:
    st.header("📂 Nạp tài liệu (RAG)")
    st.caption("Tải lên Datasheet (PDF) hoặc ảnh mạch điện (PNG/JPG).")
    uploaded_files = st.file_uploader("Chọn file", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True)
    
    st.divider()
    if st.button("🗑️ Xóa lịch sử trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 5. Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 6. Xử lý câu hỏi mới
if prompt := st.chat_input("Nhập câu hỏi (Ví dụ: Viết code STM32 đếm nút nhấn, tra lỗi PLC...):"):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Đang phân tích dữ liệu kỹ thuật..."):
            contents = []
            uploaded_gemini_files = []

            # Xử lý file đính kèm
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

            # Đưa lịch sử 10 tin nhắn gần nhất vào để AI nhớ ngữ cảnh
            history = "\n".join([f"{'Người dùng' if m['role'] == 'user' else 'AI'}: {m['content']}" for m in st.session_state.messages[-10:]])
            
            # System Prompt định hình tư duy kỹ sư
            system_instruction = (
                "Bạn là một kỹ sư hệ thống nhúng và tự động hóa. Khi hướng dẫn viết code C/C++ (STM32, ESP32) hoặc lập trình PLC, "
                "hãy giải thích rõ logic. Nếu phân tích mạch điện (như Contactor, Rơ-le 24VDC/220VAC), luôn kiểm tra nguy cơ ngắn mạch 3 pha và khóa chéo."
            )
            
            full_prompt = f"Lịch sử trò chuyện:\n{history}\n\nYêu cầu mới: {prompt}"
            contents.append(full_prompt)

            # Gọi Gemini API
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2, # Giữ mức thấp để bám sát thông số kỹ thuật
                    )
                )
                
                reply = response.text
                st.markdown(reply)
                
                st.session_state.messages.append({"role": "assistant", "content": reply})
                
                # Dọn dẹp file trên cloud
                for gf in uploaded_gemini_files:
                    client.files.delete(name=gf.name)
                    
            except Exception as e:
                st.error(f"Lỗi hệ thống: {e}")
