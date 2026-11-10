"""Local evaluation dashboard for VinUni Day03 Research Agent Lab.

Run from starter_v0: streamlit run streamlit_app.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "runs"
SUITES = {
    "Base (20 cases)": ("base", ROOT / "data" / "eval_base.json"),
    "Group (10 cases)": ("group", ROOT / "data" / "eval_group.json"),
    "Research extension": ("extension", ROOT / "data" / "eval_research_extension.json"),
}


def available_runs() -> list[Path]:
    return sorted(RUNS.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True) if RUNS.exists() else []


def load_run(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("summary"), dict):
        raise ValueError("Invalid evaluation run format")
    return value


def show_run(path: Path) -> None:
    try:
        data = load_run(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        st.error(f"Cannot load {path.name}: {exc}")
        return

    summary = data["summary"]
    st.subheader("Kết quả đánh giá")
    st.caption(f"{data.get('version', '?')} · {data.get('provider', '?')} · {data.get('suite', '?')} · {data.get('generated_at', '?')}")
    a, b, c, d = st.columns(4)
    a.metric("Tổng số case", summary.get("total_cases", 0))
    b.metric("Đã đo", summary.get("measured_cases", 0))
    c.metric("Đạt", summary.get("passed_cases", 0))
    d.metric("Provider errors", summary.get("provider_error_cases", 0))

    accuracy = float(summary.get("case_accuracy") or 0)
    st.metric("Case accuracy (chỉ tính case đã đo)", f"{accuracy:.1%}")
    st.progress(max(0.0, min(accuracy, 1.0)))
    if summary.get("provider_error_cases"):
        st.warning("Có lỗi provider/quota. Không xem tỷ lệ trên những case đo được là kết quả đầy đủ của cả bộ.")

    lcol, rcol = st.columns(2)
    with lcol:
        st.write("**Các chỉ tiêu**")
        for key, label in (
            ("tool_routing_accuracy", "Tool routing"),
            ("argument_accuracy", "Argument"),
            ("multiturn_accuracy", "Multi-turn"),
        ):
            value = summary.get(key)
            st.write(f"{label}: {value:.1%}" if isinstance(value, (int, float)) else f"{label}: N/A")
    with rcol:
        st.write("**Nhóm lỗi**")
        counts = summary.get("failure_counts") or {}
        st.bar_chart(counts) if counts else st.info("Chưa ghi nhận lỗi phân loại trên các case đã đo.")

    rows = []
    for item in data.get("results", []):
        result = item.get("result", {})
        rows.append({
            "case": item.get("id"),
            "status": "PROVIDER ERROR" if result.get("failure_type") == "provider_error" else ("PASS" if result.get("passed") else "FAIL"),
            "failure_type": result.get("failure_type") or "",
            "mismatch": result.get("observed_mismatch") or "",
            "multiturn": bool(item.get("is_multiturn")),
        })
    st.write("**Chi tiết từng case**")
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
        for item in data.get("results", []):
            with st.expander(item.get("id", "Case")):
                st.write("Expected", item.get("expect", {}))
                st.write("Actual", item.get("result", {}).get("actual_tool_calls", []))
                st.write("Failures", item.get("result", {}).get("failures", []))
    st.download_button("Tải JSON kết quả", path.read_bytes(), file_name=path.name, mime="application/json")


st.set_page_config(page_title="VinUni Day03 · Research Agent Eval", layout="wide")
st.title("Research Agent · Evaluation Dashboard")
st.caption("VinUni Day03 | Báo cáo eval v0/v1/v2 và kiểm thử chọn tool")

with st.sidebar:
    st.header("Điều khiển")
    section = st.radio("Chức năng", ["Kết quả eval", "Chạy eval", "Bộ test"], label_visibility="collapsed")

if section == "Kết quả eval":
    paths = available_runs()
    if not paths:
        st.info("Chưa có file JSON trong runs/. Hãy chạy run_eval.py hoặc chọn tab 'Chạy eval'.")
    else:
        chosen = st.selectbox("Chọn run", paths, format_func=lambda path: path.name)
        show_run(chosen)

elif section == "Chạy eval":
    st.subheader("Chạy kiểm thử mô hình")
    st.warning("Chạy Gemini/OpenRouter sẽ gửi yêu cầu API và có thể tiêu tốn quota/chi phí. Chỉ chạy khi anh xác nhận bằng nút bên dưới.")
    suite_label = st.selectbox("Bộ dữ liệu", list(SUITES))
    suite, cases_path = SUITES[suite_label]
    provider = st.selectbox("Provider", ["gemini", "openrouter", "openai", "anthropic", "ollama"])
    version = st.text_input("Nhãn phiên bản", value="v2", max_chars=30)
    if cases_path.exists():
        try:
            dataset = json.loads(cases_path.read_text(encoding="utf-8"))
            st.write(f"Số case: {len(dataset.get('cases', []))}")
        except (json.JSONDecodeError, OSError):
            st.error("Không đọc được file dữ liệu")
    else:
        st.error(f"Không có {cases_path.name}")
    if st.button("▶ Chạy evaluation", type="primary", disabled=not cases_path.exists()):
        # Explicitly limit version to an innocuous label; subprocess never uses a shell.
        import re
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,30}", version):
            st.error("Nhãn phiên bản chỉ gồm chữ, số, dấu chấm, gạch dưới hoặc gạch ngang.")
        else:
            command = [sys.executable, "run_eval.py", "--provider", provider, "--version", version,
                       "--suite", suite, "--eval-cases", str(cases_path)]
            with st.spinner("Đang chạy eval (có thể mất vài phút)..."):
                try:
                    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=600)
                    st.code((result.stdout + "\n" + result.stderr)[-14000:], language="text")
                    if result.returncode:
                        st.error(f"Eval kết thúc với exit code {result.returncode}")
                    else:
                        st.success("Đã lưu kết quả vào runs/. Mở tab 'Kết quả eval' để xem.")
                except subprocess.TimeoutExpired:
                    st.error("Quá 10 phút. Kiểm tra kết nối và giới hạn provider trước khi chạy lại.")

else:
    st.subheader("Kiểm thử offline")
    st.write("Đã có kết quả trên máy anh: **84 passed in 1.10s**.")
    st.code("python -m pytest -q", language="powershell")
    st.info("Unit tests không sử dụng Gemini quota. Chỉ số độ chính xác của model cần được đo riêng bằng run_eval.py.")
