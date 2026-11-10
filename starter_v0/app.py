"""Streamlit UI for the same research tool loop as chat.py."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import streamlit as st

from chat import ROOT, confirm_send, json_text, now_iso, run_model_tool_loop, trim_history, write_transcript
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

st.set_page_config(page_title="Research Desk", page_icon="🔎", layout="wide")
st.title("🔎 Research Desk")
st.caption("Tìm nguồn · Đọc tài liệu · Tổng hợp có dẫn chứng")

with st.sidebar:
    st.header("Phiên nghiên cứu")
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "gemini", "anthropic", "ollama"])
    default_models = {"openrouter": "nvidia/nemotron-3.5-lightning:free", "openai": "gpt-4o-mini",
                      "gemini": "gemini-3.5-flash", "anthropic": "claude-haiku-4-5-20251001", "ollama": "qwen2.5:7b"}
    model = st.text_input("Model", default_models[provider_name], key=f"model_{provider_name}")
    version = st.selectbox("Phiên bản", [f"v{i}" for i in range(6, -1, -1)])
    st.caption("Chat cần API và hạn mức còn hiệu lực. Tab Kiểm tra nguồn chạy miễn phí trên máy.")
    if st.button("Cuộc trò chuyện mới"):
        for key in ["history", "transcript", "pending_action", "session_config"]:
            st.session_state.pop(key, None)
        st.rerun()

snapshot = ROOT / "artifacts" / "versions" / version
config = (provider_name, model, version)
if st.session_state.get("session_config") != config:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S") + "_" + uuid4().hex[:8]
    evidence = build_artifact_version(version, snapshot / "system_prompt.md", snapshot / "tools.yaml")
    st.session_state.session_config = config
    st.session_state.history = []
    st.session_state.pending_action = None
    st.session_state.transcript = {
        "transcript_id": f"{version}_{provider_name}_ui_{stamp}", **artifact_version_dict(evidence),
        "provider": provider_name, "model": model, "source": "streamlit", "created_at": now_iso(),
        "system_prompt": str(snapshot / "system_prompt.md"), "tools": str(snapshot / "tools.yaml"), "turns": [],
    }

chat_tab, audit_tab, evidence_tab = st.tabs(["Trò chuyện", "Kiểm tra nguồn", "Kết quả eval"])

with chat_tab:
    st.info("Gợi ý: Tìm tin AI hôm nay · Đọc một URL · Tra policy công ty về trích dẫn.")
    for turn in st.session_state.transcript["turns"]:
        with st.chat_message("user"):
            st.write(turn["user"])
        with st.chat_message("assistant"):
            st.markdown(turn.get("assistant_text") or turn.get("error", ""))
            if turn.get("tool_events"):
                with st.expander("Nguồn và kết quả công cụ"):
                    st.json(turn["tool_events"])

    pending = st.session_state.pending_action
    if pending:
        st.warning("Nội dung chờ xác nhận gửi Telegram")
        st.code(pending["text"], language=None)
        yes, no = st.columns(2)
        if yes.button("Xác nhận gửi nội dung này", type="primary"):
            sent = confirm_send(pending["text"])
            event = {"tool": "send", "args": {"text": pending["text"], "confirmed": True}, "result": sent}
            turn = {"user": "[Bấm xác nhận gửi nội dung đã xem]", "status": "answered",
                    "assistant_text": "Đã gửi Telegram." if sent.get("status") == "sent" else json_text(sent),
                    "tool_events": [event], "started_at": now_iso(), "ended_at": now_iso()}
            st.session_state.transcript["turns"].append(turn)
            st.session_state.history.extend([{"role": "user", "content": turn["user"]},
                                             {"role": "assistant", "content": turn["assistant_text"]}])
            st.session_state.pending_action = None
            path = ROOT / "transcripts" / (st.session_state.transcript["transcript_id"] + ".transcript.json")
            write_transcript(path, st.session_state.transcript)
            st.rerun()
        if no.button("Hủy gửi"):
            st.session_state.pending_action = None
            st.rerun()

    user_text = st.chat_input("Bạn muốn nghiên cứu điều gì?")
    if user_text:
        st.session_state.pending_action = None
        turn = {"turn_index": len(st.session_state.transcript["turns"]) + 1, "user": user_text, "started_at": now_iso()}
        try:
            with st.spinner("Đang thu thập và đối chiếu nguồn…"):
                result = run_model_tool_loop(
                    provider=make_provider(provider_name), model=model,
                    messages=[{"role": "system", "content": (snapshot / "system_prompt.md").read_text(encoding="utf-8")},
                              *trim_history(st.session_state.history, 5), {"role": "user", "content": user_text}],
                    tools=to_openai_tools(load_tool_declarations(snapshot / "tools.yaml")), max_tool_rounds=4,
                )
            turn.update(result)
            st.session_state.pending_action = result.get("pending_action")
            st.session_state.history.extend([{"role": "user", "content": user_text}, {
                "role": "assistant", "content": result["assistant_text"] + "\nTOOL_EVIDENCE_JSON:\n" + json_text(result["tool_events"], max_chars=16000)}])
        except Exception as exc:
            status = getattr(exc, "status_code", None) or getattr(getattr(exc, "response", None), "status_code", None)
            turn.update({"status": "provider_error", "assistant_text": (
                "Provider hết hạn mức hoặc bị giới hạn tốc độ (HTTP 429). Thử lại khi quota được đặt lại, hoặc chọn provider còn hạn mức."
                if status == 429 else f"Không hoàn tất yêu cầu ({type(exc).__name__}). Kiểm tra cấu hình provider và kết nối."
            ), "tool_events": []})
        turn["ended_at"] = now_iso()
        st.session_state.transcript["turns"].append(turn)
        path = ROOT / "transcripts" / (st.session_state.transcript["transcript_id"] + ".transcript.json")
        write_transcript(path, st.session_state.transcript)
        st.rerun()
    if st.session_state.transcript["turns"]:
        st.download_button("Tải transcript JSON", json_text(st.session_state.transcript),
                           file_name="research.transcript.json", mime="application/json")

with audit_tab:
    st.subheader("Rà soát danh sách nguồn")
    st.write("Phát hiện link thiếu và link trùng; giữ lại các tham số có ý nghĩa. Kết quả không xác minh tính đúng của nội dung.")
    source_input = st.text_area("Nguồn dạng JSON", value=json.dumps([
        {"title": "Nguồn A", "url": "https://example.com/article?utm_source=newsletter"},
        {"title": "Nguồn A (bản sao)", "url": "https://example.com/article"},
        {"title": "Nguồn thiếu link"},
    ], ensure_ascii=False, indent=2), height=240)
    if st.button("Kiểm tra nguồn", type="primary"):
        try:
            result = TOOL_FUNCTIONS["source_audit"](json.loads(source_input))
            if result.get("error"):
                st.error(result["message"])
            else:
                a, b, c = st.columns(3)
                a.metric("Nguồn duy nhất", result["unique_count"])
                b.metric("Tên miền", result["domain_count"])
                c.metric("Vấn đề", len(result["issues"]))
                st.json(result)
        except json.JSONDecodeError:
            st.error("JSON chưa hợp lệ. Nhập một danh sách các object nguồn.")

with evidence_tab:
    st.subheader("Bằng chứng đo thực tế")
    rows = []
    for path in sorted((ROOT / "runs").glob("*.json")):
        run = json.loads(path.read_text(encoding="utf-8"))
        summary = run["summary"]
        rows.append({"Version": run["version"], "Provider": run["provider"], "Suite": run["suite"],
                     "PASS": summary["passed_cases"], "Đã đo": summary["measured_cases"],
                     "Tổng": run.get("dataset_total_cases", summary["total_cases"]), "Lỗi provider": summary["provider_error_cases"],
                     "Accuracy (case đã đo)": summary["case_accuracy"]})
    # Plain Markdown keeps the UI usable on machines where WDAC blocks pyarrow DLLs.
    if rows:
        columns = list(rows[0])
        table = "| " + " | ".join(columns) + " |\n|" + "|".join(["---"] * len(columns)) + "|\n"
        table += "\n".join("| " + " | ".join(str(row[column]) for column in columns) + " |" for row in rows)
        st.markdown(table)
    st.caption("Accuracy chỉ tính các case đã đo. Một run thiếu case chưa chứng minh chất lượng trên cả bộ đề.")
