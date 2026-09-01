import streamlit as st
import time
from api_client import APIClient

st.set_page_config(
    page_title="RetailAI Research Agent",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize API Client
if 'api_client' not in st.session_state:
    st.session_state.api_client = APIClient()

api_client = st.session_state.api_client

# ---- SIDEBAR: Research History ----
with st.sidebar:
    st.title("🛒 RetailAI Research")
    st.write("Enterprise AI Agent")
    
    st.divider()
    st.subheader("Research History")
    
    # Fetch history
    history = api_client.get_research_sessions(limit=20)
    
    if not history:
        st.info("No research sessions yet.")
    else:
        for session in history:
            title = session.get("research_question", "Untitled")
            # Truncate title if too long
            if len(title) > 40:
                title = title[:37] + "..."
                
            status_emoji = "⏳" if session["status"] in ["pending", "running"] else "✅" if session["status"] == "completed" else "❌"
            
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                if st.button(f"{status_emoji} {title}", key=f"hist_{session['id']}", use_container_width=True):
                    st.session_state.current_session_id = session["id"]
            with col2:
                with st.popover("⋮"):
                    if st.button("Delete", key=f"del_{session['id']}", type="primary", use_container_width=True):
                        api_client.delete_session(session["id"])
                        if st.session_state.get("current_session_id") == session["id"]:
                            st.session_state.current_session_id = None
                        st.rerun()

# ---- MAIN LAYOUT ----
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None

st.title("New Research Request")

with st.form("research_form"):
    question = st.text_area(
        "Enter your retail research question:",
        placeholder="e.g., How will generative AI impact retail inventory management in 2026?",
        height=100
    )
    submitted = st.form_submit_button("Submit Research", type="primary")

    if submitted:
        if len(question.strip()) < 5:
            st.error("Please enter a valid research question (at least 5 characters).")
        else:
            with st.spinner("Initializing research session... (This may take up to 60 seconds if the Render Free Tier server is waking up from sleep)"):
                try:
                    new_session = api_client.create_research_session(question)
                    st.session_state.current_session_id = new_session["id"]
                    st.success(f"Session #{new_session['id']} created successfully!")
                    # Wait a tiny bit to allow backend to potentially start (workflow runs async later or via separate worker, but for now we'll just show status)
                    time.sleep(1)
                except Exception as e:
                    st.error(f"Failed to submit: {str(e)}")

st.divider()

# ---- RESULTS DASHBOARD ----
if st.session_state.current_session_id:
    session_id = st.session_state.current_session_id
    st.header(f"Research Dashboard (Session #{session_id})")
    
    # Poll for status if not completed
    poll_placeholder = st.empty()
    max_retries = 60 # e.g., 60 seconds
    retry_count = 0
    
    session_data = None
    
    while retry_count < max_retries:
        try:
            session_data = api_client.get_research_session(session_id)
        except Exception as e:
            st.error(str(e))
            break
            
        status = session_data.get("status")
        
        if status in ["completed", "failed"]:
            poll_placeholder.empty()
            break
            
        with poll_placeholder.container():
            st.info(f"Research is currently **{status.upper()}**... Please wait.")
            st.progress((retry_count % 10) * 10)
            
        time.sleep(2)
        retry_count += 1
        
    if session_data:
        status = session_data.get("status")
        
        if status == "failed":
            st.error(f"Research Failed: {session_data.get('error_message', 'Unknown error')}")
        elif status == "completed":
            st.success("Research Completed Successfully!")
            
            # Show Findings & Recommendations
            tab1, tab2, tab3 = st.tabs(["Recommendations", "Findings", "Sources & Evidence"])
            
            with tab1:
                st.subheader("Actionable Recommendations")
                recs = session_data.get("recommendations", [])
                if not recs:
                    st.info("No recommendations generated.")
                for i, r in enumerate(recs):
                    st.markdown(f"**{i+1}. {r.get('recommendation')}**")
                    if r.get('rationale'):
                        st.markdown(f"*Rationale:* {r.get('rationale')}")
                    if r.get('confidence'):
                        st.caption(f"Confidence: {r.get('confidence')}")
                    st.divider()
                    
            with tab2:
                st.subheader("Key Findings")
                findings = session_data.get("findings", [])
                if not findings:
                    st.info("No findings generated.")
                for f in findings:
                    st.info(f"{f.get('statement')} (Confidence: {f.get('confidence')})")
                    
            with tab3:
                st.subheader("Traceability")
                sources = {s["id"]: s for s in session_data.get("sources", [])}
                evidence = {e["id"]: e for e in session_data.get("evidence", [])}
                
                for src_id, src in sources.items():
                    with st.expander(f"📄 Source: {src.get('title', 'Untitled')}"):
                        st.markdown(f"**URL:** [{src.get('url', 'No URL')}]({src.get('url', '#')})")
                        st.markdown(f"**Publisher:** {src.get('publisher')}")
                        # Find evidence for this source
                        src_evidence = [e for e in evidence.values() if e.get("source_id") == src_id]
                        if src_evidence:
                            st.markdown("**Extracted Evidence:**")
                            for ev in src_evidence:
                                st.markdown(f"- \"{ev.get('text')}\"")
                                if ev.get("relevance_score"):
                                    st.caption(f"Relevance: {ev.get('relevance_score')}")
                        else:
                            st.info("The AI reviewed this source but did not extract any highly relevant evidence to answer your specific question. It was filtered out as noise.")
