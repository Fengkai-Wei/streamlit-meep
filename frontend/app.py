import streamlit as st
import requests
import numpy as np
import plotly.graph_objects as go
import base64
from geo import *
from streamlit_sortables import sort_items
from mat import MATERIAL_KEYS
from utils import clear_temp


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

def card_widget(info, uid, top=False, bottom=False):
    key_prefix = f'geolist_{uid}'
    with st.popover(info[0], width='stretch', key=key_prefix):
        st.title(info[0])
        with st.container(horizontal=True, border=False, gap='xxsmall'):
            st.button("⚙️", type="tertiary", key=f'{key_prefix}_edit')
            st.button("🗑️", type="tertiary", key=f'{key_prefix}_delete')
            if not top:
                st.button("🔼", type="tertiary", key=f'{key_prefix}_move_up')
            if not bottom:
                st.button("🔽", type="tertiary", key=f'{key_prefix}_move_down')





@st.cache_data
def get_mesh(sx, sy, sz, nx, ny, nz):
    x, y, z = np.meshgrid(np.linspace(-sx/2, sx/2, nx), 
                         np.linspace(-sy/2, sy/2, ny), 
                         np.linspace(-sz/2, sz/2, nz), indexing='ij')
    return x.flatten(), y.flatten(), z.flatten()


@st.dialog("Source configuration",width = 'medium')
def src_cfg(old_cfg=None):
    src_left,divider,src_right = st.columns([1,0.1,1])
    with src_left:
        st.write("General parameters")
        temp_src_type = st.selectbox("Type", ["Custom", "Eigenmode","Gaussian"],index=None,key='t_src_type')
        with st.expander("Source-time config"):
            temp_srt_type = st.radio("Time type", ["Gaussian", "Continuous", "Custom",],key='t_srt_type',label_visibility='collapsed',horizontal=True)
            if temp_srt_type != "Custom":
                temp_srt_wl = st.number_input("Wavelength",placeholder="Wavelength of the source",key='t_src_f')
                temp_srt_width = st.number_input("Wavelength width",placeholder="Wavelength width",key='t_src_fd',value = 0.0)
            else:
                temp_srt_func = st.text_area("Time function",placeholder="A custom time function of the source, e.g. exp(-t**2)",key='t_src_time_func')
                temp_srt_f = st.number_input("Frequency",placeholder="Frequency of the source",key='t_src_f_custom',value = 0.0)
                temp_srt_fwidth = st.number_input("Frequency width",placeholder="Frequency width",key='t_src_fd_custom',value =1e50)
            with st.expander("Time responce"):
                temp_srt_start = st.number_input("Start time",placeholder="Time to turn on the source",key='t_src_time_start',value=0.0 if temp_srt_type != "Custom" else -1e20)
                temp_srt_end = st.number_input("End time",placeholder="Time to turn off the source",key='t_src_time_end',value =1e20)
                if temp_srt_type != "Custom":
                    temp_srt_cutoff = st.number_input("Cutoff",placeholder="Cutoff for continuous source",key='t_src_time_cutoff',value=None if temp_srt_type == "Continuous" else 5.0)
                if temp_srt_type == "Continuous":
                    temp_srt_slowness = st.number_input("Slowness",placeholder="Slowness for total-field/scattered-field source",key='t_src_time_slowness',value=3.0)
            temp_srt_int = st.checkbox("Make it integral of current",key='t_src_time_int',value=False)
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
            if st.checkbox("More advanced amplitude",key='t_src_amp_adv'):
                temp_src_amp_set = st.radio("defined by",["function","file","data"],horizontal=True,label_visibility='collapsed')
                if temp_src_amp_set == "function":
                    st.write("function")
                if temp_src_amp_set == "file":
                    st.write("file")
                if temp_src_amp_set == "data":
                    st.write("data")

    with src_right:
        st.write("Source parameters")
        if st.session_state.get('t_src_type') == None:
            st.error("Please specify source type.")
        if st.session_state.get('t_src_type') == "Custom":
            temp_src_comp = st.selectbox("Component", ["Ex", "Ey", "Ez", "Hx", "Hy", "Hz"],index=None,key='t_src_comp_custom')
        if st.session_state.get('t_src_type') == "Eigenmode":
            temp_src_comp = st.selectbox("Component", ['All',"Ex", "Ey", "Ez", "Hx", "Hy", "Hz"],index=0,key='t_src_comp_eig')

            temp_eig_band = st.number_input('Eigenband index', min_value=1, step=1,placeholder = 'The index of n of the desided band.',key = 't_src_eig_band')
            temp_eig_res = st.number_input('Eigenmode solver resolution',placeholder='Resolution for the eigenmode solver',key='t_src_eig_res',value = 2*st.session_state.get('g_sim_res') if st.session_state.get('g_sim_res') !=None else 20)
            temp_eig_tol = st.text_input('Eigenmode solver tolerance',placeholder='Tolerance for the eigenmode solver.',key='t_src_eig_tol',value = '1e12')
            with st.expander("Eigenmode lattice"):
                x,y,z = st.columns(3)
                temp_eig_lat_size = [None]*3
                temp_eig_lat_size[0]= x.number_input("Lattice size",label_visibility ='visible',placeholder="X",value=None,key='t_src_eig_lat_sx')
                temp_eig_lat_size[1]= y.number_input("Lattice size",label_visibility ='hidden',placeholder="Y",value=None,key='t_src_eig_lat_sy')
                temp_eig_lat_size[2]= z.number_input("Lattice size",label_visibility ='hidden',placeholder="Z",value=None,key='t_src_eig_lat_sz')
                temp_eig_lat_center = [None]*3
                temp_eig_lat_center[0]= x.number_input("Lattice center",label_visibility ='visible',placeholder="X",value=None,key='t_src_eig_lat_cx')
                temp_eig_lat_center[1]= y.number_input("Lattice center",label_visibility ='hidden',placeholder="Y",value=None,key='t_src_eig_lat_cy')
                temp_eig_lat_center[2]= z.number_input("Lattice center",label_visibility ='hidden',placeholder="Z",value=None,key='t_src_eig_lat_cz')
            with st.expander("Eigenmode parity"):
                temp_eig_par = st.multiselect("Parity", ["No parity","Even Z", "Odd Z", "Even Y", "ODD Y"],key='t_src_eig_parity',default=["No parity"])
            with st.expander("Direction, frequency and reciprocal for eigenmode"):
                temp_eig_match_freq = st.checkbox("Match frequency",key='t_src_eig_match_freq')
                temp_eig_dir = st.selectbox("Direction", ["Auto","X", "Y", "Z"],key='t_src_eig_dir',index= 0)
                x,y,z = st.columns(3)
                temp_eig_kpt = [None]*3
                temp_eig_kpt[0] = x.number_input("k-point",label_visibility ='visible',placeholder="kx",key='t_src_eig_kptx')
                temp_eig_kpt[1] = y.number_input("k-point",label_visibility ='hidden',placeholder="ky",key='t_src_eig_kpty')
                temp_eig_kpt[2] = z.number_input("k-point",label_visibility ='hidden',placeholder="kz",key='t_src_eig_kptz')
        if st.session_state.get('t_src_type') == "Gaussian":
            
            temp_src_comp = st.selectbox("Component", ['All',"Ex", "Ey", "Ez", "Hx", "Hy", "Hz"],index=0,key='t_src_comp_gau')
            temp_gau_w0 = st.number_input("Beam waist w0", value=None,key='t_src_gau_w0') 
            temp_gau_2d = st.checkbox("Make it 2D",key='t_src_gau_2d')
            temp_gau_x0 = [None]*3
            temp_gau_kdir = [None]*3
            temp_gau_E0 = [None]*3

            with st.expander("Focus, direction and polarization"):
                x,y,z = st.columns(3)
                temp_gau_x0[0]= x.number_input("Focus",label_visibility ='visible',placeholder="X",value=None,key='t_src_gau_x0x')
                temp_gau_x0[1]= y.number_input("Focus",label_visibility ='hidden',placeholder="Y",value=None,key='t_src_gau_x0y')
                temp_gau_x0[2]= z.number_input("Focus",label_visibility ='hidden',placeholder="Z",value=None,key='t_src_gau_x0z')
                temp_gau_kdir[0]= x.number_input("Direction",label_visibility ='visible',placeholder="X",value=None,key='t_src_gau_kdirx')
                temp_gau_kdir[1]= y.number_input("Direction",label_visibility ='hidden',placeholder="Y",value=None,key='t_src_gau_kdiry')
                temp_gau_kdir[2]= z.number_input("Direction",label_visibility ='hidden',placeholder="Z",value=None,key='t_src_gau_kdirz')
                temp_gau_E0[0]= x.number_input("Polarization",label_visibility ='visible',placeholder="Ex",value=None,key='t_src_gau_E0x')
                temp_gau_E0[1]= y.number_input("Polarization",label_visibility ='hidden',placeholder="Ey",value=None,key='t_src_gau_E0y')
                temp_gau_E0[2]= z.number_input("Polarization",label_visibility ='hidden',placeholder="Ez",value=None,key='t_src_gau_E0z')

            











@st.dialog("Geometry configuration",width = 'medium')
def add_geometry(old_cfg=None):
    geo_left, geo_right = st.columns(2)
    with geo_left:
        st.write("General parameters")
        temp_geo_type = st.selectbox("Type", ["Block", "Sphere", "Cylinder","Prism"],index=None)
        temp_geo_name = st.text_input("Name",placeholder="Name of the geometry",key='tg_name')
        temp_geo_mat = st.selectbox("Material", MATERIAL_KEYS,index=None)
        x,y,z = st.columns(3)
        temp_geo_center = [None]*3
        temp_geo_center[0]= x.number_input("Center",label_visibility ='visible',placeholder="X",value=None,key="tg_cx")
        temp_geo_center[1]= y.number_input("Center",label_visibility ='hidden',placeholder="Y",value=None,key="tg_cy")
        temp_geo_center[2]= z.number_input("Center",label_visibility ='hidden',placeholder="Z",value=None,key="tg_cz")
        
        if st.button("Confirm", type="primary", width='stretch'):
            if temp_geo_type == "Sphere":
                st.session_state.geoms.append(
                    Sphere(center=tuple(temp_geo_center), 
                           radius=st.session_state.get('t_sphere_r'), 
                           color="blue", 
                           name=st.session_state.get('tg_name')+" (Sphere)",
                           material=temp_geo_mat))
                
            if temp_geo_type == "Block":
                if st.session_state.get("t_block_ellipsoid"):
                    st.session_state.geoms.append(
                        Ellipsoid(center=tuple(temp_geo_center), 
                                  size=(st.session_state.get('t_block_sx'),
                                        st.session_state.get('t_block_sy'), 
                                        st.session_state.get('t_block_sz')), 
                                        e1=(st.session_state.get('t_block_e1x'), 
                                            st.session_state.get('t_block_e1y'), 
                                            st.session_state.get('t_block_e1z')), 
                                        e2=(st.session_state.get('t_block_e2x'), 
                                            st.session_state.get('t_block_e2y'), 
                                            st.session_state.get('t_block_e2z')),
                                        e3=(st.session_state.get('t_block_e3x'),
                                            st.session_state.get('t_block_e3y'),
                                             st.session_state.get('t_block_e3z')), 
                                        color="blue", name=st.session_state.get('tg_name')+" (Ellipsoid)",
                                        material=temp_geo_mat))
                else:
                    st.session_state.geoms.append(
                        Block(center=tuple(temp_geo_center), 
                              size=(st.session_state.get('t_block_sx'),
                                    st.session_state.get('t_block_sy'), 
                                    st.session_state.get('t_block_sz')), 
                                    e1=(st.session_state.get('t_block_e1x'), 
                                        st.session_state.get('t_block_e1y'), 
                                        st.session_state.get('t_block_e1z')), 
                                    e2=(st.session_state.get('t_block_e2x'), 
                                        st.session_state.get('t_block_e2y'), 
                                        st.session_state.get('t_block_e2z')),
                                    e3=(st.session_state.get('t_block_e3x'),
                                        st.session_state.get('t_block_e3y'),
                                         st.session_state.get('t_block_e3z')), 
                                    color="blue", name=st.session_state.get('tg_name')+" (Block)",
                                    material=temp_geo_mat))
                    
            if temp_geo_type == "Cylinder":
                if st.session_state.get("t_cylinder_subclass"):
                    if st.session_state.get('t_cylinder_subclass_type') == "Cone":
                        st.session_state.geoms.append(
                            Cone(center=tuple(temp_geo_center), 
                                 radius=st.session_state.get('t_cylinder_r'), 
                                 height=st.session_state.get('t_cylinder_h'), 
                                 axis=(st.session_state.get('t_cylinder_axis_x'), 
                                       st.session_state.get('t_cylinder_axis_y'), 
                                       st.session_state.get('t_cylinder_axis_z')), 
                                 radius1=st.session_state.get('t_cylinder_radius2'),
                                 color="blue", name=st.session_state.get('tg_name')+" (Cone)",
                                 material=temp_geo_mat)
                        )
                    if st.session_state.get('t_cylinder_subclass_type') == "Wedge":
                        st.session_state.geoms.append(
                            Wedge(center=tuple(temp_geo_center), 
                                   radius=st.session_state.get('t_cylinder_r'), 
                                   height=st.session_state.get('t_cylinder_h'), 
                                   axis=(st.session_state.get('t_cylinder_axis_x'), 
                                         st.session_state.get('t_cylinder_axis_y'), 
                                         st.session_state.get('t_cylinder_axis_z')), 
                                   wedge_angle=st.session_state.get('t_cylinder_wedge_angle'),
                                   wedge_start=(st.session_state.get('t_cylinder_wedge_x'), 
                                                 st.session_state.get('t_cylinder_wedge_y'), 
                                                 st.session_state.get('t_cylinder_wedge_z')),
                                   color="blue", name=st.session_state.get('tg_name')+" (Wedge)",
                                   material=temp_geo_mat)
                        )

                else:
                    st.session_state.geoms.append(
                        Cylinder(center=tuple(temp_geo_center), 
                                 radius=st.session_state.get('t_cylinder_r'), 
                                 height=st.session_state.get('t_cylinder_h'), 
                                 axis=(st.session_state.get('t_cylinder_axis_x'), 
                                       st.session_state.get('t_cylinder_axis_y'), 
                                       st.session_state.get('t_cylinder_axis_z')), 
                                 color="blue", name=st.session_state.get('tg_name')+" (Cylinder)",
                                 material=temp_geo_mat)
                    )

            

            if temp_geo_type == "Prism":
                st.session_state.geoms.append(
                    Prism(center=tuple(temp_geo_center),
                          height=st.session_state.get('t_prism_h'),
                          axis=(st.session_state.get('t_prism_axis_x'), 
                                st.session_state.get('t_prism_axis_y'), 
                                st.session_state.get('t_prism_axis_z')),
                          sidewall_angle=st.session_state.get('t_prism_sidewall_angle'),
                          vertices=st.session_state.get('t_prism_vertices'),
                          shift_center = (
                              st.session_state.get('t_prism_center_x'),
                              st.session_state.get('t_prism_center_y'),
                              st.session_state.get('t_prism_center_z'),
                              
                          ) if st.session_state.get("t_prism_center_checkbox") else None, 
                          color="blue", name=st.session_state.get('tg_name')+" (Prism)",
                          material=temp_geo_mat)
                )
            clear_temp()
            st.rerun()


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
        res = xyz.number_input("Simulation resolution", value=10,key='g_sim_res')
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
                for idx, geom in enumerate(st.session_state.geoms):
                    uid = getattr(geom, 'uid')
                    card_widget([f"{idx+1}. {geom.name}", geom.material], uid=uid, top=idx==0, bottom=idx==len(st.session_state.geoms)-1)
            else:
                st.info("No geometries added yet.")

    if st.session_state.active_page == "source":
        if st.button("Add source",type="primary", width='stretch'):
            src_cfg()
    if st.session_state.active_page == "monitor":
        pass



tab_view, tab_res = st.tabs(["3D viewer", "Results"])
with tab_view:
    fig = go.Figure()
    dummy_block_trace_b = geo_trace_checker(
        Ellipsoid(center=(0, 0, 0), size=(1, 1.5, 0.8), e1=(1, 0, 0), e2=(0, 1, 0), e3=(0, 0, 1), color="red", name="Dummy Block B (Ellipsoid)",material="Si")
    )
    dummy_block_trace_c = geo_trace_checker(
    Block(center=(0, -1.5, 0), size=(1.2, 0.4, 0.8), e1=(1, 0.5, 0), e2=(0, 1, 0), e3=(0, 0, 1), color="green", name="Dummy Block C (Cut)",material="Si")
    )
    fig.add_traces(dummy_block_trace_b)
    fig.add_traces(dummy_block_trace_c)
    fig.update_layout(
    scene=dict(
        xaxis_title='X (um)',
        yaxis_title='Y (um)',
        zaxis_title='Z (um)',
        # 核心：确保 3D 物理比例 1:1:1，否则球体会变成橄榄球
        aspectmode='data',
        camera=dict(
            eye=dict(x=1.8, y=1.8, z=1.2) # 设置默认视角
        )
    ),
    margin=dict(l=0, r=0, b=0, t=60),
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    st.plotly_chart(fig, width = 'stretch',height= 'stretch')



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