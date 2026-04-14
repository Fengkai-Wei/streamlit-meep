import streamlit as st
import requests
import numpy as np
import plotly.graph_objects as go
import base64
from streamlit_sortables import sort_items
from mat import MATERIAL_KEYS
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

        /* 4. 统一按钮基础样式 */
        div.stButton > button {
            width: 100%;
            border-radius: 8px;
            height: 1rem;
            background-color: transparent;
            color: #31333F;
            border: none;
            text-align: left;
            padding-left: 0.5rem;
            transition: all 0.2s ease;
        }

        /* 5. 高亮逻辑：利用标记找到下一个相邻的按钮容器 */
        [data-testid="stVerticalBlock"] > div:has(.active-marker) + div [data-testid="stButton"] button {
            background-color: #FF4B4B !important;
            color: white !important;
            font-weight: bold;
        }

        /* Hover & Active 效果 */
        div.stButton > button:hover {
            background-color: #f0f2f6 !important;
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

# --- 工具函数 ---
@st.cache_data
def get_mesh(sx, sy, sz, nx, ny, nz):
    x, y, z = np.meshgrid(np.linspace(-sx/2, sx/2, nx), 
                         np.linspace(-sy/2, sy/2, ny), 
                         np.linspace(-sz/2, sz/2, nz), indexing='ij')
    return x.flatten(), y.flatten(), z.flatten()


@st.dialog("Source configuration",width = 'medium')
def src_cfg():
    src_left,src_right = st.columns(2)
    with src_left:
        st.write("General parameters")
        temp_src_type = st.selectbox("Type", ["Custom", "Eigenmode","Gaussian"],index=None)
        temp_src_comp = st.selectbox("Component", ["Ex", "Ey", "Ez", "Hx", "Hy", "Hz"],index=None,key='t_src_comp')
        x,y,z = st.columns(3)
        temp_src_center =[None]*3
        temp_src_center[0]= x.number_input("Center",label_visibility ='visible',placeholder="X",value=None)
        temp_src_center[1]= y.number_input("Center",label_visibility ='hidden',placeholder="Y",value=None)
        temp_src_center[2]= z.number_input("Center",label_visibility ='hidden',placeholder="Z",value=None)
        x1,y1,z1 = st.columns(3)
        temp_src_size = [None]*3
        temp_src_size[0]= x1.number_input("Size",label_visibility ='visible',placeholder="X",value=None)
        temp_src_size[1]= y1.number_input("Size",label_visibility ='hidden',placeholder="Y",value=None)
        temp_src_size[2]= z1.number_input("Size",label_visibility ='hidden',placeholder="Z",value=None)
        with st.expander("Amplitude parameters"):
            temp_src_amp = st.text_input("Amplitude",placeholder="1.0")
            if st.checkbox("Advanced setup",key='t_src_amp_adv'):
                temp_src_amp_set = st.radio("",["function","file","data"],horizontal=True)
                if temp_src_amp_set == "function":
                    st.write("function")
                if temp_src_amp_set == "file":
                    st.write("file")
                if temp_src_amp_set == "data":
                    st.write("data")
    with src_right:
        pass



@st.dialog("Geometry configuration",width = 'medium')
def add_geometry(old_cfg=None):
    geo_left, geo_right = st.columns(2)
    with geo_left:
        st.write("General parameters")
        temp_geo_type = st.selectbox("Type", ["Block", "Sphere", "Cylinder","Prism"],index=None)
        temp_geo_mat = st.selectbox("Material", MATERIAL_KEYS,index=None)
        x,y,z = st.columns(3)
        temp_geo_center = [None]*3
        temp_geo_center[0]= x.number_input("Center",label_visibility ='visible',placeholder="X",value=None,key="tg_cx")
        temp_geo_center[1]= y.number_input("Center",label_visibility ='hidden',placeholder="Y",value=None,key="tg_cy")
        temp_geo_center[2]= z.number_input("Center",label_visibility ='hidden',placeholder="Z",value=None,key="tg_cz")
        
        if st.button("Confirm", type="primary", width='stretch'):
            st.write(f"{temp_geo_type} with {temp_geo_mat} at {temp_geo_center} added.")
            if temp_geo_type == "Sphere":
                st.write(f"Radius: {st.session_state.get('t_sphere_r')}")
            if temp_geo_type == "Block":
                st.write(f"Size: ({st.session_state.get('t_block_sx')}, {st.session_state.get('t_block_sy')}, {st.session_state.get('t_block_sz')})")
                st.write(f"E1: {st.session_state.get('t_block_e1x')}, {st.session_state.get('t_block_e1y')}, {st.session_state.get('t_block_e1z')}")
                st.write(f"E2: {st.session_state.get('t_block_e2x')}, {st.session_state.get('t_block_e2y')}, {st.session_state.get('t_block_e2z')}")
                st.write(f"E3: {st.session_state.get('t_block_e3x')}, {st.session_state.get('t_block_e3y')}, {st.session_state.get('t_block_e3z')}")
                st.write(f"Make it Ellipsoid: {st.session_state.get('t_block_ellipsoid')}")
            if temp_geo_type == "Cylinder":
                st.write(f"Radius: {st.session_state.get('t_cylinder_r')}")
                st.write(f"Height: {st.session_state.get('t_cylinder_h')}")
                st.write(f"Axis: ({st.session_state.get('t_cylinder_axis_x')}, {st.session_state.get('t_cylinder_axis_y')}, {st.session_state.get('t_cylinder_axis_z')})")
                if st.session_state.get("t_cylinder_subclass"):
                    st.write(f"Subclass type: {st.session_state.get('t_cylinder_subclass_type')}")
                    if st.session_state.get('t_cylinder_subclass_type') == "Cone":
                        st.write(f"Top radius: {st.session_state.get('t_cylinder_radius2')}")
                    if st.session_state.get('t_cylinder_subclass_type') == "Wedge":
                        st.write(f"Wedge angle: {st.session_state.get('t_cylinder_wedge_angle')}")
                        st.write(f"Wedge vector:({st.session_state.get('t_cylinder_wedge_x')}, {st.session_state.get('t_cylinder_wedge_y')}, {st.session_state.get('t_cylinder_wedge_z')})")

            if temp_geo_type == "Prism":
                st.write(f"Vertices: {st.session_state.get('t_prism_vertices')}")
                st.write(f"Height: {st.session_state.get('t_prism_h')}")
                st.write(f"Axis: ({st.session_state.get('t_prism_axis_x')}, {st.session_state.get('t_prism_axis_y')}, {st.session_state.get('t_prism_axis_z')})")
                if st.session_state.get('t_prism_center_checkbox'):
                    st.write(f"Shift center: ({st.session_state.get('t_prism_center_x')}, {st.session_state.get('t_prism_center_y')}, {st.session_state.get('t_prism_center_z')})")
                st.write(f"Sidewall angle: {st.session_state.get('t_prism_sidewall_angle')}")


    with geo_right:
        st.write("Type parameters")
        if temp_geo_type == None:
            st.error("Please specify geometry type.")
        else:
            if temp_geo_type == "Sphere":
                temp_radius = st.number_input("Radius", value=None,key="t_sphere_r")
            elif temp_geo_type == "Block":
                size_x,size_y,size_z= st.columns(3)
                temp_s = [None]*3
                temp_s[0] = size_x.number_input("Size",label_visibility ='visible',placeholder="Size X",value=None,key="t_block_sx")
                temp_s[1] = size_y.number_input("Size",label_visibility ='hidden',placeholder="Size Y",value=None,key="t_block_sy")
                temp_s[2] = size_z.number_input("Size",label_visibility ='hidden',placeholder="Size Z",value=None,key="t_block_sz")
                with st.expander("Block axes", expanded=False):
                    axes_x,axes_y,axes_z = st.columns(3)
                    temp_e1 = [None]*3
                    temp_e2 = [None]*3
                    temp_e3 = [None]*3
                    temp_e1[0] = axes_x.number_input(r"$\vec{e_1}$",label_visibility ='visible',placeholder="X",value=1.0,key="t_block_e1x")
                    temp_e1[1] = axes_y.number_input(r"$\vec{e_1}$",label_visibility ='hidden',placeholder="Y",value=0.0,key="t_block_e1y")
                    temp_e1[2] = axes_z.number_input(r"$\vec{e_1}$",label_visibility ='hidden',placeholder="Z",value=0.0,key="t_block_e1z")
                    temp_e2[0] = axes_x.number_input(r"$\vec{e_2}$",label_visibility ='visible',placeholder="X",value=0.0,key="t_block_e2x")
                    temp_e2[1] = axes_y.number_input(r"$\vec{e_2}$",label_visibility ='hidden',placeholder="Y",value=1.0,key="t_block_e2y")
                    temp_e2[2] = axes_z.number_input(r"$\vec{e_2}$",label_visibility ='hidden',placeholder="Z",value=0.0,key="t_block_e2z")
                    temp_e3[0] = axes_x.number_input(r"$\vec{e_3}$",label_visibility ='visible',placeholder="X",value=0.0,key="t_block_e3x")
                    temp_e3[1] = axes_y.number_input(r"$\vec{e_3}$",label_visibility ='hidden',placeholder="Y",value=0.0,key="t_block_e3y")
                    temp_e3[2] = axes_z.number_input(r"$\vec{e_3}$",label_visibility ='hidden',placeholder="Z",value=1.0,key="t_block_e3z")
                ellipsoid = st.checkbox("Make it Ellipsoid", value=False,key="t_block_ellipsoid")

            elif temp_geo_type == "Cylinder":
                temp_radius = st.number_input("Radius", value=None,key="t_cylinder_r")
                temp_height = st.number_input("Height", value=None,key="t_cylinder_h")
                with st.expander("Cylinder axis", expanded=False):
                    axis_x,axis_y,axis_z = st.columns(3)
                    temp_cylinder_axis = [None]*3
                    temp_cylinder_axis[0] = axis_x.number_input("Axis",label_visibility ='visible',placeholder="X",value=0.0,key="t_cylinder_axis_x")
                    temp_cylinder_axis[1] = axis_y.number_input("Axis",label_visibility ='hidden',placeholder="Y",value=0.0,key="t_cylinder_axis_y")
                    temp_cylinder_axis[2] = axis_z.number_input("Axis",label_visibility ='hidden',placeholder="Z",value=1.0,key="t_cylinder_axis_z")

                with st.expander("Subclass", expanded=False):

                    if st.checkbox("Make it subclass", value=False,key="t_cylinder_subclass"):
                        subs = st.radio("Subclass type", ["Cone", "Wedge"],key="t_cylinder_subclass_type")

                        if subs == "Cone":
                            radius2 = st.number_input("Top radius", value=None,key="t_cylinder_radius2")
                        if subs == "Wedge":
                            angle = st.number_input("Wedge angle",placeholder='Degree or radian in unit of pi', value=None,key="t_cylinder_wedge_angle")
                            wedge_vec_x, wedge_vec_y, wedge_vec_z = st.columns(3)
                            temp_wedge_vec = [None]*3
                            temp_wedge_vec[0] = wedge_vec_x.number_input("Wedge vector",label_visibility ='visible',placeholder="X",value=1.0,key="t_cylinder_wedge_x")
                            temp_wedge_vec[1] = wedge_vec_y.number_input("Wedge vector",label_visibility ='hidden',placeholder="Y",value=0.0,key="t_cylinder_wedge_y")
                            temp_wedge_vec[2] = wedge_vec_z.number_input("Wedge vector",label_visibility ='hidden',placeholder="Z",value=0.0,key="t_cylinder_wedge_z")
            elif temp_geo_type == "Prism":
                vertices = st.text_area("Vertices list", value="123", placeholder="Enter vertices as (x,y,z) per line. They must lie in a plane that's perpendicular to the axis.",key="t_prism_vertices")
                temp_height = st.number_input("Height", value=None,key="t_prism_h")
                with st.expander("Prism axis", expanded=False):
                    axis_x,axis_y,axis_z = st.columns(3)
                    temp_prism_axis = [None]*3
                    temp_prism_axis[0] = axis_x.number_input("Axis",label_visibility ='visible',placeholder="X",value=0.0,key="t_prism_axis_x")
                    temp_prism_axis[1] = axis_y.number_input("Axis",label_visibility ='hidden',placeholder="Y",value=0.0,key="t_prism_axis_y")
                    temp_prism_axis[2] = axis_z.number_input("Axis",label_visibility ='hidden',placeholder="Z",value=1.0,key="t_prism_axis_z")
                with st.expander("Center and angle", expanded=False):
                    if st.checkbox("Shift center", value=False,key="t_prism_center_checkbox"):
                        prism_x, prism_y, prism_z = st.columns(3)
                        temp_prism_center = [None]*3
                        temp_prism_center[0] = prism_x.number_input("Bottom center",label_visibility ='visible',placeholder="X",value=1.0,key="t_prism_x")
                        temp_prism_center[1] = prism_y.number_input("Bottom center",label_visibility ='hidden',placeholder="Y",value=0.0,key="t_prism_y")
                        temp_prism_center[2] = prism_z.number_input("Bottom center",label_visibility ='hidden',placeholder="Z",value=0.0,key="t_prism_z")
                    temp_sidewall_angle = st.number_input("Sidewall angle",placeholder='Degree or radian in unit of pi', value=0,key="t_prism_sidewall_angle")
                




            


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
        res = xyz.number_input("Simulation resolution", value=10)
        bg_mat = xyz.number_input("Background material", value=1.0)

        BCs = st.expander("Boundary conditions", expanded=False)
        BCs.write("Boundary conditions settings will go here.")

        simu_setup = st.expander("Simulation setup", expanded=False)
        sim_until = simu_setup.selectbox("Termination unitl", ["Time / ms", "Si", "SiO2", "Ag", "Au"])


    if st.session_state.active_page == "geometry":
        if st.button("Add geometry", type="primary", width='stretch'):
            add_geometry()

        with st.expander("Geometry list", expanded=True):
            if st.session_state.geoms:
                items = [f"{g['type']} ({g['material']}) at {g['center']}" for i, g in enumerate(st.session_state.geoms)]
                sorted_items = sort_items(items,direction='vertical')
                if sorted_items != items:
                    new_list = [st.session_state.geoms[int(s.split(":")[0])] for s in sorted_items]
                    st.session_state.geoms = new_list
                    st.rerun()
            else:
                st.info("No geometries added yet.")

    if st.session_state.active_page == "source":
        if st.button("Add source",type="primary", width='stretch'):
            src_cfg()
    if st.session_state.active_page == "monitor":
        pass



tab_view, tab_res = st.tabs(["3D viewer", "Results"])
with tab_view:
    st.info("3D viewer will be implemented here.")

# 1. 仿真设置
"""with tab_cfg:
    c1, c2, c3 = st.columns(3)
    box1 = c1.container(border=True)
    box1_title = box1.subheader("📐 Space setup" )
    sx = box1.number_input("Size X", value=5.0)
    sy = box1.number_input("Size Y", value=5.0)
    sz = box1.number_input("Size Z", value=5.0)
    res = box1.number_input("Simulation resolution", value=10)
    bg_eps = box1.number_input("Background material", value=1.0)

    box2 = c2.container(border=True)
    box2_title = box2.subheader("Boundary conditions")

    box3 = c3.container(border=True)
    box3_title = box3.subheader("Simulation Setup")
    sim_until = box3.selectbox("Termination unitl", ["Time / ms", "Si", "SiO2", "Ag", "Au"])
    if st.button("🚀 Run simulation", type="primary", use_container_width=True):
        payload = {
            "sx": sx, "sy": sy, "sz": sz, "res": res, "bg_eps": bg_eps, "until": sim_until,
            "geoms": st.session_state.geoms, "sources": st.session_state.sources
        }
        with st.spinner("WSL 计算中..."):
            r = requests.post("http://127.0.0.1:8000/simulate_full", json=payload)
            st.session_state.results = r.json()"""

# 2. 几何体管理
"""with tab_geo:
    geo_add_col,geo_list_col = st.columns([2,1])

    with geo_add_col.container(border = True):
        st.subheader("Add Geometry")
        g_type = st.selectbox("Type", ["Block", "Sphere"])
        mat = st.selectbox("Material", ["User defined (Epsilon)", "Si", "SiO2", "Ag", "Au"])
        eps = st.number_input("Custom Epsilon", value=2.0) if mat == "User defined (Epsilon)" else 1.0
        pos = (st.number_input("X"), st.number_input("Y"), st.number_input("Z"))
        if g_type == "Block":
            s_val = (st.number_input("SX", value=1.0), st.number_input("SY", value=1.0), st.number_input("SZ", value=1.0))
            params = {"size": s_val}
        else:
            params = {"radius": st.number_input("R", value=1.0)}
        
        if st.button("confirm"):
            st.session_state.geoms.append({"type": g_type, "material": mat, "eps": eps, "center": pos, **params})
            st.rerun()

    
    with geo_list_col.container(border = True):
        st.subheader("Geometry List")

        if st.session_state.geoms:
            items = [f"{g['type']} ({g['material']}) at {g['center']}" for i, g in enumerate(st.session_state.geoms)]
            sorted_items = sort_items(items,direction='vertical')
            if sorted_items != items:
                new_list = [st.session_state.geoms[int(s.split(":")[0])] for s in sorted_items]
                st.session_state.geoms = new_list
                st.rerun()
        else:
            st.info("No geometries added yet.")
"""
"""# 3. 光源管理
with tab_src:
    pass"""

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