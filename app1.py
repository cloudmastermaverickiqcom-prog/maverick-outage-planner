import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="MaverickIQ | Fleet Command", page_icon="⚡")

# --- CUSTOM CSS (Layout & Hierarchy) ---
st.markdown("""
<style>
    /* 1. FIX THE "BLACK BAR" ISSUE: Push content down */
    .block-container { 
        padding-top: 4rem; 
        padding-bottom: 2rem; 
    }
    
    /* GLOBAL TEXT COLORS */
    h1, h2, h3, h4, p, span, div { color: #F8FAFC; }
    .metric-label { color: #94a3b8 !important; }
    
    /* --- CARD STYLES --- */
    .card-container {
        background-color: #1e293b;
        border-radius: 10px;
        border: 1px solid #334155;
        padding: 15px;
        height: 100%;
        transition: all 0.2s;
    }
    .card-container:hover {
        border-color: #3B82F6;
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    
    /* Large Card (Outages) */
    .card-large {
        border-top: 5px solid #d97706; /* Default Amber */
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    }
    
    /* Compact Card (Running) */
    .card-small {
        border-top: 4px solid #059669; /* Green */
        text-align: center;
    }

    /* BADGES */
    .badge { padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; }
    .badge-planned { background: rgba(217, 119, 6, 0.2); color: #fbbf24; border: 1px solid #d97706; }
    .badge-unplanned { background: rgba(220, 38, 38, 0.2); color: #f87171; border: 1px solid #dc2626; }
    .badge-running { background: rgba(5, 150, 105, 0.2); color: #34d399; border: 1px solid #059669; }

    /* --- NAVIGATION BAR STYLING --- */
    div[data-testid="stButton"] button {
        width: 100%;
        border-radius: 6px;
        font-weight: bold;
        border: 1px solid #475569;
        color: #f1f5f9;
        background-color: #334155;
        transition: background-color 0.2s;
    }
    div[data-testid="stButton"] button:hover {
        border-color: #3B82F6;
        color: white;
        background-color: #2563EB;
    }
</style>
""", unsafe_allow_html=True)

# --- NAVIGATION LOGIC ---
if 'view' not in st.session_state: st.session_state.view = 'Fleet'
if 'selected_site' not in st.session_state: st.session_state.selected_site = None

def navigate(view, site=None):
    st.session_state.view = view
    st.session_state.selected_site = site

# --- DATA GENERATION ---
@st.cache_data
def get_fleet_data():
    return pd.DataFrame([
        # PRIORITY SITES (OUTAGES)
        {"id": "SITE-01", "name": "North Substation", "region": "North", "type": "Combined Cycle", "cap": "650MW", "status": "Planned Outage", "budget": 6487261, "spend": 657375, "progress": 32, "alert": "Rotor Lift"},
        {"id": "SITE-02", "name": "South Gen Unit 1", "region": "South", "type": "Gas Turbine", "cap": "220MW", "status": "Unplanned Maintenance", "budget": 1200000, "spend": 980000, "progress": 85, "alert": "GSU Failure"},
        # RUNNING SITES
        {"id": "SITE-03", "name": "Metro Hydro", "region": "Metro", "type": "Hydro", "cap": "450MW", "status": "Running", "budget": 3.5e6, "spend": 1.2e6},
        {"id": "SITE-04", "name": "Rural Solar", "region": "Rural", "type": "Solar", "cap": "150MW", "status": "Running", "budget": 0.8e6, "spend": 0.45e6},
        {"id": "SITE-05", "name": "East Peaker", "region": "East", "type": "Gas", "cap": "180MW", "status": "Running", "budget": 2.1e6, "spend": 1.8e6},
        {"id": "SITE-06", "name": "West Valley", "region": "West", "type": "CCGT", "cap": "600MW", "status": "Running", "budget": 5.1e6, "spend": 2.1e6},
        {"id": "SITE-07", "name": "Coast Wind", "region": "Coast", "type": "Wind", "cap": "300MW", "status": "Running", "budget": 1.5e6, "spend": 0.6e6}
    ])

@st.cache_data
def get_long_term_schedule():
    """Generates a 2-year lookahead for all 7 sites."""
    schedule = []
    base_date = datetime.now()
    
    # Define Outage Windows (Seasons)
    seasons = [
        {"name": "Fall 2026", "start": base_date + timedelta(days=240)}, # Sep 2026
        {"name": "Spring 2027", "start": base_date + timedelta(days=420)}, # Mar 2027
        {"name": "Fall 2027", "start": base_date + timedelta(days=600)}, # Sep 2027
    ]
    
    fleet = get_fleet_data()
    
    for _, site in fleet.iterrows():
        # 1. Handle CURRENT Status
        if site['status'] == 'Planned Outage':
            # Current active outage
            schedule.append({
                "Site": site['name'],
                "Start": base_date - timedelta(days=15),
                "Finish": base_date + timedelta(days=30),
                "Type": "Active Planned",
                "Duration": "45 Days"
            })
        elif site['status'] == 'Unplanned Maintenance':
             # Current forced outage
             schedule.append({
                "Site": site['name'],
                "Start": base_date - timedelta(days=2),
                "Finish": base_date + timedelta(days=5),
                "Type": "Active Unplanned",
                "Duration": "7 Days"
            })
        
        # 2. Generate FUTURE Outages for EVERYONE
        # Pick a random season for the next major outage
        future_season = random.choice(seasons)
        duration_days = random.choice([28, 45, 120]) # Minor, Standard, Major
        outage_type = "Major Overhaul" if duration_days == 120 else "Planned Maintenance"
        
        # Stagger starts slightly so they don't all align perfectly
        stagger = random.randint(-15, 15)
        start_date = future_season['start'] + timedelta(days=stagger)
        
        schedule.append({
            "Site": site['name'],
            "Start": start_date,
            "Finish": start_date + timedelta(days=duration_days),
            "Type": "Future Planned",
            "Duration": f"{duration_days} Days ({outage_type})"
        })
        
    return pd.DataFrame(schedule)

@st.cache_data
def get_planned_projects():
    projects = []
    systems = {
        'Gas Turbine': ['Combustion', 'Compressor', 'Turbine', 'Rotor'],
        'Steam Turbine': ['HP Section', 'IP/LP Section', 'Valves', 'Bearings'],
        'HRSG': ['Pressure Parts', 'Duct Burners', 'SCR/CO', 'Casing'],
        'Generator': ['Stator', 'Rotor', 'Exciter'],
        'BOP': ['Cooling Water', 'Compressed Air', 'Fuel Gas']
    }
    
    for i in range(1, 86):
        sys = random.choice(list(systems.keys()))
        sub = random.choice(systems[sys])
        est_labor = random.randint(20000, 100000)
        est_mat = random.randint(10000, 150000)
        status = random.choice(['Not Started', 'In Progress', 'In Progress', 'Completed'])
        
        pct = 1.0 if status == 'Completed' else (random.uniform(0.1, 0.9) if status == 'In Progress' else 0.0)
            
        projects.append({
            "id": f"PRJ-{1000+i}",
            "name": f"{sub} Task {i}",
            "full_name": f"PRJ-{1000+i}: {sub} Task {i}",
            "system": sys,
            "subsystem": sub,
            "status": status,
            "critical": random.choice([True, False, False]),
            "budget_labor": est_labor,
            "actual_labor": est_labor * pct * random.uniform(0.95, 1.05),
            "budget_mat": est_mat,
            "actual_mat": est_mat * pct * random.uniform(0.9, 1.1),
            "start_offset": random.randint(0, 40),
            "duration": random.randint(5, 15)
        })
        
    df = pd.DataFrame(projects)
    base = datetime.now()
    df['Start Date'] = df['start_offset'].apply(lambda x: base + timedelta(days=x))
    df['End Date'] = df.apply(lambda row: row['Start Date'] + timedelta(days=row['duration']), axis=1)
    return df

df_fleet = get_fleet_data()
df_schedule = get_long_term_schedule()
df_projects = get_planned_projects()

# --- FUNCTION FOR STATUS COLORING ---
def color_status(val):
    color = 'grey'
    if val == 'Completed':
        color = '#064e3b' # Dark Green
    elif val == 'In Progress':
        color = '#78350f' # Dark Amber
    elif val == 'Not Started':
        color = '#7f1d1d' # Dark Red
    return f'background-color: {color}; color: white; border-radius: 4px; padding: 4px;'

# --- VIEW 1: FLEET COMMAND ---
if st.session_state.view == 'Fleet':
    st.markdown("## ⚡ MaverickIQ | Fleet Command")
    
    # 1. PRIORITY ROW (Outages = Large Cards)
    st.markdown("### ⚠️ Active Attention Required")
    col1, col2 = st.columns(2)
    outage_sites = df_fleet[df_fleet['status'] != 'Running']
    
    for i, (index, row) in enumerate(outage_sites.iterrows()):
        target_col = col1 if i == 0 else col2
        border_color = "#dc2626" if "Unplanned" in row['status'] else "#d97706"
        badge_cls = "badge-unplanned" if "Unplanned" in row['status'] else "badge-planned"
        
        with target_col:
            st.markdown(f"""
            <div class="card-container card-large" style="border-top-color: {border_color};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0;">{row['name']}</h3>
                    <span class="badge {badge_cls}">{row['status']}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-top:15px;">
                    <div><p style="margin:0; color:#94a3b8; font-size:0.9rem;">Type</p><p style="margin:0; font-weight:bold;">{row['type']}</p></div>
                    <div><p style="margin:0; color:#94a3b8; font-size:0.9rem;">Alert</p><p style="margin:0; font-weight:bold; color:{border_color};">{row['alert']}</p></div>
                    <div style="text-align:right;"><p style="margin:0; color:#94a3b8; font-size:0.9rem;">Budget</p><p style="margin:0; font-weight:bold;">${row['spend']/1000:,.0f}k / {row['budget']/1000:,.0f}k</p></div>
                </div>
                <div style="margin-top:15px; background:rgba(255,255,255,0.1); height:8px; border-radius:4px;">
                    <div style="width:{row['spend']/row['budget']*100}%; background:{border_color}; height:100%; border-radius:4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Manage {row['name']} →", key=f"btn_{row['id']}", use_container_width=True):
                navigate('Detail', row.to_dict())
                st.rerun()

    # 2. RUNNING ROW
    st.markdown("### 🟢 Operational Fleet")
    cols = st.columns(5)
    running_sites = df_fleet[df_fleet['status'] == 'Running']
    for i, (index, row) in enumerate(running_sites.iterrows()):
        with cols[i]:
            st.markdown(f"""
            <div class="card-container card-small">
                <h4 style="margin:0; font-size:1rem;">{row['name']}</h4>
                <p style="color:#94a3b8; font-size:0.8rem; margin-bottom:5px;">{row['region']}</p>
                <span class="badge badge-running">RUNNING</span>
                <hr style="border-color:#334155; margin:10px 0;">
                <p style="font-size:0.8rem; margin:0;">Output: <strong>{row['cap']}</strong></p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("View", key=f"btn_{row['id']}", use_container_width=True):
                navigate('Detail', row.to_dict())
                st.rerun()

    # 3. 2-YEAR LOOKAHEAD (NEW)
    st.markdown("---")
    st.markdown("### 🗓️ 2-Year Fleet Schedule (2026-2027)")
    
    # Define Color Map for Schedule
    color_map = {
        "Active Planned": "#d97706",    # Amber
        "Active Unplanned": "#dc2626",  # Red
        "Future Planned": "#059669"     # Green
    }
    
    fig_schedule = px.timeline(
        df_schedule, 
        x_start="Start", 
        x_end="Finish", 
        y="Site", 
        color="Type", 
        color_discrete_map=color_map,
        hover_data=["Duration"],
        template="plotly_dark",
        height=400
    )
    fig_schedule.update_yaxes(autorange="reversed", title="") # List top to bottom
    fig_schedule.update_xaxes(title="Timeline")
    
    # Add 'Today' line
    fig_schedule.add_vline(x=datetime.now().timestamp() * 1000, line_width=2, line_dash="dash", line_color="white", annotation_text="Today")
    
    st.plotly_chart(fig_schedule, use_container_width=True)

# --- VIEW 2: SITE DETAIL ---
elif st.session_state.view == 'Detail':
    site = st.session_state.selected_site
    
    # --- NAVIGATION BAR ---
    nav_col1, nav_col2 = st.columns([1, 6])
    with nav_col1:
        if st.button("⬅ HOME"):
            navigate('Fleet')
            st.rerun()
    with nav_col2:
        st.markdown(f"## {site['name']} Dashboard")

    st.markdown("---")

    if "Planned" in site['status']:
        t1, t2, t3, t4 = st.tabs(["📊 Overview", "🏭 Asset Drill-Down", "💰 Financials", "🗓️ Schedule"])
        
        with t1:
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Maverick Score", "88/100")
            k2.metric("Completion", "32%")
            k3.metric("Spend", f"${site['spend']:,.0f}")
            k4.metric("Risk", "Low")
            
            c1, c2 = st.columns(2)
            with c1:
                grp = df_projects.groupby('system')[['actual_labor', 'actual_mat']].sum().reset_index()
                fig = px.bar(grp, x='system', y=['actual_labor', 'actual_mat'], template='plotly_dark')
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.dataframe(df_projects['status'].value_counts(), use_container_width=True)
                
        with t2:
            st.markdown("### 🔍 Asset Hierarchy Manager")
            
            f1, f2, f3 = st.columns([1, 1, 2])
            with f1:
                sel_sys = st.selectbox("1. Select System", df_projects['system'].unique())
            with f2:
                avail_sub = df_projects[df_projects['system'] == sel_sys]['subsystem'].unique()
                sel_sub = st.selectbox("2. Select Sub-System", avail_sub)
            
            # Filter Data
            subset = df_projects[(df_projects['system'] == sel_sys) & (df_projects['subsystem'] == sel_sub)]
            
            with f3:
                if not subset.empty:
                    pie_data = subset['status'].value_counts().reset_index()
                    pie_data.columns = ['Status', 'Count']
                    fig_pie = px.pie(pie_data, values='Count', names='Status', color='Status',
                                     color_discrete_map={'Completed':'#059669', 'In Progress':'#d97706', 'Not Started':'#dc2626'},
                                     hole=0.5)
                    fig_pie.update_layout(template="plotly_dark", margin=dict(t=0, b=0, l=0, r=0), height=100, showlegend=False)
                    fig_pie.update_traces(textposition='inside', textinfo='value')
                    
                    pc1, pc2 = st.columns([1, 2])
                    with pc1: st.plotly_chart(fig_pie, use_container_width=True)
                    with pc2: st.caption(f"**{sel_sub}** Breakdown"); st.caption(f"Total Tasks: {len(subset)}")

            st.divider()

            if subset.empty:
                st.warning("No projects found.")
            else:
                for _, row in subset.iterrows():
                    with st.expander(f"{row['id']}: {row['name']} ({row['status']})"):
                        xc1, xc2, xc3 = st.columns(3)
                        xc1.markdown(f"**Critical Path:** {'🔴 Yes' if row['critical'] else 'No'}")
                        l_pct = row['actual_labor'] / row['budget_labor'] if row['budget_labor'] > 0 else 0
                        xc2.caption("Labor Budget"); xc2.progress(min(l_pct, 1.0)); xc2.text(f"${row['actual_labor']:,.0f} / ${row['budget_labor']:,.0f}")
                        m_pct = row['actual_mat'] / row['budget_mat'] if row['budget_mat'] > 0 else 0
                        xc3.caption("Material Budget"); xc3.progress(min(m_pct, 1.0)); xc3.text(f"${row['actual_mat']:,.0f} / ${row['budget_mat']:,.0f}")

        with t3:
            st.markdown("### 💰 Cost Control Tower")
            fc1, fc2 = st.columns([1, 3])
            with fc1: status_filter = st.selectbox("Filter by Status", ["All", "In Progress", "Completed", "Not Started"])
            
            fin_view = df_projects.copy()
            fin_view['Total Budget'] = fin_view['budget_labor'] + fin_view['budget_mat']
            fin_view['Total Actual'] = fin_view['actual_labor'] + fin_view['actual_mat']
            fin_view['Variance'] = fin_view['Total Budget'] - fin_view['Total Actual']
            
            if status_filter != "All": fin_view = fin_view[fin_view['status'] == status_filter]
            
            st.dataframe(
                fin_view[['full_name', 'status', 'Total Budget', 'Total Actual', 'Variance']].style.map(color_status, subset=['status']),
                column_config={"full_name": "Project Name", "Total Budget": st.column_config.NumberColumn(format="$%d"), "Total Actual": st.column_config.NumberColumn(format="$%d"), "Variance": st.column_config.NumberColumn(format="$%d")},
                use_container_width=True, hide_index=True
            )

        with t4:
            fig_gantt = px.timeline(df_projects.sort_values('Start Date'), x_start="Start Date", x_end="End Date", y="name", color="system", template="plotly_dark")
            st.plotly_chart(fig_gantt, use_container_width=True)

    elif "Unplanned" in site['status']:
        st.error(f"🚨 ACTIVE INCIDENT: {site['alert']}")
        c1, c2 = st.columns(2)
        with c1: st.metric("Estimated Loss", "$45,000 / hr"); st.metric("Time Offline", "14h 30m")
        with c2: st.subheader("Recovery Actions"); st.checkbox("Safety Lockdown", value=True); st.checkbox("Damage Assessment", value=True)
            
    else:
        st.success("✅ Operational - Nominal Status")
        st.line_chart([random.randint(90,100) for _ in range(24)])