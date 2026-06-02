from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from chat import run_model_tool_loop, trim_history, write_transcript, safe_slug
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version, artifact_version_dict

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

st.set_page_config(page_title="Research Agent", page_icon="🔍", layout="wide")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")
    provider_name = st.selectbox("Provider", ["gemini", "openrouter", "anthropic", "openai"], index=0)
    model_input = st.text_input("Model", value="gemini-3.1-flash-lite", help="Leave blank for provider default")
    version_label = st.text_input("Version", value="v3")
    st.divider()
    st.markdown("**Tools available**")
    declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    for t in declarations:
        st.markdown(f"- `{t['name']}`")
    st.divider()
    if st.button("🗑️ Clear conversation"):
        for key in ["messages", "history", "transcript", "transcript_path"]:
            st.session_state.pop(key, None)
        st.rerun()

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages: list[dict] = []
if "history" not in st.session_state:
    st.session_state.history: list[dict] = []
if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "transcript_path" not in st.session_state:
    st.session_state.transcript_path = None

# ── Load artifacts (cached) ───────────────────────────────────────────────────
@st.cache_resource
def load_artifacts():
    system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    tool_decls = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    return system_prompt, to_openai_tools(tool_decls)

system_prompt, openai_tools = load_artifacts()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🔍 Research Agent")
st.caption("Tìm tin tức, đọc URL, theo dõi Twitter/X, tìm paper — hỏi bằng tiếng Việt hoặc tiếng Anh.")

# ── Render existing messages ──────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_events"):
            tool_names = ", ".join(e["tool"] for e in msg["tool_events"])
            with st.expander(f"🔧 Tools used: {tool_names}"):
                st.json(msg["tool_events"])

# ── Chat input ────────────────────────────────────────────────────────────────
if user_input := st.chat_input("Nhập câu hỏi..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    messages_for_model = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, 5),
        {"role": "user", "content": user_input},
    ]

    with st.chat_message("assistant"):
        with st.spinner("Đang xử lý..."):
            try:
                provider = make_provider(provider_name)
                model = model_input.strip() or None
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages_for_model,
                    tools=openai_tools,
                    model=model,
                    max_tool_rounds=4,
                )
                assistant_text = result["assistant_text"] or ""
                tool_events = result.get("tool_events", [])

                st.markdown(assistant_text)
                if tool_events:
                    tool_names = ", ".join(e["tool"] for e in tool_events)
                    with st.expander(f"🔧 Tools used: {tool_names}"):
                        st.json(tool_events)

            except Exception as exc:
                assistant_text = ""
                tool_events = []
                st.error(f"Provider error: {exc}")

    # Update history and session messages
    st.session_state.history.append({"role": "user", "content": user_input})
    st.session_state.history.append({"role": "assistant", "content": assistant_text})
    st.session_state.messages.append({
        "role": "assistant",
        "content": assistant_text,
        "tool_events": tool_events or None,
    })

    # Init transcript on first turn
    if st.session_state.transcript is None:
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        transcript_id = f"{safe_slug(version_label)}_{safe_slug(provider_name)}_{timestamp}"
        artifact_ver = build_artifact_version(
            version_label,
            ARTIFACTS_DIR / "system_prompt.md",
            ARTIFACTS_DIR / "tools.yaml",
        )
        st.session_state.transcript_path = ROOT / "transcripts" / f"{transcript_id}.transcript.json"
        st.session_state.transcript = {
            "transcript_id": transcript_id,
            **artifact_version_dict(artifact_ver),
            "provider": provider_name,
            "model": model,
            "turns": [],
        }

    st.session_state.transcript["turns"].append({
        "user": user_input,
        "assistant_text": assistant_text,
        "tool_events": tool_events,
        "status": result.get("status") if "result" in dir() else "error",
    })
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)

# ── Transcript download ───────────────────────────────────────────────────────
if st.session_state.transcript:
    with st.sidebar:
        st.divider()
        st.success(f"Transcript: `{st.session_state.transcript_path.name}`")
        st.download_button(
            label="⬇️ Download transcript",
            data=json.dumps(st.session_state.transcript, ensure_ascii=False, indent=2),
            file_name=st.session_state.transcript_path.name,
            mime="application/json",
        )
