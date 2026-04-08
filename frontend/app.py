import streamlit as st
import requests
import numpy as np
import plotly.graph_objects as go
import base64
from streamlit_sortables import sort_items

st.set_page_config(layout="wide", page_title="Meep Web GUI")

# --- 状态初始化 ---
if "geoms" not in st.session_state: st.session_state.geoms = []
if "sources" not in st.session_state: st.session_state.sources = []
if "results" not in st.session_state: st.session_state.results = None

# --- 工具函数 ---
@st.cache_data
def get_mesh(sx, sy, sz, nx, ny, nz):
    x, y, z = np.meshgrid(np.linspace(-sx/2, sx/2, nx), 
                         np.linspace(-sy/2, sy/2, ny), 
                         np.linspace(-sz/2, sz/2, nz), indexing='ij')
    return x.flatten(), y.flatten(), z.flatten()

# --- UI 布局 ---
st.title("🔬 Meep 高级仿真工作站")
tab_cfg, tab_geo, tab_src, tab_res = st.tabs(["⚙️ 设置", "💎 几何", "🔦 光源", "📊 结果渲染"])

# 1. 仿真设置
with tab_cfg:
    c1, c2, c3 = st.columns(3)
    box1 = c1.container(border=True)
    box1_title = box1.subheader("📐 空间设置" )
    sx = box1.number_input("Size X", value=5.0)
    sy = box1.number_input("Size Y", value=5.0)
    sz = box1.number_input("Size Z", value=5.0)
    res = box1.number_input("分辨率", value=10)
    bg_eps = box1.number_input("背景介电常数", value=1.0)

    box2 = c2.container(border=True)
    box2_title = box2.subheader("Boundary conditions")

    box3 = c3.container(border=True)
    box3_title = box3.subheader("Simulation Setup")
    sim_until = box3.selectbox("Termination unitl", ["Time / ms", "Si", "SiO2", "Ag", "Au"])
    if st.button("🚀 开启计算", type="primary", use_container_width=True):
        payload = {
            "sx": sx, "sy": sy, "sz": sz, "res": res, "bg_eps": bg_eps, "until": sim_until,
            "geoms": st.session_state.geoms, "sources": st.session_state.sources
        }
        with st.spinner("WSL 计算中..."):
            r = requests.post("http://127.0.0.1:8000/simulate_full", json=payload)
            st.session_state.results = r.json()

# 2. 几何体管理
with tab_geo:
    with st.expander("➕ 添加几何体"):
        g_type = st.selectbox("类型", ["Block", "Sphere"])
        mat = st.selectbox("材料", ["手动输入 (Epsilon)", "Si", "SiO2", "Ag", "Au"])
        eps = st.number_input("自定义 Epsilon", value=2.0) if mat == "手动输入 (Epsilon)" else 1.0
        pos = (st.number_input("X"), st.number_input("Y"), st.number_input("Z"))
        if g_type == "Block":
            s_val = (st.number_input("SX", value=1.0), st.number_input("SY", value=1.0), st.number_input("SZ", value=1.0))
            params = {"size": s_val}
        else:
            params = {"radius": st.number_input("R", value=1.0)}
        
        if st.button("确认添加"):
            st.session_state.geoms.append({"type": g_type, "material": mat, "eps": eps, "center": pos, **params})
            st.rerun()

    if st.session_state.geoms:
        st.subheader("🖱️ 拖拽排序 (下方为覆盖层)")
        items = [f"{i}: {g['type']} ({g['material']}) at {g['center']}" for i, g in enumerate(st.session_state.geoms)]
        sorted_items = sort_items(items)
        if sorted_items != items:
            new_list = [st.session_state.geoms[int(s.split(":")[0])] for s in sorted_items]
            st.session_state.geoms = new_list
            st.rerun()

# 3. 光源管理
with tab_src:
    with st.expander("➕ 添加光源"):
        comp = st.selectbox("分量", ["Ez", "Ex", "Ey"])
        freq = st.number_input("中心频率", value=1.0)
        fwidth = st.number_input("带宽 (fwidth)", value=0.1)
        s_pos = (st.number_input("Src X"), st.number_input("Src Y"), st.number_input("Src Z"))
        if st.button("添加光源"):
            st.session_state.sources.append({"component": comp, "freq": freq, "fwidth": fwidth, "center": s_pos})
            st.rerun()
    st.write(st.session_state.sources)

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