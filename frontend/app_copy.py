import streamlit as st
import requests
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import base64
from geo_config import (
    _validate_geom, geo_cfg, get_mesh, geo_trace_checker,
    BasicGeometry, Block, Ellipsoid, Sphere, Cylinder, Cone, Wedge, Prism
)
from src_config import src_cfg
from utils import clear_temp, card_widget


st.set_page_config(layout="wide", page_title="Meep Web GUI")

st.markdown("""
    <style>
        [data-testid="stSidebarHeader"] {
            padding-top: 0.2rem !important;
            padding-bottom: 0rem !important;
            min-height: auto !important;
        }

        /* 2. 移除用户内容区域顶部的填充 */
        [data-testid="stSidebarUserContent"] {
            padding-top: 0rem !important;
        }

        /* 2. 核心修复：消除标记组件占用的物理空间 */
        /* 找到包含我们标记的 Streamlit 基础容器，强制高度为0并隐藏外边距 */
        div[data-testid="stElementContainer"]:has(.active-marker) {
            display: none !important;
            height: 0px !important;
            margin: 0px !important;
            padding: 0px !important;
        }

        /* 3. 减少按钮之间的纵向间距 */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0.2rem !important; 
        }

        /* 4. 统一按钮基础样式（全局生效） */
        div.stButton > button {
            width: 100%;
            border-radius: 8px;
            height: 1rem;
            background-color: #FF8585 !important;
            color: white !important;
            border: none;
            text-align: left;
            padding-left: 0.5rem;
            transition: all 0.2s ease;
        }

        /* 5. 高亮逻辑：加粗当前侧边栏按钮文字 */
        [data-testid="stVerticalBlock"] > div:has(.active-marker) + div [data-testid="stButton"] button {
            font-weight: bold;
        }

        /* Hover & Active 效果 */
        div.stButton > button:hover {
            background-color: #FF4B4B !important;
            transform: translateX(5px);
        }
        div.stButton > button:active {
            transform: scale(0.95) !important;
        }
    </style>
    """, unsafe_allow_html=True)
# --- 状态初始化 ---
if "geoms" not in st.session_state: st.session_state.geoms = []
if "sources" not in st.session_state: st.session_state.sources = []
if "monitors" not in st.session_state: st.session_state.monitors = []
if "results" not in st.session_state: st.session_state.results = None
if "active_page" not in st.session_state: st.session_state.active_page = "simulation"

# --- UI 布局 ---
#st.title("🔬 Meep Web Workspace")

with st.sidebar:
    menu_items = {
            "simulation": 0,
            "geometry": 0,
            "source": 1,
            "monitor": 1,
        }
    col_list = st.columns(2)
    for label, col in menu_items.items():
        button_label = f"{label.capitalize()}"

        with col_list[col]:
            if st.session_state.active_page == label:
                st.markdown('<span class="active-marker"></span>', unsafe_allow_html=True)

                
            # 按钮统一生成
            if st.button(button_label, key=f"btn_{label}", use_container_width=True):
                st.session_state.active_page = label
                st.rerun()

    if st.session_state.active_page == "simulation":
        xyz = st.expander("Space setup", expanded=True)

        x,y,z = xyz.columns(3)
        sx = x.number_input("Size",label_visibility ='visible',placeholder="X span")
        sy = y.number_input(" ",label_visibility ='hidden',placeholder="Y span")
        sz = z.number_input(" ",label_visibility ='hidden',placeholder="Z span")
        res = xyz.number_input("Simulation resolution", value=10,key='g_sim_res')
        bg_mat = xyz.number_input("Background material", value=1.0)

        BCs = st.expander("Boundary conditions", expanded=False)
        BCs.write("Boundary conditions settings will go here.")

        simu_setup = st.expander("Simulation setup", expanded=False)
        sim_until = simu_setup.selectbox("Termination unitl", ["Time / ms", "Si", "SiO2", "Ag", "Au"])


    if st.session_state.active_page == "geometry":
        if st.button("Add geometry", type="primary", width='stretch'):
            geo_cfg()

        
        with st.expander("Geometry list", expanded=True):
            if st.session_state.geoms:
                for idx, geom in enumerate(st.session_state.geoms):
                    card_widget(geom, obj_type='geometry', idx=idx, edit_callback=geo_cfg, top=idx == 0, bottom=idx == len(st.session_state.geoms) - 1)
            else:
                st.info("No geometries added yet.")

    if st.session_state.active_page == "source":
        if st.button("Add source",type="primary", width='stretch'):
            src_cfg()

        with st.expander("Source list", expanded=True):
            if st.session_state.sources:
                for idx, source in enumerate(st.session_state.sources):
                    card_widget(source, obj_type='source', idx=idx, edit_callback=src_cfg, top=idx == 0, bottom=idx == len(st.session_state.sources) - 1)
            else:
                st.info("No sources added yet.")



tab_view, tab_res = st.tabs(["3D viewer", "Results"])
with tab_view:
    fig = go.Figure()
    for geom in st.session_state.geoms:
        traces = geo_trace_checker(geom)
        if isinstance(traces, list):
            fig.add_traces(traces)
        else:
            fig.add_trace(traces)

    fig.update_layout(
        scene=dict(
            xaxis_title='X (um)',
            yaxis_title='Y (um)',
            zaxis_title='Z (um)',
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.8, y=1.8, z=1.2)
            )
        ),
        margin=dict(l=0, r=0, b=0, t=60),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    st.plotly_chart(fig, width='stretch', height='stretch')



# 4. 结果渲染
with tab_res:
    if st.session_state.results and st.session_state.results["status"] == "success":
        res_data = st.session_state.results
        layer = st.selectbox("选择层", list(res_data["fields"].keys()))
        
        raw_b64 = res_data["fields"][layer]
        arr = np.frombuffer(base64.b64decode(raw_b64), dtype=np.float32).reshape(tuple(res_data["shape"]))
        
        X, Y, Z = get_mesh(sx, sy, sz, *arr.shape)
        v_max = np.max(np.abs(arr))
        
        fig = go.Figure(data=go.Volume(
            x=X, y=Y, z=Z, value=arr.flatten(),
            isomin=-v_max, isomax=v_max, opacity=0.1, surface_count=8, colorscale='RdBu'
        ))
        st.plotly_chart(fig, use_container_width=True)
    elif st.session_state.results:
        st.error(st.session_state.results.get("trace"))
