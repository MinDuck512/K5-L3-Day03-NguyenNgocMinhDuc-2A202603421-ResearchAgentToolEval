"""Deep Research Agent - Streamlit Interactive UI & Evaluation Workbench."""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from agent import ResearchAgent
from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import build_artifact_version

ROOT = Path(__file__).resolve().parent
load_lab_env(ROOT)
ARTIFACTS_DIR = ROOT / "artifacts"
RUNS_DIR = ROOT / "runs"
TRANSCRIPTS_DIR = ROOT / "transcripts"
DATA_DIR = ROOT / "data"

st.set_page_config(
    page_title="Deep Research Agent Workbench",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
        color: #1E3A8A;
    }
    .sub-title {
        color: #4B5563;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .tool-call-box {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    </style>
""",
    unsafe_allow_html=True,
)


def load_version_artifacts(version_tag: str) -> tuple[str, list[dict[str, Any]], Path, Path]:
    prompt_file = ARTIFACTS_DIR / f"system_prompt_{version_tag}.md"
    if not prompt_file.exists():
        prompt_file = ARTIFACTS_DIR / "system_prompt.md"

    tools_file = ARTIFACTS_DIR / f"tools_{version_tag}.yaml"
    if not tools_file.exists():
        tools_file = ARTIFACTS_DIR / "tools.yaml"

    prompt_text = prompt_file.read_text(encoding="utf-8")
    declarations = load_tool_declarations(tools_file)
    return prompt_text, declarations, prompt_file, tools_file


def save_transcript(messages: list[dict[str, Any]], version_tag: str, provider_name: str) -> Path:
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    filename = f"{version_tag}_{provider_name}_{timestamp}.transcript.json"
    target = TRANSCRIPTS_DIR / filename
    payload = {
        "timestamp": datetime.now().isoformat(),
        "version": version_tag,
        "provider": provider_name,
        "turns": messages,
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return target


# --- Sidebar ---
st.sidebar.markdown("## ⚙️ Configuration")

version_options = ["v6", "v5", "v4", "v3", "v2", "v1", "v0"]
selected_version = st.sidebar.selectbox(
    "Agent Version",
    options=version_options,
    index=0,
    help="Select the optimization iteration of the research agent.",
)

provider_options = ["openai", "gemini", "openrouter", "ollama"]
selected_provider = st.sidebar.selectbox(
    "Provider",
    options=provider_options,
    index=0,
)

model_override = st.sidebar.text_input(
    "Model (optional)",
    value="gpt-4o-mini" if selected_provider == "openai" else "",
    placeholder="Leave blank for provider default",
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 API Key Status")
env_status = {
    "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
    "TAVILY_API_KEY": bool(os.getenv("TAVILY_API_KEY")),
    "FIRECRAWL_API_KEY": bool(os.getenv("FIRECRAWL_API_KEY")),
    "RAPIDAPI_KEY": bool(os.getenv("RAPIDAPI_KEY")),
    "TELEGRAM_BOT_TOKEN": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
}
for k, v in env_status.items():
    icon = "✅" if v else "⚠️"
    st.sidebar.markdown(f"{icon} `{k}`")

st.sidebar.markdown("---")
if st.sidebar.button("🧹 Clear Chat History", use_container_width=True):
    st.session_state["messages"] = []
    st.session_state["awaiting_confirmation"] = None
    st.rerun()

# --- Main App ---
st.markdown('<div class="main-title">🔬 Deep Research Agent Workbench</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Interactive Pair Research Agent, Multi-Version Tool Evaluation, and Evidence Dashboard</div>', unsafe_allow_html=True)

tabs = st.tabs(["💬 Live Research Agent", "📊 Evaluation Dashboard", "🛠️ Tool Playground", "📜 Prompt & Declarations"])

# TAB 1: Live Chat
with tabs[0]:
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "awaiting_confirmation" not in st.session_state:
        st.session_state["awaiting_confirmation"] = None

    prompt_text, declarations, prompt_p, tools_p = load_version_artifacts(selected_version)
    openai_tools = to_openai_tools(declarations)
    art_ver = build_artifact_version(selected_version, prompt_p, tools_p)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption(f"Active Artifact: `{art_ver.artifact_version}` | Registered Tools: `{len(declarations)}`")
    with col2:
        st.caption(f"Provider: `{selected_provider}`")
    with col3:
        if st.session_state["messages"]:
            if st.button("💾 Save Transcript", use_container_width=True):
                path = save_transcript(st.session_state["messages"], selected_version, selected_provider)
                st.success(f"Saved: {path.name}")

    # Example prompts buttons
    st.markdown("**Quick test prompts:**")
    eq1, eq2, eq3, eq4 = st.columns(4)
    preset_query = None
    if eq1.button("Sam Altman latest tweet"):
        preset_query = "Tweet mới nhất của Sam Altman là gì?"
    if eq2.button("AI News Today (lookup)"):
        preset_query = "Tin tức AI hôm nay có gì nổi bật?"
    if eq3.button("Company Source Policy"):
        preset_query = "Theo company policy, tweet viral có được coi là fact đã xác nhận không?"
    if eq4.button("Calculate Stats Ratio"):
        preset_query = "Tính giúp mình tốc độ tăng trưởng doanh thu theo biểu thức: (350 - 280) / 280 * 100"

    # Display chat history
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            if msg.get("tool_calls"):
                for call in msg["tool_calls"]:
                    with st.expander(f"⚙️ Tool Call: `{call['name']}`", expanded=False):
                        st.json(call.get("args", {}))
            if msg.get("tool_results"):
                for res in msg["tool_results"]:
                    with st.expander(f"📦 Result: `{res.get('tool', 'tool')}`", expanded=False):
                        st.json(res)
            st.markdown(msg.get("content") or "")

    # Pending Confirmation Banner
    if st.session_state["awaiting_confirmation"]:
        conf_action = st.session_state["awaiting_confirmation"]
        st.warning(f"⚠️ Action requires user confirmation before proceeding: `{conf_action.get('summary')}`")
        c1, c2 = st.columns(2)
        if c1.button("✅ Confirm & Execute", type="primary", use_container_width=True):
            user_input = "Tôi đã rà soát nội dung kỹ rồi, xác nhận gửi đi ngay"
            st.session_state["awaiting_confirmation"] = None
            st.session_state["messages"].append({"role": "user", "content": user_input})
            st.rerun()
        if c2.button("❌ Cancel / Reject", use_container_width=True):
            user_input = "Hủy bỏ, không gửi nữa"
            st.session_state["awaiting_confirmation"] = None
            st.session_state["messages"].append({"role": "user", "content": user_input})
            st.rerun()

    # Chat input
    user_prompt = st.chat_input("Hỏi agent điều tra, tóm tắt, tìm kiếm thông tin hoặc tra cứu policy...")
    if preset_query and not user_prompt:
        user_prompt = preset_query

    if user_prompt:
        st.session_state["messages"].append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Agent execution
        with st.chat_message("assistant"):
            with st.spinner("Agent is reasoning and selecting tools..."):
                try:
                    provider = make_provider(selected_provider)
                    agent = ResearchAgent(
                        provider=provider,
                        system_prompt=prompt_text,
                        tools=openai_tools,
                        model=model_override if model_override.strip() else None,
                    )

                    # Build conversation turns format
                    turns = [
                        {"role": m["role"], "content": m.get("content", "")}
                        for m in st.session_state["messages"]
                    ]
                    run_result = agent.run(turns, tool_choice="auto")

                    # Display tool calls
                    tool_calls_data = []
                    if run_result.tool_calls:
                        for call in run_result.tool_calls:
                            tool_calls_data.append({"name": call.name, "args": call.args})
                            with st.expander(f"⚙️ Tool Call: `{call.name}`", expanded=True):
                                st.json(call.args)

                    # Display tool execution outputs
                    if run_result.tool_results:
                        for res in run_result.tool_results:
                            with st.expander(f"📦 Tool Result: `{res.get('tool', 'output')}`", expanded=False):
                                st.json(res)

                    # If clarify requested confirmation, update pending state
                    for call in run_result.tool_calls:
                        if call.name == "clarify" and call.args.get("response_type") == "yes_no":
                            st.session_state["awaiting_confirmation"] = {
                                "summary": call.args.get("question", "Confirmation required"),
                            }

                    # Final assistant message
                    reply_text = run_result.text or ""
                    if not reply_text and run_result.tool_calls:
                        tool_names = ", ".join([f"`{c.name}`" for c in run_result.tool_calls])
                        reply_text = f"Đã thực hiện xong các công cụ: {tool_names}."
                    st.markdown(reply_text)

                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": reply_text,
                        "tool_calls": tool_calls_data,
                        "tool_results": run_result.tool_results,
                    })

                except Exception as exc:
                    st.error(f"Execution Error: {exc}")

# TAB 2: Evaluation Dashboard
with tabs[1]:
    st.subheader("📈 Evaluation Runs & Benchmark Metrics")

    run_files = sorted(list(RUNS_DIR.glob("*.json")), reverse=True)
    if not run_files:
        st.info("No eval run files found in runs/. Run `python run_eval.py` to generate eval evidence.")
    else:
        # Load run summaries
        run_summaries = []
        for rf in run_files:
            try:
                content = json.loads(rf.read_text(encoding="utf-8"))
                summary = content.get("summary", {})
                run_summaries.append({
                    "Run File": rf.name,
                    "Version": content.get("version", ""),
                    "Suite": content.get("suite", ""),
                    "Provider": content.get("provider", ""),
                    "Total": summary.get("total_cases", 0),
                    "Passed": summary.get("passed_cases", 0),
                    "Accuracy": f"{summary.get('case_accuracy', 0.0) * 100:.1f}%",
                    "Routing": f"{summary.get('tool_routing_accuracy', 0.0) * 100:.1f}%",
                    "Arg Match": f"{summary.get('argument_accuracy', 0.0) * 100:.1f}%",
                    "Multi-Turn": f"{summary.get('multiturn_accuracy', 0.0) * 100:.1f}%",
                    "Timestamp": content.get("generated_at", ""),
                })
            except Exception:
                continue

        st.dataframe(run_summaries, use_container_width=True)

        # Inspect selected run
        st.markdown("### 🔍 Detailed Run Inspector")
        inspect_file = st.selectbox("Select Run File to Inspect", options=[rf.name for rf in run_files])
        if inspect_file:
            rf_path = RUNS_DIR / inspect_file
            run_data = json.loads(rf_path.read_text(encoding="utf-8"))
            sum_data = run_data.get("summary", {})

            # Metric metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Case Accuracy", f"{sum_data.get('case_accuracy', 0.0)*100:.1f}%", f"{sum_data.get('passed_cases',0)}/{sum_data.get('total_cases',0)}")
            m2.metric("Tool Routing", f"{sum_data.get('tool_routing_accuracy', 0.0)*100:.1f}%")
            m3.metric("Arg Accuracy", f"{sum_data.get('argument_accuracy', 0.0)*100:.1f}%")
            m4.metric("Multi-Turn Acc", f"{sum_data.get('multiturn_accuracy', 0.0)*100:.1f}%")

            # Filter results
            results = run_data.get("results", [])
            show_only_fails = st.checkbox("Show only FAIL cases", value=False)
            filtered = [r for r in results if not r["result"]["passed"]] if show_only_fails else results

            for item in filtered:
                is_passed = item["result"]["passed"]
                badge = "🟢 PASS" if is_passed else "🔴 FAIL"
                cid = item["id"]
                with st.expander(f"{badge} | **{cid}** - {item.get('metadata', {}).get('what_it_tests', '')}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**User Query / Turns:**")
                        st.json(item.get("input"))
                        st.markdown("**Expected:**")
                        st.json(item.get("expect"))
                    with c2:
                        st.markdown("**Actual Tool Calls:**")
                        st.json(item["result"].get("actual_tool_calls"))
                        st.markdown("**Failures / Observed Mismatch:**")
                        st.write(item["result"].get("failures"))
                        st.write(item["result"].get("observed_mismatch"))

# TAB 3: Tool Playground
with tabs[2]:
    st.subheader("🛠️ Direct Tool Execution Sandbox")
    st.caption("Test individual tools directly without sending prompts to an LLM.")

    all_tool_names = list(TOOL_FUNCTIONS.keys())
    chosen_tool = st.selectbox("Choose Tool to Test", options=all_tool_names)

    if chosen_tool == "calculator":
        expr = st.text_input("Expression", value="(250 - 200) / 200 * 100")
        if st.button("Calculate"):
            res = TOOL_FUNCTIONS["calculator"](expression=expr)
            st.json(res)

    elif chosen_tool == "summarize":
        sample_text = st.text_area("Text to summarize", value="Trí tuệ nhân tạo đang biến đổi ngành y tế. Các mô hình thị giác máy tính hỗ trợ chẩn đoán phim X-quang với độ chính xác cao. Việc phân tích hồ sơ bệnh án điện tử giúp dự đoán nguy cơ biến chứng sớm.")
        style = st.selectbox("Style", ["bullet_points", "numbered", "paragraph"])
        if st.button("Summarize"):
            res = TOOL_FUNCTIONS["summarize"](text=sample_text, style=style, max_points=3)
            st.json(res)

    elif chosen_tool == "cross_reference":
        claim = st.text_input("Claim", value="Kiến trúc Transformer ra đời năm 2017 do Google giới thiệu")
        sources = st.text_area("Sources (1 per line)", value="Năm 2017, các nhà nghiên cứu tại Google công bố kiến trúc Transformer.\nBài báo Attention Is All You Need giới thiệu mô hình Transformer năm 2017.\nNội dung không liên quan.")
        if st.button("Cross-Reference Claim"):
            source_list = [s.strip() for s in sources.split("\n") if s.strip()]
            res = TOOL_FUNCTIONS["cross_reference"](claim=claim, sources=source_list)
            st.json(res)

    elif chosen_tool == "lookup":
        q = st.text_input("Search query", value="AI hardware news")
        topic = st.selectbox("Topic", ["news", "general"])
        tf = st.selectbox("Timeframe", ["day", "week", "month", "year"])
        if st.button("Run Web Lookup"):
            res = TOOL_FUNCTIONS["lookup"](query=q, topic=topic, timeframe=tf)
            st.json(res)

    elif chosen_tool == "policy":
        q = st.text_input("Policy query", value="source citation twitter x")
        parea = st.selectbox("Policy Area", ["all", "source_citation", "data_privacy", "external_publishing", "ai_research", "tool_usage"])
        if st.button("Search Policy"):
            res = TOOL_FUNCTIONS["policy"](query=q, policy_area=parea)
            st.json(res)

    elif chosen_tool == "timeline":
        handle = st.text_input("Handle (without @)", value="sama")
        lim = st.number_input("Limit", value=3, min_value=1, max_value=20)
        if st.button("Get User Tweets"):
            res = TOOL_FUNCTIONS["timeline"](screenname=handle, limit=int(lim))
            st.json(res)

    elif chosen_tool == "export_report":
        content = st.text_area("Report Content", value="# Research Report\nKey insights here...")
        fname = st.text_input("Filename", value="test_report.md")
        ftype = st.selectbox("Format", ["markdown", "html", "json", "text"])
        if st.button("Export File"):
            res = TOOL_FUNCTIONS["export_report"](content=content, filename=fname, format_type=ftype)
            st.json(res)

    else:
        st.info(f"Tool `{chosen_tool}` is registered in the system.")

# TAB 4: Prompt & Declarations
with tabs[3]:
    st.subheader("📜 System Prompt & Tools Declarations")
    prompt_text, declarations, prompt_p, tools_p = load_version_artifacts(selected_version)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**System Prompt (`{prompt_p.name}`):**")
        st.code(prompt_text, language="markdown")

    with c2:
        st.markdown(f"**Tool Declarations (`{tools_p.name}`):**")
        st.code(tools_p.read_text(encoding="utf-8"), language="yaml")

