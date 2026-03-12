import streamlit as st
import time
from datetime import datetime, timedelta, timezone
from monitoring import setup_langfuse

from agents.segmentation import segmentation_agent, rank_and_select_customers
from agents.copywriter import content_generation_agent, optimizer_agent_bulk
from agents.execution import execution_agent
from agents.reporting import reporting_agent
from tools import dynamic_api_executor
from groq import Groq

setup_langfuse()

# ── Session State ──────────────────────────────────────────────────────────────
defaults = {
    "page": "input",               # input | review | monitoring | pick_variant
    "generated_data": None,
    "cohort_ids": [],
    "brief": "",
    "campaign_id": None,
    "optimization_count": 0,
    "all_customers_count": 0,
    "optimizer_variants": [],      # list of 5 dicts
    "prev_open_rate": 0,
    "prev_click_rate": 0,
    "new_open_rate": 0,
    "new_click_rate": 0,
    "campaign_history": [],        # list of {round, campaign_id, subject, open_rate, click_rate}
    "fetched_open_rate": 0,        # persisted after fetch so metrics stay visible
    "fetched_click_rate": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="CampaignX", page_icon="🚀", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.page-title {
    font-family: 'Syne', sans-serif;
    font-size: 24px; font-weight: 800;
    color: #e6f1ff; margin-bottom: 2px;
}
.page-sub { font-size: 13px; color: #64748b; margin-bottom: 24px; }

.email-preview {
    background: #0d1b2a;
    border: 1px solid #1e3a5f;
    border-left: 4px solid #00c8ff;
    padding: 22px 26px; border-radius: 12px;
    color: #ccd6f6; line-height: 1.9; font-size: 14px;
}

/* Variant cards on pick_variant page */
.vcard {
    background: #0b1929;
    border: 2px solid #1a2f4a;
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 8px;
    transition: all 0.15s ease;
}
.vcard-selected {
    border-color: #00c8ff !important;
    background: #0d2035 !important;
    box-shadow: 0 0 0 3px rgba(0,200,255,0.12);
}
.vtag {
    display: inline-block;
    border-radius: 20px; padding: 3px 12px;
    font-size: 11px; font-weight: 700;
    letter-spacing: 0.06em; text-transform: uppercase;
    margin-bottom: 10px;
}
.subject-line {
    font-size: 15px; font-weight: 600;
    color: #e2e8f0; margin: 6px 0 8px;
}
.reasoning-text { font-size: 12px; color: #64748b; font-style: italic; }

/* Stat pill */
.stat-pill {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 14px; border-radius: 100px;
    font-size: 13px; font-weight: 600;
}

/* Compare box */
.compare-box {
    border-radius: 14px; padding: 20px 24px; margin: 16px 0;
}

.sidebar-chip {
    background: #0d1b2a; border-radius: 10px;
    padding: 10px 14px; margin-bottom: 8px;
    border-left: 3px solid #00c8ff;
}

.stButton > button {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
}
div[data-testid="stMetricValue"] { font-family: 'Syne', sans-serif !important; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚀 CampaignX")
    st.caption("Multi-Agent Marketing Automation")
    st.divider()

    page_order  = ["input", "review", "monitoring", "pick_variant", "comparison"]
    page_labels = {"input": "📋 Brief", "review": "✍️ Review",
                   "monitoring": "📊 Monitor", "pick_variant": "🎯 Pick & Launch",
                   "comparison": "📈 Compare"}
    cur = st.session_state.page

    st.markdown("**Flow**")
    for p in page_order:
        lbl = page_labels[p]
        if p == cur:
            st.markdown(f"🔵 **{lbl}**")
        elif page_order.index(p) < page_order.index(cur):
            st.markdown(f"✅ ~~{lbl}~~")
        else:
            st.markdown(f"⚪ {lbl}")

    st.divider()

    if st.session_state.all_customers_count:
        st.markdown(f"""<div class="sidebar-chip">
            <div style="font-size:10px;color:#64748b;text-transform:uppercase;">Total Cohort</div>
            <div style="font-size:18px;font-weight:700;color:#e2e8f0;">{st.session_state.all_customers_count:,}</div>
        </div>""", unsafe_allow_html=True)

    if st.session_state.cohort_ids:
        n = len(st.session_state.cohort_ids)
        t = st.session_state.all_customers_count or n
        st.markdown(f"""<div class="sidebar-chip" style="border-left-color:#00ff88;">
            <div style="font-size:10px;color:#64748b;text-transform:uppercase;">Targeted</div>
            <div style="font-size:18px;font-weight:700;color:#00ff88;">{n:,}
                <span style="font-size:12px;">({n/t*100:.0f}%)</span></div>
        </div>""", unsafe_allow_html=True)

    if st.session_state.prev_open_rate:
        st.markdown(f"""<div class="sidebar-chip" style="border-left-color:#ffd700;">
            <div style="font-size:10px;color:#64748b;text-transform:uppercase;">Last Open Rate</div>
            <div style="font-size:18px;font-weight:700;color:#ffd700;">{st.session_state.prev_open_rate:.1f}%</div>
        </div>""", unsafe_allow_html=True)

    if st.session_state.optimization_count:
        st.markdown(f"""<div class="sidebar-chip" style="border-left-color:#c39bd3;">
            <div style="font-size:10px;color:#64748b;text-transform:uppercase;">Optimizations</div>
            <div style="font-size:18px;font-weight:700;color:#c39bd3;">{st.session_state.optimization_count}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    if st.button("🔁 Start Over", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# ── Shared helper: send_time string ───────────────────────────────────────────
def get_send_time_str(mode, sel_date=None, sel_time=None):
    """Returns properly formatted DD:MM:YY HH:MM:SS in IST."""
    if mode == "quick":
        dt_ist = datetime.now(timezone.utc) + timedelta(hours=5, minutes=31)  # UTC+5:30 + 1 min
        return dt_ist.strftime("%d:%m:%y %H:%M:%S")
    else:
        dt = datetime.combine(sel_date, sel_time)
        return dt.strftime("%d:%m:%y %H:%M:%S")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — INPUT
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "input":
    st.markdown('<div class="page-title">🚀 CampaignX — New Campaign</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Describe your goal. AI agents will segment the audience and draft the first email.</div>', unsafe_allow_html=True)

    col_form, col_info = st.columns([2, 1])

    with col_form:
        brief = st.text_area("Campaign Brief",
            value="Run email campaign for launching XDeposit. Announce higher returns for female senior citizens.",
            height=130)
        target_limit = st.number_input("Max Audience Size", min_value=1, max_value=100000, value=1000, step=100)

        if st.button("✨ Generate AI Campaign", type="primary", use_container_width=True):
            if not brief.strip():
                st.warning("Enter a campaign brief first!")
            else:
                with st.status("🤖 Agents working...", expanded=True) as status:
                    st.session_state.brief = brief
                    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

                    st.write("🔍 Fetching customer database...")
                    cohort_data = dynamic_api_executor(client, "Get all customer cohort IDs")

                    if "data" in cohort_data and len(cohort_data["data"]) > 0:
                        all_customers = cohort_data["data"]
                        st.session_state.all_customers_count = len(all_customers)
                        st.write(f"📊 Loaded **{len(all_customers):,}** customers.")

                        st.write("🕵️ Segmentation Agent scoring...")
                        seg = segmentation_agent(brief, all_customers[0])
                        logic = seg.get("scoring_logic", "0")
                        st.info(f"⚙️ {seg.get('strategy','')}")

                        st.write("🎯 Ranking & selecting top customers...")
                        st.session_state.cohort_ids = rank_and_select_customers(logic, all_customers, limit=target_limit)
                        st.write(f"✅ {len(st.session_state.cohort_ids):,} customers selected.")

                        st.write("✍️ Drafting email...")
                        st.session_state.generated_data = content_generation_agent(brief)
                        st.session_state.optimization_count = 0
                        st.session_state.optimizer_variants = []
                        st.session_state.prev_open_rate = 0

                        status.update(label="✅ Ready!", state="complete", expanded=False)
                        st.session_state.page = "review"
                        st.rerun()
                    else:
                        status.update(label="❌ API Error.", state="error")
                        st.error("Could not retrieve customer cohort.")

    with col_info:
        st.markdown("""<div style="background:#0b1929;border:1px solid #1a2f4a;border-radius:16px;padding:22px;font-size:13px;color:#64748b;">
        <p><strong style="color:#00c8ff;">1. Segmentation Agent</strong><br>Scores every customer.</p>
        <p><strong style="color:#00ff88;">2. Copywriter Agent</strong><br>Writes the first email.</p>
        <p><strong style="color:#ffd700;">3. Execution Agent</strong><br>Schedules via API.</p>
        <p><strong style="color:#c39bd3;">4. Reporting Agent</strong><br>Fetches open/click data.</p>
        <p><strong style="color:#ff6b6b;">5. Optimizer Agent</strong><br>Generates 5 new variants to beat the metrics.</p>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — REVIEW & SEND FIRST CAMPAIGN
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "review":
    st.markdown('<div class="page-title">✍️ Review & Schedule</div>', unsafe_allow_html=True)

    result = st.session_state.generated_data
    n = len(st.session_state.cohort_ids)
    t = st.session_state.all_customers_count or n

    # Audience pills
    st.markdown(f"""
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px;">
        <span class="stat-pill" style="background:#00c8ff15;border:1px solid #00c8ff40;color:#00c8ff;">👥 {t:,} Total Cohort</span>
        <span class="stat-pill" style="background:#00ff8815;border:1px solid #00ff8840;color:#00ff88;">🎯 {n:,} Selected ({n/t*100:.0f}%)</span>
        <span class="stat-pill" style="background:#ffd70015;border:1px solid #ffd70040;color:#ffd700;">📧 {n:,} Emails</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🧠 Agent Reasoning", expanded=False):
        st.info(result.get("strategy_reasoning", ""))

    st.markdown("### 📧 Email Draft")
    st.markdown(f"**Subject:** `{result.get('subject_line','')}`")
    st.markdown(f'<div class="email-preview">{result.get("email_body","")}</div>', unsafe_allow_html=True)
    st.write("")

    col_rej, _ = st.columns([1, 3])
    with col_rej:
        if st.button("🔄 Rewrite Email"):
            with st.spinner("Rewriting..."):
                st.session_state.generated_data = content_generation_agent(
                    st.session_state.brief,
                    "Write a completely different version with a new tone and angle."
                )
                st.rerun()

    st.divider()
    st.markdown("### 🕒 Schedule & Send")

    # Quick send
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        quick = st.button("⚡ Send in 1 Minute", type="primary", use_container_width=True)
    with c2:
        sel_date = st.date_input("Date", datetime.now(timezone.utc).date(), key="rev_date")
    with c3:
        default_t = (datetime.now(timezone.utc) + timedelta(hours=5, minutes=35)).time()
        sel_time = st.time_input("Time (IST)", default_t, key="rev_time")

    manual = st.button("🚀 Send at Scheduled Time", use_container_width=True, key="rev_manual")

    send_time_str = None
    if quick:
        send_time_str = get_send_time_str("quick")
        st.success(f"⚡ Will send at **{send_time_str}** IST")
    elif manual:
        send_time_str = get_send_time_str("manual", sel_date, sel_time)
        st.success(f"🕒 Will send at **{send_time_str}** IST")

    if send_time_str:
        with st.status("Launching...", expanded=True) as status:
            st.write(f"📤 Sending to **{n:,}** customers...")
            exec_result = execution_agent(
                result.get("subject_line"), result.get("email_body"),
                st.session_state.cohort_ids, send_time_str
            )
            if "campaign_id" in exec_result:
                st.session_state.campaign_id = exec_result["campaign_id"]
                status.update(label="✅ Campaign Live!", state="complete")
                st.toast("🎉 Campaign Launched!")
                st.balloons()
                time.sleep(2)
                st.session_state.page = "monitoring"
                st.rerun()
            else:
                status.update(label="❌ Failed.", state="error")
                st.error(f"Details: {exec_result}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — MONITORING
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "monitoring":
    st.markdown('<div class="page-title">📊 Live Campaign Dashboard</div>', unsafe_allow_html=True)

    cid = st.session_state.campaign_id
    n   = len(st.session_state.cohort_ids)

    st.success(f"🟢 Campaign Active — ID: `{cid}` | **{n:,}** emails sent")

    if st.session_state.optimization_count > 0:
        st.info(f"🔄 This is optimized round **#{st.session_state.optimization_count}**")

    # ── Fetch metrics section ──────────────────────────────────────────────
    col_fetch, col_new = st.columns([3, 1])
    with col_fetch:
        fetch = st.button("🔄 Fetch Real-Time Analytics", type="primary", use_container_width=True)
    with col_new:
        if st.button("➕ New Campaign", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    if fetch:
        with st.spinner("Fetching report..."):
            report = reporting_agent(cid)

        if "data" in report and len(report["data"]) > 0:
            data   = report["data"]
            total  = len(data)
            opens  = sum(1 for r in data if r.get("EO") == "Y")
            clicks = sum(1 for r in data if r.get("EC") == "Y")
            open_r  = (opens  / total) * 100
            click_r = (clicks / total) * 100

            # Update campaign history (upsert current round)
            existing = next((h for h in st.session_state.campaign_history if h["campaign_id"] == cid), None)
            if existing:
                existing["open_rate"] = open_r
                existing["click_rate"] = click_r
            else:
                st.session_state.campaign_history.append({
                    "round": st.session_state.optimization_count,
                    "campaign_id": cid,
                    "subject": st.session_state.generated_data.get("subject_line", ""),
                    "open_rate": open_r,
                    "click_rate": click_r,
                })

            # Save fetched rates into session
            st.session_state.fetched_open_rate  = open_r
            st.session_state.fetched_click_rate = click_r
            st.rerun()
        else:
            st.warning("⏳ No data yet — campaign may still be in queue. Wait a minute and try again.")

    # ── Show metrics if we have them ───────────────────────────────────────
    if "fetched_open_rate" in st.session_state and st.session_state.fetched_open_rate:
        open_r  = st.session_state.fetched_open_rate
        click_r = st.session_state.fetched_click_rate

        st.markdown("### 📊 Performance")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📤 Sent",       f"{n:,}")
        c2.metric("📬 Open Rate",  f"{open_r:.1f}%")
        c3.metric("🖱️ Click Rate", f"{click_r:.1f}%")
        c4.metric("👻 Unopened",   f"{n - int(n * open_r / 100):,}")

        # Health banner
        if open_r < 15:
            hc, hl = "#ff6b6b", "⚠️ Below Average — Run optimization to improve"
        elif open_r < 30:
            hc, hl = "#ffd700", "📈 Average — Can definitely be improved"
        else:
            hc, hl = "#00ff88", "🏆 Strong! But can still try to push higher"

        st.markdown(f"""<div style="background:{hc}12;border:1px solid {hc}44;border-radius:10px;
            padding:12px 18px;margin:14px 0;color:{hc};font-weight:600;">{hl}</div>""",
            unsafe_allow_html=True)

        # ── Optimization Engine (always visible after fetch) ───────────────
        st.divider()
        st.markdown("### ⚡ Optimize — Generate 5 New Emails")
        st.markdown(f"""<div style="background:#0b1929;border:1px solid #1a2f4a;border-radius:14px;padding:18px 22px;margin-bottom:18px;">
            <div style="font-size:14px;color:#94a3b8;">
                Current: Open <strong style="color:#00c8ff;">{open_r:.1f}%</strong> | 
                Click <strong style="color:#00ff88;">{click_r:.1f}%</strong><br><br>
                AI will generate <strong style="color:#c39bd3;">5 completely different optimized emails</strong>.
                Pick the best one and send it to the same <strong style="color:#ffd700;">{n:,} people</strong>.
                After that, a <strong style="color:#00c8ff;">comparison page</strong> will show how much your rates improved.
            </div>
        </div>""", unsafe_allow_html=True)

        notes = st.text_area("Manager's notes (optional):",
            placeholder="e.g. 'Open rate is low. Try urgency angle. Make subject shorter.'",
            height=70)

        if st.button("⚡ Generate 5 Optimized Emails →", type="primary", use_container_width=True):
            with st.spinner("AI generating 5 variants... (~15 sec)"):
                variants = optimizer_agent_bulk(
                    brief          = st.session_state.brief,
                    original_subject = st.session_state.generated_data.get("subject_line",""),
                    open_rate      = open_r,
                    click_rate     = click_r,
                    human_guidance = notes
                )
            if variants:
                # Save current rates as the "before" for comparison
                st.session_state.prev_open_rate  = open_r
                st.session_state.prev_click_rate = click_r
                st.session_state.optimizer_variants  = variants
                st.session_state.optimization_count += 1
                st.session_state.new_open_rate  = 0
                st.session_state.new_click_rate = 0
                st.session_state.fetched_open_rate  = 0
                st.session_state.fetched_click_rate = 0
                st.session_state.page = "pick_variant"
                st.rerun()
            else:
                st.error("Failed to generate variants. Try again.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — PICK 1 OF 5 OPTIMIZED EMAILS → LAUNCH → BACK TO MONITORING
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "pick_variant":
    variants = st.session_state.optimizer_variants
    prev_o   = st.session_state.prev_open_rate
    prev_c   = st.session_state.prev_click_rate
    n        = len(st.session_state.cohort_ids)

    st.markdown('<div class="page-title">🎯 Pick Your Optimized Email</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">5 AI-generated variants below — each uses a different strategy to beat your previous Open Rate of <strong style="color:#ffd700;">{prev_o:.1f}%</strong> and Click Rate of <strong style="color:#00ff88;">{prev_c:.1f}%</strong>. Pick one and send to the same {n:,} people.</div>', unsafe_allow_html=True)

    COLORS = ["#00c8ff", "#00ff88", "#ffd700", "#c39bd3", "#ff6b6b"]
    ICONS  = ["🔥", "🔮", "🤝", "💙", "📊"]

    if "selected_v" not in st.session_state:
        st.session_state.selected_v = None

    # ── 5 variant cards ────────────────────────────────────────────────────
    for i, v in enumerate(variants):
        color = COLORS[i]
        icon  = ICONS[i]
        is_sel = st.session_state.selected_v == i

        # Card
        sel_class = "vcard-selected" if is_sel else ""
        st.markdown(f"""
        <div class="vcard {sel_class}">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span class="vtag" style="background:{color}20;border:1px solid {color}50;color:{color};">
                    {icon} V{i+1} — {v.get('variant_label','Variant')}
                </span>
                {"<span style='font-size:12px;font-weight:700;color:#00c8ff;'>✓ SELECTED</span>" if is_sel else ""}
            </div>
            <div class="subject-line">📧 {v.get('subject_line','')}</div>
            <div class="reasoning-text">💡 {v.get('strategy_reasoning','')[:200]}...</div>
        </div>
        """, unsafe_allow_html=True)

        # Buttons row: Select + Preview expander
        bc1, bc2 = st.columns([1, 3])
        with bc1:
            btn_label = "✅ Selected" if is_sel else f"Select V{i+1}"
            if st.button(btn_label, key=f"vbtn_{i}", use_container_width=True,
                         type="primary" if is_sel else "secondary"):
                st.session_state.selected_v = i
                st.rerun()
        with bc2:
            with st.expander(f"👁️ Preview full email — V{i+1}"):
                st.markdown(f"**Subject:** `{v.get('subject_line','')}`")
                st.markdown(f'<div class="email-preview">{v.get("email_body","")}</div>', unsafe_allow_html=True)

        st.write("")  # spacer

    # ── Launch section (appears after selection) ───────────────────────────
    st.divider()

    if st.session_state.selected_v is not None:
        idx    = st.session_state.selected_v
        chosen = variants[idx]
        color  = COLORS[idx]

        st.markdown(f"""
        <div style="background:{color}0d;border:2px solid {color}40;border-radius:14px;padding:18px 22px;margin-bottom:20px;">
            <div style="font-size:11px;color:#64748b;text-transform:uppercase;margin-bottom:4px;">You selected</div>
            <div style="font-size:14px;font-weight:700;color:{color};">V{idx+1} — {chosen.get('variant_label','')}</div>
            <div style="font-size:14px;color:#e2e8f0;margin-top:6px;">📧 {chosen.get('subject_line','')}</div>
            <div style="font-size:12px;color:#64748b;margin-top:8px;">
                Will be sent to <strong style="color:#ffd700;">{n:,} people</strong> (same audience as before)
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🕒 Send This Email")

        sc1, sc2, sc3 = st.columns([1, 1, 2])
        with sc1:
            q_btn = st.button("⚡ Send in 1 Minute", type="primary", use_container_width=True, key="vq")
        with sc2:
            v_date = st.date_input("Date", datetime.now(timezone.utc).date(), key="v_date")
        with sc3:
            default_t = (datetime.now(timezone.utc) + timedelta(hours=5, minutes=35)).time()
            v_time = st.time_input("Time (IST)", default_t, key="v_time")

        m_btn = st.button("🚀 Send at Scheduled Time", use_container_width=True, key="vm")

        send_time_str = None
        if q_btn:
            send_time_str = get_send_time_str("quick")
            st.success(f"⚡ Sending at **{send_time_str}** IST")
        elif m_btn:
            send_time_str = get_send_time_str("manual", v_date, v_time)
            st.success(f"🕒 Sending at **{send_time_str}** IST")

        if send_time_str:
            with st.status("Launching optimized campaign...", expanded=True) as status:
                st.write(f"📤 Sending V{idx+1} to **{n:,}** customers at {send_time_str}...")
                exec_result = execution_agent(
                    chosen.get("subject_line"),
                    chosen.get("email_body"),
                    st.session_state.cohort_ids,
                    send_time_str
                )
                if "campaign_id" in exec_result:
                    # Update campaign ID to the NEW one
                    st.session_state.campaign_id    = exec_result["campaign_id"]
                    st.session_state.generated_data = chosen
                    st.session_state.selected_v     = None
                    st.session_state.optimizer_variants = []
                    st.session_state.fetched_open_rate  = 0
                    st.session_state.fetched_click_rate = 0
                    status.update(label="✅ Optimized Campaign Live!", state="complete")
                    st.toast("🚀 Optimized Campaign Launched!")
                    st.balloons()
                    time.sleep(2)
                    # Go directly to comparison page
                    st.session_state.page = "comparison"
                    st.rerun()
                else:
                    status.update(label="❌ Failed.", state="error")
                    st.error(f"Details: {exec_result}")
    else:
        st.info("👆 Select one of the 5 variants above to see the launch options.")

    st.write("")
    if st.button("← Back to Monitor (without sending)", use_container_width=True):
        st.session_state.optimization_count -= 1
        st.session_state.selected_v = None
        st.session_state.page = "monitoring"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — COMPARISON (shown after each optimization round)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "comparison":
    st.markdown('<div class="page-title">📈 Performance Comparison</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">Round #{st.session_state.optimization_count} — Your optimized email was sent to <strong style="color:#ffd700;">{len(st.session_state.cohort_ids):,}</strong> people. Fetch the new results to see the improvement.</div>', unsafe_allow_html=True)

    cid = st.session_state.campaign_id
    n   = len(st.session_state.cohort_ids)
    old_o = st.session_state.prev_open_rate
    old_c = st.session_state.prev_click_rate

    # ── Always show previous rates ─────────────────────────────────────────
    st.markdown(f"""<div style="background:#0b1929;border:1px solid #1a2f4a;border-radius:14px;padding:18px 22px;margin-bottom:20px;">
        <div style="font-size:12px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;">Previous Campaign Rates (Round #{st.session_state.optimization_count - 1 if st.session_state.optimization_count > 0 else 0})</div>
        <div style="display:flex;gap:40px;margin-top:10px;">
            <div><span style="font-size:24px;font-weight:800;font-family:'Syne',sans-serif;color:#ffd700;">{old_o:.1f}%</span> <span style="color:#64748b;font-size:12px;">Open Rate</span></div>
            <div><span style="font-size:24px;font-weight:800;font-family:'Syne',sans-serif;color:#00c8ff;">{old_c:.1f}%</span> <span style="color:#64748b;font-size:12px;">Click Rate</span></div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Fetch new results button ───────────────────────────────────────────
    new_o = st.session_state.new_open_rate
    new_c = st.session_state.new_click_rate
    has_new = new_o > 0

    if not has_new:
        st.markdown("""<div style="background:#00c8ff0d;border:2px dashed #00c8ff40;border-radius:14px;padding:20px;text-align:center;margin-bottom:20px;">
            <div style="font-size:15px;font-weight:600;color:#00c8ff;">📊 Ready to compare?</div>
            <div style="font-size:13px;color:#94a3b8;margin-top:6px;">Click below to fetch the new campaign's open & click rates and see the comparison.</div>
        </div>""", unsafe_allow_html=True)

        if st.button("🔄 Fetch New Campaign Results & Compare", type="primary", use_container_width=True):
            with st.spinner("Fetching report for the new campaign..."):
                report = reporting_agent(cid)
            if "data" in report and len(report["data"]) > 0:
                data   = report["data"]
                total  = len(data)
                opens  = sum(1 for r in data if r.get("EO") == "Y")
                clicks = sum(1 for r in data if r.get("EC") == "Y")
                open_r  = (opens  / total) * 100
                click_r = (clicks / total) * 100

                st.session_state.new_open_rate  = open_r
                st.session_state.new_click_rate = click_r

                # Update history
                existing = next((h for h in st.session_state.campaign_history if h["campaign_id"] == cid), None)
                if existing:
                    existing["open_rate"] = open_r
                    existing["click_rate"] = click_r
                else:
                    st.session_state.campaign_history.append({
                        "round": st.session_state.optimization_count,
                        "campaign_id": cid,
                        "subject": st.session_state.generated_data.get("subject_line", ""),
                        "open_rate": open_r,
                        "click_rate": click_r,
                    })
                st.rerun()
            else:
                st.warning("⏳ No data yet — campaign may still be in queue. Wait a minute and try again.")

    # ── Show full comparison once new rates are fetched ─────────────────────
    if has_new:
        delta_o = new_o - old_o
        delta_c = new_c - old_c

        # Side by side cards
        col_prev, col_arrow, col_new_card = st.columns([2, 1, 2])

        with col_prev:
            st.markdown(f"""<div style="background:#0b1929;border:2px solid #ff6b6b40;border-radius:16px;padding:24px;text-align:center;">
                <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;">Previous Campaign</div>
                <div style="margin-top:16px;">
                    <div style="font-size:11px;color:#64748b;">Open Rate</div>
                    <div style="font-size:32px;font-weight:800;font-family:'Syne',sans-serif;color:#ffd700;">{old_o:.1f}%</div>
                </div>
                <div style="margin-top:12px;">
                    <div style="font-size:11px;color:#64748b;">Click Rate</div>
                    <div style="font-size:32px;font-weight:800;font-family:'Syne',sans-serif;color:#00c8ff;">{old_c:.1f}%</div>
                </div>
            </div>""", unsafe_allow_html=True)

        with col_arrow:
            color_o = "#00ff88" if delta_o >= 0 else "#ff6b6b"
            color_c = "#00ff88" if delta_c >= 0 else "#ff6b6b"
            arrow_o = "▲" if delta_o >= 0 else "▼"
            arrow_c = "▲" if delta_c >= 0 else "▼"
            st.markdown(f"""<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;padding-top:30px;">
                <div style="font-size:11px;color:#64748b;margin-bottom:4px;">Open</div>
                <div style="font-size:28px;font-weight:800;color:{color_o};">{arrow_o} {abs(delta_o):.1f}%</div>
                <div style="margin:20px 0;border-top:1px solid #1a2f4a;width:60px;"></div>
                <div style="font-size:11px;color:#64748b;margin-bottom:4px;">Click</div>
                <div style="font-size:28px;font-weight:800;color:{color_c};">{arrow_c} {abs(delta_c):.1f}%</div>
            </div>""", unsafe_allow_html=True)

        with col_new_card:
            st.markdown(f"""<div style="background:#0b1929;border:2px solid #00ff8840;border-radius:16px;padding:24px;text-align:center;">
                <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.1em;">Optimized (Round #{st.session_state.optimization_count})</div>
                <div style="margin-top:16px;">
                    <div style="font-size:11px;color:#64748b;">Open Rate</div>
                    <div style="font-size:32px;font-weight:800;font-family:'Syne',sans-serif;color:#ffd700;">{new_o:.1f}%</div>
                </div>
                <div style="margin-top:12px;">
                    <div style="font-size:11px;color:#64748b;">Click Rate</div>
                    <div style="font-size:32px;font-weight:800;font-family:'Syne',sans-serif;color:#00c8ff;">{new_c:.1f}%</div>
                </div>
            </div>""", unsafe_allow_html=True)

        # Verdict
        if delta_o > 0 and delta_c > 0:
            vc, vt = "#00ff88", "🏆 Both metrics improved! The optimization worked."
        elif delta_o > 0 or delta_c > 0:
            vc, vt = "#ffd700", "📈 Partial improvement. Consider optimizing again."
        else:
            vc, vt = "#ff6b6b", "⚠️ Metrics didn't improve. Try a different strategy in the next round."

        st.markdown(f"""<div style="background:{vc}12;border:2px solid {vc}44;border-radius:14px;
            padding:16px 22px;margin:24px 0;color:{vc};font-weight:700;font-size:15px;text-align:center;">
            {vt}
        </div>""", unsafe_allow_html=True)

        # ── Re-fetch button (to refresh rates) ─────────────────────────────
        if st.button("🔄 Re-fetch Latest Results", use_container_width=True):
            with st.spinner("Fetching latest report..."):
                report = reporting_agent(cid)
            if "data" in report and len(report["data"]) > 0:
                data   = report["data"]
                total  = len(data)
                opens  = sum(1 for r in data if r.get("EO") == "Y")
                clicks = sum(1 for r in data if r.get("EC") == "Y")
                st.session_state.new_open_rate  = (opens  / total) * 100
                st.session_state.new_click_rate = (clicks / total) * 100
                # Update history
                existing = next((h for h in st.session_state.campaign_history if h["campaign_id"] == cid), None)
                if existing:
                    existing["open_rate"] = st.session_state.new_open_rate
                    existing["click_rate"] = st.session_state.new_click_rate
                st.rerun()
            else:
                st.warning("⏳ No data returned. Try again in a moment.")

        # ── Full history table ─────────────────────────────────────────────
        history = st.session_state.campaign_history
        if len(history) > 1:
            st.divider()
            st.markdown("### 📋 Full Optimization History")

            history_html = """<div style="background:#0b1929;border:1px solid #1a2f4a;border-radius:14px;overflow:hidden;margin:12px 0;">
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead>
                <tr style="background:#0d2035;border-bottom:2px solid #1a2f4a;">
                    <th style="padding:12px 16px;text-align:left;color:#64748b;font-size:11px;text-transform:uppercase;">Round</th>
                    <th style="padding:12px 16px;text-align:left;color:#64748b;font-size:11px;text-transform:uppercase;">Subject Line</th>
                    <th style="padding:12px 16px;text-align:center;color:#64748b;font-size:11px;text-transform:uppercase;">Open Rate</th>
                    <th style="padding:12px 16px;text-align:center;color:#64748b;font-size:11px;text-transform:uppercase;">Click Rate</th>
                    <th style="padding:12px 16px;text-align:center;color:#64748b;font-size:11px;text-transform:uppercase;">Δ Open</th>
                    <th style="padding:12px 16px;text-align:center;color:#64748b;font-size:11px;text-transform:uppercase;">Δ Click</th>
                </tr>
            </thead>
            <tbody>"""

            for i, h in enumerate(history):
                row_bg = "#0d1b2a" if i % 2 == 0 else "#0b1929"
                if i > 0:
                    d_o = h["open_rate"] - history[i-1]["open_rate"]
                    d_c = h["click_rate"] - history[i-1]["click_rate"]
                    co = "#00ff88" if d_o >= 0 else "#ff6b6b"
                    cc = "#00ff88" if d_c >= 0 else "#ff6b6b"
                    delta_o_str = f'<span style="color:{co};font-weight:600;">{"▲" if d_o >= 0 else "▼"} {abs(d_o):.1f}%</span>'
                    delta_c_str = f'<span style="color:{cc};font-weight:600;">{"▲" if d_c >= 0 else "▼"} {abs(d_c):.1f}%</span>'
                else:
                    delta_o_str = '<span style="color:#64748b;">—</span>'
                    delta_c_str = '<span style="color:#64748b;">—</span>'

                round_label = "Initial" if h["round"] == 0 else f'Opt #{h["round"]}'
                subject_preview = h.get("subject", "")[:50] + ("..." if len(h.get("subject", "")) > 50 else "")

                history_html += f"""<tr style="background:{row_bg};border-bottom:1px solid #1a2f4a15;">
                    <td style="padding:10px 16px;color:#c39bd3;font-weight:600;">{round_label}</td>
                    <td style="padding:10px 16px;color:#e2e8f0;">{subject_preview}</td>
                    <td style="padding:10px 16px;text-align:center;color:#ffd700;font-weight:600;">{h["open_rate"]:.1f}%</td>
                    <td style="padding:10px 16px;text-align:center;color:#00c8ff;font-weight:600;">{h["click_rate"]:.1f}%</td>
                    <td style="padding:10px 16px;text-align:center;">{delta_o_str}</td>
                    <td style="padding:10px 16px;text-align:center;">{delta_c_str}</td>
                </tr>"""

            history_html += "</tbody></table></div>"
            st.markdown(history_html, unsafe_allow_html=True)

        # ── Action buttons — Optimize Again or Done ────────────────────────
        st.divider()
        st.markdown("### 🔄 What's Next?")

        col_opt, col_done = st.columns(2)

        with col_opt:
            st.markdown(f"""<div style="background:#c39bd310;border:1px solid #c39bd340;border-radius:12px;padding:16px;margin-bottom:12px;">
                <div style="font-size:13px;color:#94a3b8;">
                    Not satisfied? Generate <strong style="color:#c39bd3;">5 new optimized variants</strong>
                    and try again with the same <strong style="color:#ffd700;">{n:,}</strong> audience.
                </div>
            </div>""", unsafe_allow_html=True)

            notes = st.text_area("Manager's guidance (optional):",
                placeholder="e.g. 'Try shorter subject lines', 'Focus on urgency'",
                height=70, key="comp_notes")

            if st.button("⚡ Optimize Again → Generate 5 New Emails", type="primary", use_container_width=True):
                with st.spinner("AI generating 5 new variants... (~15 sec)"):
                    variants = optimizer_agent_bulk(
                        brief=st.session_state.brief,
                        original_subject=st.session_state.generated_data.get("subject_line", ""),
                        open_rate=st.session_state.new_open_rate,
                        click_rate=st.session_state.new_click_rate,
                        human_guidance=notes
                    )
                if variants:
                    st.session_state.prev_open_rate = st.session_state.new_open_rate
                    st.session_state.prev_click_rate = st.session_state.new_click_rate
                    st.session_state.new_open_rate = 0
                    st.session_state.new_click_rate = 0
                    st.session_state.optimizer_variants = variants
                    st.session_state.optimization_count += 1
                    st.session_state.page = "pick_variant"
                    st.rerun()
                else:
                    st.error("Failed to generate variants. Try again.")

        with col_done:
            st.markdown("""<div style="background:#00ff8810;border:1px solid #00ff8840;border-radius:12px;padding:16px;margin-bottom:12px;">
                <div style="font-size:13px;color:#94a3b8;">
                    Happy with the results? Go back to monitoring or start fresh.
                </div>
            </div>""", unsafe_allow_html=True)

            st.write("")
            if st.button("📊 Back to Monitoring", use_container_width=True):
                st.session_state.fetched_open_rate  = st.session_state.new_open_rate
                st.session_state.fetched_click_rate = st.session_state.new_click_rate
                st.session_state.prev_open_rate = st.session_state.new_open_rate
                st.session_state.prev_click_rate = st.session_state.new_click_rate
                st.session_state.new_open_rate = 0
                st.session_state.new_click_rate = 0
                st.session_state.page = "monitoring"
                st.rerun()

            if st.button("➕ Start New Campaign", use_container_width=True):
                st.session_state.clear()
                st.rerun()
