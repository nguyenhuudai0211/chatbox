import os
import streamlit as st
from google import genai
from google.genai import types

# 3 Cấp độ suy luận đặt tên riêng biệt
REASONING_TIERS = {
    "⚡ Flash-Lite (Thấp — Phản hồi tức thì)": {
        "temp": 0.1,
        "badge": "FLASH-LITE • TỐC ĐỘ CAO",
        "directive": (
            "Trả lời cực kỳ ngắn gọn, đi thẳng vào kết quả, code hoặc công thức chính. "
            "Không giải thích rườm rà."
        )
    },
    "⚖️ Core-Pro (Trung bình — Chuẩn xác cao)": {
        "temp": 0.25,
        "badge": "CORE-PRO • CHUẨN KỸ THUẬT",
        "directive": (
            "Giải thích rõ ràng từng bước, lập bảng so sánh trực quan, kiểm tra kỹ các thông số "
            "và đảm bảo độ chính xác cao nhất."
        )
    },
    "🧠 Deep-Ultra (Cao — Siêu suy luận đa tầng)": {
        "temp": 0.6,
        "badge": "DEEP-ULTRA • SUY LUẬN SÂU",
        "directive": (
            "Phân tích chuyên sâu như một Giáo sư và Kỹ sư trưởng. Trước khi đưa ra kết luận, "
            "hãy phân tích bản chất vật lý/toán học, kiểm tra các trường hợp biên, cảnh báo bẫy sai số "
            "hoặc nguy cơ mất an toàn điện, sau đó trình bày giải pháp toàn diện nhất."
        )
    }
}

DOMAIN_MODES = {
    "🌐 Đa năng (Hỏi mọi chủ đề)": "Bạn là trợ lý AI toàn năng, am hiểu sâu rộng mọi lĩnh vực từ đời sống, lập trình đến học thuật.",
    "⚙️ Kỹ thuật Tự động hóa & PLC": "Bạn là chuyên gia PLC (Mitsubishi/Siemens), mạch động lực Contactor/Rơ-le 24VDC-220VAC và truyền động điện.",
    "🎛️ Vi điều khiển & Robotics (STM32/ESP32/ROS2)": "Bạn là kỹ sư hệ thống nhúng chuyên STM32 HAL, ESP32, giao tiếp CAN/UART/I2C và ROS2.",
    "📊 Xác suất Thống kê & Toán Kỹ thuật": "Bạn là giảng viên Toán ứng dụng, Xác suất thống kê và Lý thuyết điều khiển tự động (MATLAB)."
}


def get_api_keys_pool():
    """Hỗ trợ đọc 1 key hoặc nhiều key (cách nhau bằng dấu phẩy) từ Streamlit Secrets."""
    raw_keys = st.secrets.get("GEMINI_API_KEY", "")
    if not raw_keys:
        return []
    return [k.strip() for k in raw_keys.split(",") if k.strip()]


def get_active_client():
    keys = get_api_keys_pool()
    if not keys:
        st.error("⚠️ Chưa cấu hình `GEMINI_API_KEY` trong Streamlit Secrets.")
        st.stop()
    idx = st.session_state.get("key_index", 0) % len(keys)
    active_key = keys[idx]
    masked_key = f"...{active_key[-6:]}" if len(active_key) > 8 else "Active"
    return genai.Client(api_key=active_key), masked_key, len(keys), idx + 1


def rotate_next_key():
    keys = get_api_keys_pool()
    if len(keys) > 1:
        st.session_state.key_index = (st.session_state.get("key_index", 0) + 1) % len(keys)


def sync_thread_files_to_gemini(thread_obj, client):
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


def build_system_instruction(domain_key, reasoning_key):
    domain_prompt = DOMAIN_MODES.get(domain_key, DOMAIN_MODES["🌐 Đa năng (Hỏi mọi chủ đề)"])
    tier_info = REASONING_TIERS.get(reasoning_key, REASONING_TIERS["⚖️ Core-Pro (Trung bình — Chuẩn xác cao)"])

    return (
        f"{domain_prompt}\n"
        f"Người dùng tên là Đại Foolish. Hãy xưng hô thân thiện, tự nhiên.\n"
        f"CHỈ THỊ SUY LUẬN: {tier_info['directive']}\n"
        "QUY TẮC CÔNG THỨC TOÁN HỌC: Chỉ viết mỗi công thức đúng 1 lần duy nhất trong cặp dấu $...$ hoặc $$...$$. "
        "Tuyệt đối không viết lặp lại công thức bằng chữ thường bên cạnh LaTeX."
    )
