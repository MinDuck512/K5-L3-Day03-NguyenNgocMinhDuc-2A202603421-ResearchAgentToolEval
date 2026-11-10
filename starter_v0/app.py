"""Streamlit Web UI for Research Agent (Day 03 Lab).
Allows interactive live testing, visualizing tool calls, and inspecting results.
"""
from __future__ import annotations

import json
from pathlib import Path
import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from chat import run_model_tool_loop, trim_history

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

st.set_page_config(
    page_title="Research Agent UI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown(
    """
    <style>
    .tool-badge {
        background-color: #2b313e;
        color: #00e676;
        padding: 4px 10px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 0.9em;
        margin-right: 6px;
    }
    .stChatMessage {
        border-radius: 10px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Load artifacts
system_prompt_text = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
tool_declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
openai_tools = to_openai_tools(tool_declarations)

# Sidebar
with st.sidebar:
    st.title("🤖 Research Agent")
    st.caption("AI20k Lab — Evidence-Driven Tool Agent")
    st.markdown("---")

    provider_name = st.selectbox(
        "Provider",
        options=["openrouter", "openai", "gemini", "ollama"],
        index=0,
    )
    model_name = st.text_input("Model (để trống nếu dùng mặc định)", value="")

    st.markdown("### 🛠️ Danh sách Tools")
    for tool in tool_declarations:
        badge = "✨ MỚI" if tool["name"] == "calculator" else "⚙️ Core"
        with st.expander(f"{tool['name']} ({badge})"):
            st.write(tool.get("description", ""))

    st.markdown("---")
    st.markdown("### 💡 Câu hỏi mẫu")
    sample_queries = [
        "Tweet mới nhất của Sam Altman là gì?",
        "Tin tức AI hôm nay có gì nổi bật?",
        "Doanh thu quý này đạt 150 tỷ, quý trước là 120 tỷ. Hãy tính tỷ lệ phần trăm tăng trưởng giúp mình.",
        "Mọi người đang bàn gì về GPT-5 trên Twitter?",
        "Tóm tắt bài viết này giúp mình: https://openai.com/research/",
    ]
    for q in sample_queries:
        if st.button(f"👉 {q[:35]}...", key=q, help=q):
            st.session_state["user_input_preset"] = q

    if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
        st.session_state["messages"] = []
        st.session_state["agent_history"] = []
        st.rerun()

# State initialization
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "agent_history" not in st.session_state:
    st.session_state["agent_history"] = []

# Main UI
st.header("Research Agent Live Demo")
st.write("Hỏi đáp thông minh, tự động định tuyến và kích hoạt các công cụ tra cứu thông tin thực tế.")

# Render chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        if "tool_events" in msg and msg["tool_events"]:
            for event in msg["tool_events"]:
                with st.status(f"🔧 Đã gọi tool: `{event['tool']}`", expanded=False):
                    st.write("**Tham số (Arguments):**")
                    st.json(event.get("args", {}))
                    st.write("**Kết quả (Result):**")
                    st.json(event.get("result", {}))
        st.markdown(msg["content"])

# Chat input
preset = st.session_state.pop("user_input_preset", None)
user_prompt = st.chat_input("Nhập câu hỏi hoặc yêu cầu nghiên cứu...") or preset

if user_prompt:
    # Display user message
    st.session_state["messages"].append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Initialize provider
    try:
        provider = make_provider(provider_name)
    except Exception as exc:
        st.error(f"Lỗi khởi tạo provider: {exc}")
        st.stop()

    # Build prompt messages
    model_arg = model_name.strip() or None
    trimmed = trim_history(st.session_state["agent_history"], window=4)
    model_messages = [
        {"role": "system", "content": system_prompt_text},
        *trimmed,
        {"role": "user", "content": user_prompt},
    ]

    with st.chat_message("assistant"):
        with st.spinner("Agent đang suy nghĩ và thực thi tools..."):
            result = run_model_tool_loop(
                provider=provider,
                messages=model_messages,
                tools=openai_tools,
                model=model_arg,
                max_tool_rounds=4,
            )

        # Show executed tools
        tool_events = result.get("tool_events", [])
        if tool_events:
            for event in tool_events:
                with st.status(f"🔧 Đã gọi tool: `{event['tool']}`", expanded=True):
                    st.write("**Tham số (Arguments):**")
                    st.json(event.get("args", {}))
                    st.write("**Kết quả (Result):**")
                    st.json(event.get("result", {}))

        assistant_text = result.get("assistant_text", "")
        st.markdown(assistant_text)

        # Save to chat history
        st.session_state["messages"].append({
            "role": "assistant",
            "content": assistant_text,
            "tool_events": tool_events,
        })
        st.session_state["agent_history"].append({"role": "user", "content": user_prompt})
        st.session_state["agent_history"].append({"role": "assistant", "content": assistant_text})

