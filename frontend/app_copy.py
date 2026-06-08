import streamlit as st
import requests
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import math
import cmath
import base64
from geo_config import (
    _validate_geom, geo_cfg, get_mesh, geo_trace_checker,
    BasicGeometry, Block, Ellipsoid, Sphere, Cylinder, Cone, Wedge, Prism
)
from src_config import (
    src_cfg, src_trace_checker, Source, GaussianSource, 
    Gaussian_srct, EigenmodeSource
)
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
if 'dialog_toast_msg' not in st.session_state: st.session_state.dialog_toast_msg = None

if st.session_state.dialog_toast_msg:
    txt, icon, dur = st.session_state.dialog_toast_msg
    st.toast(txt, icon=icon, duration=dur)
    st.session_state.dialog_toast_msg = None

# 初始化测试数据（仅执行一次）
if not st.session_state.sources:
    pass
    # 定义一个符合 Meep 规范的测试 amp_func (平面波)
    # k_vec = np.array([1.0, 1.0, 1.0]) # 波矢方向
    # def test_pw_amp(x):
    #     # x 是相对于光源中心 (center) 的坐标
    #     # 模拟强度随中心向边缘衰减 (Gaussian) + 线性相位
    #     r_sq = np.sum(x**2)
    #     intensity = math.exp(-r_sq / 10.0) 
    #     phase = np.dot(k_vec, x)
    #     return intensity * cmath.exp(1j * phase)

    # st.session_state.sources.append(
    #     Source(
    #         name='test_pol',
    #         srct=Gaussian_srct(wavelength=1.55, fwidth=0.1),
    #         color='yellow',
    #         component='Ex',
    #         opacity=0.5,
    #         center=[0, 0, 0],
    #         size=[5, 5, 0],
    #         amplitude=1.0,
    #         amp_func=test_pw_amp,
    #         amp_func_file=None,
    #     )
    # )

    # # 添加测试 Eigenmode Source
    # st.session_state.sources.append(
    #     EigenmodeSource(
    #         name='test_eigenmode',
    #         color='#66CCFF',
    #         srct=Gaussian_srct(wavelength=1.55, fwidth=0.1),
    #         component='All',
    #         opacity=0.6,
    #         center=[2, 0, 0],
    #         size=[0, 3, 3],
    #         direction='X',
    #         eig_band=1,
    #         eig_kpoint=[1, 1, 0],
    #         eig_lattice_size=[0, 5, 5],
    #         eig_lattice_center=[2, 0, 0],
    #         amplitude=1.0,
    #     )
    # )
    # # 添加测试 Gaussian Source
    # st.session_state.sources.append(
    #     GaussianSource(
    #         name='test_gaussian_beam',
    #         color='#00FF88',
    #         srct=Gaussian_srct(wavelength=1.0, fwidth=0.2),
    #         opacity=0.4,
    #         center=[0, 0, 2],
    #         size=[0, 6, 6],  # 位于 Y-Z 平面的面光源
    #         beam_x0=[0, 0, 0],       # 焦点在原点
    #         beam_kdir=[1, 1, 0], # 斜向传播
    #         beam_w0=0.2,             # 腰径
    #         beam_E0=[0, 2, 2],       # 偏振沿 Z
    #         amplitude=1.0,
    #     )
    # )






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
    st.divider(width='stretch')

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

    # 绘制光源
    for source in st.session_state.sources:
        src_traces = src_trace_checker(source)
        if isinstance(src_traces, list):
            fig.add_traces(src_traces)
        else:
            fig.add_trace(src_traces)

    fig.update_layout(
        scene=dict(
            xaxis_title='X (um)',
            yaxis_title='Y (um)',
            zaxis_title='Z (um)',
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.8, y=1.8, z=1.2),
                projection=dict(type='orthographic')
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
