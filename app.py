import time
import streamlit as st
from google.genai import types

from styles import inject_custom_css, AI_SVG_AVATAR, USER_SVG_AVATAR
from storage import (
    init_session_storage,
    save_database,
    create_new_thread,
    switch_thread,
    delete_thread,
    process_and_save_uploads
)
from ai_engine import (
    REASONING_TIERS,
    DOMAIN_MODES,
    get_active_client,
    rotate_next_key,
    sync_thread_files_to_gemini,
    build_system_instruction
)

# 1. Khởi tạo cấu hình trang, CSS & Database
st.set_page_config(
    page_title="Đại Foolish AI — Studio",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)
inject_custom_css()
init_session_storage()

db = st.session_state.db
current_id = db["current_thread_id"]
current_thread = db["threads"][current_id]
client, masked_key, total_keys, active_key_num = get_active_client()

# ==============================================================================
# 2. SIDEBAR: LỊCH SỬ ĐOẠN CHAT & TRẠM QUẢN LÝ KEY (GEMINI2API VIBE)
# ==============================================================================
with st.sidebar:
    st.markdown("### ✦ **Đại Foolish Studio**")

    st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
    if st.button("➕  Cuộc trò chuyện mới", use_container_width=True):
        create_new_thread()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    st.caption("💬 LỊCH SỬ CÁC ĐOẠN CHAT")

    # Hiển thị danh sách đoạn chat (Đã fix triệt để lỗi xem lại chat cũ)
    for tid in list(db["threads"].keys())[::-1]:
        t_info = db["threads"][tid]
        is_current = (tid == current_id)
        icon = "🟦" if is_current else "💭"

        col_nav, col_del = st.columns([0.82, 0.18])
        with col_nav:
            if st.button(f"{icon} {t_info['title'][:22]}", key=f"thread_btn_{tid}", use_container_width=True):
                switch_thread(tid)
                st.rerun()
        with col_del:
            if len(db["threads"]) > 1:
                if st.button("✕", key=f"del_btn_{tid}", help="Xóa đoạn chat này"):
                    delete_thread(tid)
                    st.rerun()

    st.divider()
    files_list = current_thread.get("files", [])
    st.caption(f"📚 KHO TÀI LIỆU ĐÃ LƯU ({len(files_list)})")
    if files_list:
        for f_meta in files_list:
            st.markdown(f"<div class='file-chip'>📄 {f_meta['display_name']}</div>", unsafe_allow_html=True)
    else:
        st.caption("Chưa có file. Bấm dấu ➕ ở ô chat để nạp PDF, Ảnh hoặc .ZIP!")

    if total_keys > 1:
        if st.button(f"🔄 Đổi API Key ({active_key_num}/{total_keys})", use_container_width=True):
            rotate_next_key()
            st.rerun()

    st.markdown(f"""
    <div class="profile-footer">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #3a83f7, #924ff7); display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.8rem; color: white;">ĐF</div>
            <div>
                <div style="font-size: 0.88rem; font-weight: 600;">Đại Foolish</div>
                <div style="font-size: 0.7rem; color: #9ba1a6;">Key {active_key_num}/{total_keys} ({masked_key})</div>
            </div>
        </div>
        <div style="background: rgba(64,201,119,0.15); color: #40c977; font-size: 0.68rem; padding: 2px 8px; border-radius: 99px; font-weight: 600;">ONLINE</div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. THANH TRẠNG THÁI API GATEWAY & BỘ CHỌN SUY LUẬN NGAY TRÊN KHUNG CHAT
# ==============================================================================
st.markdown(f"""
<div class="gateway-bar">
    <div><span class="status-dot"></span><b>Gemini2API Gateway:</b> Connected</div>
    <div style="display: flex; gap: 8px;">
        <span class="telemetry-badge">Key Pool: {active_key_num}/{total_keys}</span>
        <span class="telemetry-badge">Total Queries: {db.get('total_requests', 0)}</span>
        <span class="telemetry-badge">Vault Files: {len(files_list)}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Đặt bộ chọn Chuyên môn & Cấp độ suy luận ngay ngoài màn hình chính
c_reasoning, c_domain = st.columns([1.15, 1])
with c_reasoning:
    selected_reasoning = st.selectbox(
        "🧠 Cấp độ suy luận:",
        list(REASONING_TIERS.keys()),
        index=1,
        label_visibility="collapsed"
    )
with c_domain:
    selected_domain = st.selectbox(
        "🎯 Lĩnh vực:",
        list(DOMAIN_MODES.keys()),
        index=0,
        label_visibility="collapsed"
    )

# ==============================================================================
# 4. MÀN HÌNH CHỜ (ZERO-STATE) KHI ĐOẠN CHAT CHƯA CÓ TIN NHẮN
# ==============================================================================
if len(current_thread["messages"]) == 0:
    st.markdown("""
    <div class="hero-wrapper">
        <div class="hero-title">Chào Đại Foolish, tôi có thể giúp gì cho bạn?</div>
        <div class="hero-subtitle">Chọn cấp độ suy luận phía trên, nạp tài liệu hoặc bấm thẻ gợi ý để bắt đầu</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 Giải bài tập Thống kê (Slide 27)\n\nTính trung bình mẫu x̄ và phương sai s²\n\n↳", use_container_width=True):
            st.session_state.queued_prompt = (
                "Giải chi tiết từng bước bài tập ở Slide 27 (Engineering Probability & Statistics Chapter 1): "
                "Tìm trung bình mẫu (Sample Mean) và phương sai mẫu (Sample Variance) của dãy 11 số: "
                "21, 12, 34, 22, 17, 18, 43, 28, 56, 34, 12."
            )
            st.rerun()
    with col2:
        if st.button("⚡ Soát lỗi mạch PLC & Contactor\n\nKiểm tra khóa chéo & ngắn mạch 3 pha\n\n↳", use_container_width=True):
            st.session_state.queued_prompt = (
                "Phân tích nguyên lý đấu dây PLC (220VAC) điều khiển Contactor thông qua Rơ-le trung gian 24VDC "
                "và cách kiểm tra khóa chéo chống ngắn mạch 3 pha."
            )
            st.rerun()
    with col3:
        if st.button("🌐 Hỏi đáp & Lập trình Đa năng\n\nViết code Python, Web, STM32 hoặc dịch thuật\n\n↳", use_container_width=True):
            st.session_state.queued_prompt = (
                "Hãy gợi ý cho mình các mẹo tối ưu hóa code Python và cấu trúc dự án phần mềm chuyên nghiệp."
            )
            st.rerun()

# ==============================================================================
# 5. HIỂN THỊ LỊCH SỬ TIN NHẮN TRONG ĐOẠN CHAT HIỆN TẠI
# ==============================================================================
for m_idx, msg in enumerate(current_thread["messages"]):
    avatar_img = USER_SVG_AVATAR if msg["role"] == "user" else AI_SVG_AVATAR
    with st.chat_message(msg["role"], avatar=avatar_img):
        if msg.get("attached_names"):
            chips = "".join([f'<span class="file-chip">📄 {name}</span>' for name in msg["attached_names"]])
            st.markdown(chips, unsafe_allow_html=True)

        if msg.get("thought_steps"):
            with st.expander(f"🧠 Tiến trình suy luận ({msg.get('tier_badge', 'CORE-PRO')})", expanded=False):
                for step in msg["thought_steps"]:
                    st.markdown(f"- {step}")

        st.markdown(msg["content"])

        if msg.get("telemetry"):
            st.markdown(f"<div class='msg-meta'>{msg['telemetry']}</div>", unsafe_allow_html=True)

        # 3 Thẻ gợi ý tiếp theo (Follow-up Cards) ở tin nhắn cuối cùng
        if msg["role"] == "assistant" and m_idx == len(current_thread["messages"]) - 1:
            followups = msg.get("followups", [])
            if followups:
                st.markdown("<div style='font-size: 0.86rem; color: #a1a1aa; margin: 0.9rem 0 0.4rem 0;'>💡 Gợi ý tiếp theo:</div>", unsafe_allow_html=True)
                f_cols = st.columns(len(followups))
                for f_i, f_item in enumerate(followups):
                    with f_cols[f_i]:
                        if st.button(f"{f_item['title']}\n\n↳", key=f"fu_{current_id}_{m_idx}_{f_i}", use_container_width=True):
                            st.session_state.queued_prompt = f_item["prompt"]
                            st.rerun()

# ==============================================================================
# 6. Ô NHẬP LIỆU NGẮN GỌN & XỬ LÝ STREAMING + ĐO ĐẠC TELEMETRY
# ==============================================================================
chat_submission = st.chat_input(
    "Tôi có thể giúp gì cho bạn?",
    accept_file="multiple",
    file_type=["pdf", "png", "jpg", "jpeg", "txt", "zip"]
)

active_prompt = None
newly_uploaded = []

if st.session_state.queued_prompt:
    active_prompt = st.session_state.queued_prompt
    st.session_state.queued_prompt = None
elif chat_submission:
    active_prompt = chat_submission.text or "Hãy phân tích và tóm tắt tài liệu đính kèm."
    newly_uploaded = chat_submission.files

if active_prompt:
    start_time = time.time()
    attached_names = []

    if newly_uploaded:
        with st.spinner("Đang lưu tài liệu vào Kho lưu trữ vĩnh viễn..."):
            attached_names = process_and_save_uploads(newly_uploaded, client, current_id, current_thread)

    # Tự động cập nhật tiêu đề đoạn chat ở cột trái dựa vào câu hỏi đầu tiên
    if len(current_thread["messages"]) == 0:
        clean_title = active_prompt.replace("\n", " ").strip()
        current_thread["title"] = clean_title[:26] + ("..." if len(clean_title) > 26 else "")

    current_thread["messages"].append({
        "role": "user",
        "content": active_prompt,
        "attached_names": attached_names
    })
    db["total_requests"] = db.get("total_requests", 0) + 1
    save_database(db)

    with st.chat_message("user", avatar=USER_SVG_AVATAR):
        if attached_names:
            chips = "".join([f'<span class="file-chip">📄 {name}</span>' for name in attached_names])
            st.markdown(chips, unsafe_allow_html=True)
        st.markdown(active_prompt)

    tier_cfg = REASONING_TIERS[selected_reasoning]

    with st.chat_message("assistant", avatar=AI_SVG_AVATAR):
        thought_log = []
        with st.status(f"🧠 **Đang suy luận ({tier_cfg['badge']})**", expanded=True) as status_box:
            s1 = f"⚙️ Kích hoạt cấu hình: **{selected_reasoning}** (`Temp = {tier_cfg['temp']}`)"
            st.write(s1)
            thought_log.append(s1)

            s2 = f"🎯 Lĩnh vực định tuyến: **{selected_domain}**"
            st.write(s2)
            thought_log.append(s2)

            active_gemini_files = sync_thread_files_to_gemini(current_thread, client)
            if active_gemini_files:
                s3 = f"📚 Đã nạp **{len(active_gemini_files)} tài liệu** từ Vault vào bộ nhớ ngữ cảnh."
                st.write(s3)
                thought_log.append(s3)

            contents = list(active_gemini_files)
            history_str = "\n".join([
                f"{'Đại Foolish' if m['role'] == 'user' else 'AI'}: {m['content']}"
                for m in current_thread["messages"][-12:]
            ])
            contents.append(f"Lịch sử trò chuyện:\n{history_str}\n\nCâu hỏi hiện tại: {active_prompt}")

            sys_instruct = build_system_instruction(selected_domain, selected_reasoning)
            status_box.update(label=f"✦ **Hoàn tất suy luận ({tier_cfg['badge']})**", state="complete", expanded=False)

        response_placeholder = st.empty()
        full_reply = ""

        try:
            stream_resp = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruct,
                    temperature=tier_cfg["temp"],
                )
            )
            for chunk in stream_resp:
                if chunk.text:
                    full_reply += chunk.text
                    response_placeholder.markdown(full_reply + " ▍")
            response_placeholder.markdown(full_reply)

            elapsed_sec = round(time.time() - start_time, 2)
            est_tokens = max(1, len(full_reply) // 4)
            telemetry_str = f"⚡ {tier_cfg['badge']}  |  ⏱️ Latency: {elapsed_sec}s  |  🪙 ~{est_tokens} tokens  |  🔑 Key #{active_key_num}"

            followups = [
                {
                    "title": "Giải thích sâu hơn bằng ví dụ thực tế",
                    "prompt": "Hãy lấy một ví dụ thực tế hoặc bài tập cụ thể để minh họa rõ hơn cho phần vừa trả lời."
                },
                {
                    "title": "Viết code / Công thức thực thi",
                    "prompt": "Hãy cung cấp đoạn code hoặc bảng tổng hợp công thức hoàn chỉnh cho nội dung trên."
                },
                {
                    "title": "Kiểm tra các lỗi sai thường gặp",
                    "prompt": "Khi áp dụng kiến thức hoặc đoạn code này vào thực tế thì cần lưu ý những bẫy hoặc lỗi sai nào?"
                }
            ]

            current_thread["messages"].append({
                "role": "assistant",
                "content": full_reply,
                "thought_steps": thought_log,
                "tier_badge": tier_cfg["badge"],
                "telemetry": telemetry_str,
                "followups": followups
            })
            save_database(db)
            st.rerun()

        except Exception as e:
            rotate_next_key()
            st.error(f"⚠️ Lỗi phản hồi từ API (Hệ thống đã tự động chuyển sang Key dự phòng cho lượt sau): {e}")
