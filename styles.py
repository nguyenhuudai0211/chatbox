import streamlit as st

AI_SVG_AVATAR = """data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="%233a83f7"/><stop offset="50%" stop-color="%239b72cb"/><stop offset="100%" stop-color="%23d96570"/></linearGradient></defs><rect width="100" height="100" rx="50" fill="%23141416"/><path d="M50 12 C54 38 62 46 88 50 C62 54 54 62 50 88 C46 62 38 54 12 50 C38 46 46 38 50 12 Z" fill="url(%23g)"/></svg>"""

USER_SVG_AVATAR = """data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><linearGradient id="u" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="%233a83f7"/><stop offset="100%" stop-color="%23173e76"/></linearGradient></defs><circle cx="50" cy="50" r="50" fill="url(%23u)"/><text x="50" y="62" font-family="Arial, sans-serif" font-size="34" font-weight="bold" fill="%23ffffff" text-anchor="middle">ĐF</text></svg>"""


def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {
            --bg-surface: #0d0d0d;
            --bg-sidebar: #141414;
            --bg-elevated: #1f1f22;
            --text-primary: #ededed;
            --text-secondary: #a1a1aa;
            --accent-blue: #3a83f7;
            --border-subtle: rgba(255, 255, 255, 0.09);
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
            max-width: 880px !important;
            padding-top: 1.2rem !important;
            padding-bottom: 7.5rem !important;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: var(--bg-sidebar) !important;
            border-right: 1px solid var(--border-subtle) !important;
        }
        [data-testid="stSidebar"] .stButton > button {
            border-radius: 10px !important;
            text-align: left !important;
            justify-content: flex-start !important;
            padding: 0.48rem 0.75rem !important;
            background-color: transparent !important;
            border: 1px solid transparent !important;
            color: var(--text-primary) !important;
            font-size: 0.86rem !important;
            transition: all 0.15s ease !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: rgba(255, 255, 255, 0.07) !important;
            border-color: rgba(255, 255, 255, 0.12) !important;
        }

        .new-chat-btn > button {
            background: linear-gradient(135deg, rgba(58,131,247,0.22), rgba(155,114,203,0.22)) !important;
            border: 1px solid rgba(58, 131, 247, 0.45) !important;
            font-weight: 600 !important;
        }

        /* Thanh Top Telemetry Bar (Đặc trưng của Gemini2API Gateway) */
        .gateway-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #161618;
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 8px 16px;
            margin-bottom: 14px;
            font-size: 0.8rem;
        }
        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: #40c977;
            box-shadow: 0 0 8px #40c977;
            margin-right: 6px;
        }
        .telemetry-badge {
            font-family: 'JetBrains Mono', monospace;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 2px 8px;
            border-radius: 6px;
            color: #a8c7fa;
            font-size: 0.75rem;
        }

        /* Hero Banner */
        .hero-wrapper {
            text-align: center;
            padding: 2.2rem 1rem 1.4rem 1rem;
        }
        .hero-title {
            font-size: 2.3rem;
            font-weight: 700;
            background: linear-gradient(90deg, #63a8f8 0%, #c58af9 50%, #ff8983 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.35rem;
        }
        .hero-subtitle {
            font-size: 1rem;
            color: var(--text-secondary);
        }

        /* Bong bóng Chat */
        [data-testid="stChatMessage"] {
            border-radius: 18px !important;
            padding: 1.1rem 1.35rem !important;
            margin-bottom: 0.95rem !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            background-color: rgba(31, 31, 34, 0.6) !important;
        }

        /* Nhãn File và Nhãn Telemetry dưới mỗi câu trả lời */
        .file-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(58, 131, 247, 0.14);
            border: 1px solid rgba(58, 131, 247, 0.38);
            color: #a8c7fa;
            border-radius: 8px;
            padding: 3px 10px;
            margin: 0 6px 8px 0;
            font-size: 0.8rem;
        }
        .msg-meta {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            color: #71717a;
            margin-top: 8px;
            padding-top: 6px;
            border-top: 1px dashed rgba(255, 255, 255, 0.08);
        }

        /* Thẻ gợi ý có mũi tên ↳ */
        div[data-testid="column"] .stButton > button {
            background-color: #1b1b1e !important;
            border: 1px solid rgba(255, 255, 255, 0.09) !important;
            border-radius: 16px !important;
            padding: 0.85rem 1rem !important;
            color: #ededed !important;
            text-align: left !important;
            height: auto !important;
            min-height: 82px !important;
            font-size: 0.85rem !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="column"] .stButton > button:hover {
            background-color: #25262b !important;
            border-color: #3a83f7 !important;
            transform: translateY(-2px) !important;
        }

        /* Footer Profile */
        .profile-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #1b1b1e;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 14px;
            padding: 10px 12px;
            margin-top: 12px;
        }
    </style>
    """, unsafe_allow_html=True)
