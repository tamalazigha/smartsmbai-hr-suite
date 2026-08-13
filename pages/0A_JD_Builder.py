"""Pages/0A_JD_Builder.py — Agent A: JD Builder (SmartSMBAI)
Two tabs: Build New JD | JD Library
Auto-saves to Supabase on generate. Agent B reads from library.
"""
import streamlit as st, json
from jd_agent import (build_job_description, save_job_description,
                       get_job_descriptions, REGIONS, EEO_DEFAULT)

st.set_page_config(page_title="JD Builder — SmartSMBAI", page_icon="📝", layout="wide")
st.markdown("""<div style='padding:12px 16px;background:linear-gradient(135deg,#1A2B5E,#059669);
border-radius:6px;margin-bottom:16px'>
<span style='font-size:18px;font-weight:700;color:#fff'>Smart</span>
<span style='font-size:18px;font-weight:700;color:#93C5FD'>SMB</span>
<span style='font-size:18px;font-weight:700;color:#fff'>AI</span>
<span style='font-size:12px;color:#A7F3D0;margin-left:10px'>
Agent A — JD Builder · Certified Growth Agent · Region-Specific · Auto-Saves to Library</span>
</div>""", unsafe_allow_html=True)

tab_build, tab_library = st.tabs(["✏️ Build New JD", "📚 JD Library"])

# ── TAB 1: BUILD NEW JD ──────────────────────────────────────────────
with tab_build:
    col1, col2 = st.columns([1, 2])
    with col1:
        region = st.selectbox("Region *", REGIONS, key="build_region")
        eeo    = st.text_area("EEO Statement", value=EEO_DEFAULT, height=100, key="build_eeo")

    with col2:
        st.info(
            f"**Certified Growth Agent — {region}**\n\n"
            "This is SmartSMBAI's single role. Claude will generate a region-specific "
            "job description tailored to local channels, payment methods, networks, "
            "and regulatory context. The JD is automatically saved to the library "
            "after generation — no manual save needed."
        )

    st.markdown("---")
    if st.button("✨ Generate Job Description", type="primary", use_container_width=True):
        with st.spinner(f"Claude is writing the {region} Growth Agent JD…"):
            result = build_job_description(region=st.session_state["build_region"],
                                           eeo=st.session_state["build_eeo"])
        if "error" in result:
            st.error(f"Generation failed: {result['error']}")
        else:
            # Auto-save to Supabase immediately
            jd_id = save_job_description(result)
            result["id"] = jd_id
            st.session_state["current_jd"] = result
            if jd_id:
                st.success(f"✅ Job description generated and saved to library! (ID: `{jd_id[:8]}…`)")
                st.info("➡️ Go to **Agent B — Job Board** to format and distribute it, or view it in the **JD Library** tab.")
            else:
                st.warning("Generated but could not save to database — check Supabase connection.")

    if "current_jd" in st.session_state:
        jd = st.session_state["current_jd"]
        st.markdown("---")
        st.markdown(f"## {jd.get('role_title', '')}")

        with st.expander("📄 Role Summary", expanded=True):
            st.write(jd.get("role_summary", ""))

        with st.expander("📋 What You'll Do"):
            for r in jd.get("what_youll_do", []): st.markdown(f"- {r}")

        with st.expander("✅ What We Need"):
            for r in jd.get("what_we_need", []): st.markdown(f"- {r}")

        if jd.get("nice_to_have"):
            with st.expander("⭐ Nice to Have"):
                for r in jd["nice_to_have"]: st.markdown(f"- {r}")

        with st.expander("💰 Compensation"):
            for r in jd.get("compensation", []): st.markdown(f"- {r}")

        with st.expander("📣 Social Media Teasers"):
            st.markdown("**X / Twitter (≤280 chars):**")
            st.code(jd.get("social_teaser_short", ""), language=None)
            st.markdown("**LinkedIn Post:**")
            st.text_area("LinkedIn", value=jd.get("social_teaser_linkedin", ""),
                         height=100, disabled=True, key="li_preview")

        with st.expander("📝 Full Job Description (plain text)"):
            st.text_area("Full JD", value=jd.get("full_jd", ""), height=400,
                         key="full_jd_preview")
            st.download_button(
                "⬇️ Download as .txt",
                data=jd.get("full_jd", ""),
                file_name=f"SmartSMBAI_Growth_Agent_{jd.get('region','').replace(' ','_')}.txt",
                mime="text/plain",
            )
            st.download_button(
                "⬇️ Download as JSON",
                data=json.dumps(jd, indent=2),
                file_name=f"SmartSMBAI_JD_{jd.get('region','').replace(' ','_')}.json",
                mime="application/json",
            )

        if st.button("➡️ Load into Agent B — Job Board", type="primary"):
            st.session_state["distribute_jd"] = jd
            st.success("Loaded into Agent B. Navigate to Agent B — Job Board now.")

# ── TAB 2: JD LIBRARY ────────────────────────────────────────────────
with tab_library:
    st.markdown("### All Saved Job Descriptions")
    if st.button("🔄 Refresh Library", key="refresh_lib"):
        st.rerun()

    jds = get_job_descriptions()
    if not jds:
        st.info("No saved JDs yet. Generate one in the Build tab — it saves automatically.")
    else:
        import pandas as pd
        df = pd.DataFrame([{
            "Title":    j.get("role_title", ""),
            "Region":   j.get("location", ""),
            "Status":   j.get("status", "draft").title(),
            "Created":  j.get("created_at", "")[:10],
            "ID":       j.get("id", "")[:8] + "…",
        } for j in jds])
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### Load a JD into Agent B")
        options = [f"{j.get('role_title','')} — {j.get('created_at','')[:10]}" for j in jds]
        selected = st.selectbox("Select a JD:", options, key="lib_select")

        col_load, col_del = st.columns([2, 1])
        with col_load:
            if st.button("📤 Load this JD into Agent B", type="primary", use_container_width=True):
                idx = options.index(selected)
                st.session_state["distribute_jd"] = jds[idx]
                st.session_state["current_jd"]    = jds[idx]
                st.success("✅ Loaded! Navigate to **Agent B — Job Board** to distribute it.")

        with col_del:
            if st.button("🗑️ Archive this JD", use_container_width=True):
                idx = options.index(selected)
                jd_id = jds[idx].get("id", "")
                if jd_id:
                    from database import _sb
                    if _sb:
                        try:
                            _sb.table("job_descriptions").update(
                                {"status": "archived"}
                            ).eq("id", jd_id).execute()
                            st.success("Archived.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Archive failed: {e}")

        # Preview selected JD
        if selected:
            idx = options.index(selected)
            jd  = jds[idx]
            with st.expander(f"👁️ Preview: {jd.get('role_title','')}", expanded=False):
                st.write(jd.get("summary", jd.get("full_jd","")[:500] + "…"))
                st.caption(f"Status: {jd.get('status','draft').title()} · Created: {jd.get('created_at','')[:10]}")
