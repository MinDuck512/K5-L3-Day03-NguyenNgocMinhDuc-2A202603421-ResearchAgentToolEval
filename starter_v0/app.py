from __future__ import annotations

from pathlib import Path

import streamlit as st

from chat import run_model_tool_loop, trim_history
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

st.set_page_config(page_title="Research Agent UI - Day 03", page_icon="🔎", layout="centered")
st.title("🔎 Research Agent — Interactive UI")
st.caption("Chạy trực tiếp loop tool-calling từ chat.py với artifacts/system_prompt.md và artifacts/tools.yaml.")

system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
tools_path = ARTIFACTS_DIR / "tools.yaml"

with st.sidebar:
    st.header("Cấu hình")
    version_label = st.text_input("Version label", value="v3")
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini", "ollama"])
    model_override = st.text_input("Model override (tùy chọn)", value="")
    max_rounds = st.slider("Max tool rounds", min_value=1, max_value=6, value=4)

    artifact_version = build_artifact_version(version_label or "v3", system_prompt_path, tools_path)
    st.code(artifact_version.artifact_version, language="text")

    tool_declarations = load_tool_declarations(tools_path)
    st.subheader(f"Tools ({len(tool_declarations)})")
    for item in tool_declarations:
        st.markdown(f"- `{item['name']}`")

    if st.button("Xóa hội thoại"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("tool_events"):
            with st.expander(f"Tool calls ({len(msg['tool_events'])})"):
                for ev in msg["tool_events"]:
                    st.markdown(f"**`{ev['tool']}`** args: `{ev['args']}`")
                    st.json(ev["result"])
        st.markdown(msg["content"])

if prompt := st.chat_input("Nhập yêu cầu research (tin tức, tweet, Hacker News, arXiv, policy)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    openai_tools = to_openai_tools(load_tool_declarations(tools_path))
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(history, 5),
        {"role": "user", "content": prompt},
    ]

    with st.chat_message("assistant"):
        with st.spinner(f"Đang gọi {provider_name}..."):
            try:
                provider = make_provider(provider_name)
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=model_override.strip() or None,
                    max_tool_rounds=max_rounds,
                )
                tool_events = result.get("tool_events", [])
                if tool_events:
                    with st.expander(f"Tool calls ({len(tool_events)})"):
                        for ev in tool_events:
                            st.markdown(f"**`{ev['tool']}`** args: `{ev['args']}`")
                            st.json(ev["result"])
                reply = result.get("assistant_text") or ""
                st.markdown(reply)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply,
                    "tool_events": tool_events,
                })
            except Exception as exc:
                err_msg = f"Lỗi provider `{provider_name}`: `{type(exc).__name__}: {exc}`"
                st.error(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})
