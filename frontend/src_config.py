import streamlit as st
import numpy as np
import pandas as pd
import uuid
import plotly.graph_objects as go
from utils import clear_temp


OPACITY = 0.75



class CW_srct:
    def __init__(
        self,
        frequency=None,
        start_time=0.0,
        end_time=1e20,
        width=0,
        fwidth=np.inf,
        cutoff=None,
        slowness=3.0,
        wavelength=None,
        is_integrated=False,
        **kwargs,
    ):
        self.frequency = frequency
        self.start_time = start_time
        self.end_time = end_time
        self.width = width
        self.fwidth = fwidth
        self.cutoff = cutoff
        self.slowness = slowness
        self.wavelength = wavelength
        self.is_integrated = is_integrated

class Gaussian_srct:
    def __init__(
        self,
        frequency=None,
        width=0.0,
        fwidth=np.inf,
        start_time=0.0,
        cutoff=5.0,
        is_integrated=False,
        wavelength=None,
        **kwargs,
    ):
        self.frequency = frequency
        self.width = width
        self.fwidth = fwidth
        self.start_time = start_time
        self.cutoff = cutoff
        self.is_integrated = is_integrated
        self.wavelength = wavelength

class Custom_srct:
    def __init__(
        self,
        src_func,
        start_time=-1e20,
        end_time=1e20,
        is_integrated=False,
        center_frequency=0.0,
        fwidth=0.0,
        **kwargs,
    ):
        self.src_func = src_func
        self.start_time = start_time
        self.end_time = end_time
        self.is_integrated = is_integrated
        self.center_frequency = center_frequency
        self.fwidth = fwidth



class Source:
    def __init__(
        self,
        name,
        color,
        srct,
        component,
        opacity=1.0,
        center=None,
        volume=None,
        size=np.array([0, 0, 0]),
        amplitude=1.0,
        amp_func=None,
        amp_func_file='',
        amp_data=None,
    ):
        self.srct = srct
        self.name = name
        self.color = color
        self.opacity = opacity
        self.component = component
        self.center = center
        self.volume = volume
        self.size = size
        self.amplitude = amplitude
        self.amp_func = amp_func
        self.amp_func_file = amp_func_file
        self.amp_data = amp_data
        self.uid = uuid.uuid4().hex

class EigenmodeSource(Source):
    def __init__(
        self,
        name,
        color,
        srct,
        center=None,
        volume=None,
        eig_lattice_size=None,
        eig_lattice_center=None,
        eig_vol=None,
        componenet='All',
        direction='Auto',
        eig_band=1,
        eig_kpoint=np.array([0, 0, 0]),
        eig_match_freq=True,
        eig_parity='No parity',
        eig_resolution=0,
        eig_tolerance=1e-12,
        **kwargs,
    ):
        super().__init__(name, color, srct, component=componenet, center=center, volume=volume, **kwargs)
        self.eig_lattice_size = eig_lattice_size
        self.eig_lattice_center = eig_lattice_center
        self.eig_vol = eig_vol
        self.direction = direction
        self.eig_band = eig_band
        self.eig_kpoint = eig_kpoint
        self.eig_match_freq = eig_match_freq
        self.eig_parity = eig_parity
        self.eig_resolution = eig_resolution
        self.eig_tolerance = eig_tolerance

class GaussianSource(Source):
    def __init__(
        self,
        name,
        color,
        srct,
        center=None,
        volume=None,
        component='All',
        beam_x0=np.array([0, 0, 0]),
        beam_kdir=np.array([0, 0, 0]),
        beam_w0=None,
        beam_E0=np.array([0, 0, 0]),
        **kwargs,
    ):
        super().__init__(name, color, srct, component=component, center=center, volume=volume, **kwargs)
        self.beam_x0 = beam_x0
        self.beam_kdir = beam_kdir
        self.beam_w0 = beam_w0
        self.beam_E0 = beam_E0


class GaussianSource2D(Source):
    def __init__(
        self,
        name,
        color,
        srct,
        center=None,
        volume=None,
        component='All',
        beam_x0=np.array([0, 0, 0]),
        beam_kdir=np.array([0, 0, 0]),
        beam_w0=None,
        beam_E0=np.array([0, 0, 0]),
        **kwargs,
    ):
        super().__init__(name, color, srct, component=component, center=center, volume=volume, **kwargs)
        self.beam_x0 = beam_x0
        self.beam_kdir = beam_kdir
        self.beam_w0 = beam_w0
        self.beam_E0 = beam_E0








@st.dialog("Source configuration", width='large')
def src_cfg(old_cfg=None, edit_idx=None):
    # --- 初始化默认值 ---
    default_color = None
    default_src_type = None
    default_srt_type = None
    default_center = [None, None, None]
    default_size = [None, None, None]
    default_name = None
    default_srt_func = None
    default_srt_wl = None
    default_srt_wl_width = 0.0
    default_srt_fwidth = 0.0
    default_width_option = "Temporal"
    default_srt_start = 0.0
    default_srt_end = 1e20
    default_srt_cutoff = None
    default_srt_int = False
    default_srt_slowness = None
    default_srt_func = None
    default_amp = 1.0
    default_amp_adv = None
    default_amp_set = None
    default_amp_func = None
    default_amp_func_file = ''
    default_src_custom_comp = None
    default_src_eig_comp = None
    default_src_eig_band = 1
    default_src_eig_res = None
    default_src_eig_tol = 1e-8
    default_src_eig_lattice = [None, None, None]
    default_src_eig_lattice_center = [None, None, None]
    default_src_eig_parity = ['No parity']
    default_src_eig_match_freq = None
    default_src_eig_dir = 'Auto'
    default_src_eig_kpt = [None, None, None]
    default_src_gau_comp = None
    default_src_gau_w0 = None
    default_src_gau_x0 = [None, None, None]
    default_src_gau_kdir = [None, None, None]
    default_src_gau_E0 = [None, None, None]
    default_src_gau_2d = False


    
    if old_cfg is not None:
        cfg_type = type(old_cfg).__name__
        
        default_color = getattr(old_cfg, "color", None)
        default_name = getattr(old_cfg, "name", None)
        default_amp = getattr(old_cfg, "amplitude", 1.0)
        if old_cfg.center is not None: default_center = list(old_cfg.center)
        if old_cfg.volume is not None: default_size = list(old_cfg.volume)

        if cfg_type == 'EigenmodeSource': 
            default_src_type = 'Eigenmode'
            default_src_eig_comp = getattr(old_cfg, "component", None)
            default_src_eig_band = getattr(old_cfg, 'eig_band', default_src_eig_band)
            default_src_eig_res = getattr(old_cfg, 'eig_resolution', default_src_eig_res)
            default_src_eig_tol = getattr(old_cfg, 'eig_tolerance', default_src_eig_tol)
            default_src_eig_lattice = list(getattr(old_cfg, 'eig_lattice_size', default_src_eig_lattice))
            default_src_eig_lattice_center = list(getattr(old_cfg, 'eig_lattice_center', default_src_eig_lattice_center))
            default_src_eig_parity = getattr(old_cfg, 'eig_parity', default_src_eig_parity)
            default_src_eig_match_freq = getattr(old_cfg, 'eig_match_freq', default_src_eig_match_freq)
            default_src_eig_dir = getattr(old_cfg, 'direction', default_src_eig_dir)
            default_src_eig_kpt = list(getattr(old_cfg, 'eig_kpoint', default_src_eig_kpt))

        elif cfg_type == 'GaussianSource':
            default_src_type = 'Gaussian'
            default_src_gau_comp = getattr(old_cfg, "component", None)
            default_src_gau_w0 = getattr(old_cfg, 'beam_w0', None)
            default_src_gau_x0 = list(getattr(old_cfg, 'beam_x0', default_src_gau_x0))
            default_src_gau_kdir = list(getattr(old_cfg, 'beam_kdir', default_src_gau_kdir))
            default_src_gau_E0 = list(getattr(old_cfg, 'beam_E0', default_src_gau_E0))
            default_src_gau_2d = getattr(old_cfg, 'beam_2d', default_src_gau_2d)

        elif cfg_type == 'Source': 
            default_src_type = 'Custom'
            default_src_custom_comp = getattr(old_cfg, "component", None)

        
        if hasattr(old_cfg, "srct"):
            srct = old_cfg.srct
            srct_type = type(srct).__name__
            if srct_type == 'Gaussian_srct': 
                default_srt_type = 'Gaussian'
                default_srt_cutoff = getattr(srct, 'cutoff', 5.0)
            elif srct_type == 'CW_srct': 
                default_srt_type = 'Continuous'
                default_srt_start = getattr(srct, 'start_time', 0.0)
                default_srt_end = getattr(srct, 'end_time', 1e20)
                default_srt_cutoff = getattr(srct, 'cutoff', 5.0)
                default_srt_slowness = getattr(srct, 'slowness', 3.0)
            elif srct_type == 'Custom_srct': 
                default_srt_type = 'Custom'
                default_srt_start = getattr(srct, 'start_time', -1e20)
                default_srt_end = getattr(srct, 'end_time', 1e20)
                default_srt_custom_cfreq = getattr(srct, 'center_frequency', 0.0)
            
            default_srt_wl = getattr(srct, 'wavelength') or 1.0/getattr(srct, 'frequency')
            default_srt_wl_width = getattr(srct, 'width', 0.0)
            if hasattr(srct, 'wavelength'):
                default_srt_wl = getattr(srct, 'wavelength')
            elif hasattr(srct, 'frequency'):
                default_srt_wl = 1.0/getattr(srct, 'frequency')
            if hasattr(srct, 'width'):
                default_srt_wl_width = getattr(srct, 'width')
                default_width_option = "Tempeoral"
            elif hasattr(srct, 'fwidth'):
                default_srt_fwidth = getattr(srct, 'fwidth')
                default_width_option = "Frequency"

            default_srt_int = getattr(srct, 'is_integrated', False)



        # 组件与特定参数


    # --- 2. 获取临时状态值 ---
    temp_src_type = st.session_state.get('t_src_type', default_src_type or "Custom")
    temp_srt_type = st.session_state.get('t_srt_type', default_srt_type or "Continuous")
    temp_src_center = [
        st.session_state.get('t_src_center_x', default_center[0]),
        st.session_state.get('t_src_center_y', default_center[1]),
        st.session_state.get('t_src_center_z', default_center[2]),
    ]
    temp_src_size = [
        st.session_state.get('t_src_size_x', default_size[0]),
        st.session_state.get('t_src_size_y', default_size[1]),
        st.session_state.get('t_src_size_z', default_size[2]),
    ]
    temp_amp_adv = st.session_state.get('t_src_amp_adv', default_amp_adv)
    temp_amp_set = st.session_state.get('t_src_amp_set', default_amp_set)
    temp_amp_func = st.session_state.get('t_src_amp_func', default_amp_func)
    temp_amp_func_file = st.session_state.get('t_src_amp_func_file', default_amp_func_file)

    if st.button("Confirm", type='primary', use_container_width=True):
        if temp_src_type is None:
            st.toast("Please select source type!", icon="⚠️")
        else:
            if temp_srt_type == "Custom":
                srct = Custom_srct(
                    src_func=st.session_state.get('t_src_time_func'),
                    start_time=st.session_state.get('t_src_time_start', -1e20),
                    end_time=st.session_state.get('t_src_time_end', 1e20),
                    is_integrated=st.session_state.get('t_src_time_int', False),
                    center_frequency=st.session_state.get('t_src_f_custom', 0.0),
                    fwidth=st.session_state.get('t_src_fd_custom', 1e50),
                )
            elif temp_srt_type == "Gaussian":
                srct = Gaussian_srct(
                    frequency=st.session_state.get('t_src_f'),
                    width=st.session_state.get('t_src_fd', 0.0),
                    fwidth=st.session_state.get('t_src_fd', 0.0),
                    start_time=st.session_state.get('t_src_time_start', 0.0),
                    cutoff=st.session_state.get('t_src_time_cutoff', 5.0),
                    is_integrated=st.session_state.get('t_src_time_int', False),
                    wavelength=st.session_state.get('t_src_f'),
                )
            elif temp_srt_type == "Continuous":
                srct = CW_srct(
                    frequency=st.session_state.get('t_src_f'),
                    start_time=st.session_state.get('t_src_time_start', 0.0),
                    end_time=st.session_state.get('t_src_time_end', 1e20),
                    width=st.session_state.get('t_src_fd', 0.0),
                    fwidth=st.session_state.get('t_src_fd', np.inf),
                    cutoff=st.session_state.get('t_src_time_cutoff', None),
                    slowness=st.session_state.get('t_src_time_slowness', 3.0),
                    wavelength=st.session_state.get('t_src_f'),
                    is_integrated=st.session_state.get('t_src_time_int', False),
                )

            # 根据类型创建具体对象
            base_kwargs = {
                "name": st.session_state.get('t_src_name', f"{temp_src_type} source"),
                "color": "#ffffff",
                "srct": srct,
                "component": st.session_state.get('t_src_comp_custom') if temp_src_type == 'Custom' else st.session_state.get('t_src_comp_eig') if temp_src_type == 'Eigenmode' else st.session_state.get('t_src_comp_gau'),
                "center": tuple(temp_src_center) if all(v is not None for v in temp_src_center) else None,
                "volume": tuple(temp_src_size) if all(v is not None for v in temp_src_size) else None,
                "amplitude": float(st.session_state.get('t_src_amp') or 1.0),
            }

            if temp_src_type == "Eigenmode":
                new_source = EigenmodeSource(
                    **base_kwargs,
                    eig_band=st.session_state.get('t_src_eig_band', 1),
                    eig_resolution=st.session_state.get('t_src_eig_res', 20),
                    eig_tolerance=float(st.session_state.get('t_src_eig_tol', '1e-12')),
                )
            elif temp_src_type == "Gaussian":
                new_source = GaussianSource(
                    **base_kwargs,
                    beam_w0=st.session_state.get('t_src_gau_w0'),
                )
            else:
                new_source = Source(**base_kwargs)

            if 'sources' not in st.session_state:
                st.session_state.sources = []
                
            if edit_idx is not None and 0 <= edit_idx < len(st.session_state.sources):
                st.session_state.sources[edit_idx] = new_source
                st.toast(f"Source {new_source.name} updated", icon="✔️")
            else:
                st.session_state.sources.append(new_source)
                st.toast(f"Source added: {new_source.name}", icon="✔️")
                
            clear_temp()
            st.rerun()

    # --- 4. UI 布局 ---
    src_left, divider, src_right = st.columns([1, 0.1, 1])
    with src_left:
        src_type_options = ["Custom", "Eigenmode", "Gaussian"]
        temp_src_type_select = st.selectbox("Source type", src_type_options, 
                                     index=src_type_options.index(temp_src_type), key='t_src_type')
        st.text_input("Name", placeholder="Source name", key='t_src_name', value=default_name)
        
        with st.expander("Source-time config"):
            srt_type_options = ["Gaussian", "Continuous", "Custom"]
            temp_srt_type_select = st.radio("Time type", srt_type_options, 
                                     index=srt_type_options.index(temp_srt_type),
                                     key='t_srt_type', label_visibility='collapsed', horizontal=True)
            if temp_srt_type == "Custom":
                temp_srt_func = st.text_area("Time function", placeholder="A custom time function of the source, e.g. exp(-t**2)", key='t_srt_time_func', value=default_srt_func)
            temp_srt_wl = st.number_input("Wavelength", placeholder="Wavelength of the source", key='t_srt_wl', value=default_srt_wl)
            width_list = ["Tempeoral", "Frequency"]
            width_option = st.radio("Wavelength width defined by", width_list, key='t_srt_wl_width_option', horizontal=True,index=width_list.index(default_width_option))
            if width_option == "Tempeoral":
                temp_srt_width = st.number_input("Temporal width", placeholder="Temporal width", key='t_srt_wl_width', value=default_srt_wl_width)
            elif width_option == "Frequency":
                temp_srt_width = st.number_input("Frequency width", placeholder="Frequency width", key='t_srt_fwidth',value=default_srt_fwidth)

            with st.expander("Time responce"):
                temp_srt_start = st.number_input("Start time", placeholder="Time to turn on the source", key='t_srt_start', value=default_srt_start)
                temp_srt_end = st.number_input("End time", placeholder="Time to turn off the source", key='t_srt_end', value=default_srt_end)
                if temp_srt_type != "Custom":
                    temp_srt_cutoff = st.number_input("Cutoff", placeholder="Cutoff", key='t_srt_cutoff', value=default_srt_cutoff)
                if temp_srt_type == "Continuous":
                    temp_srt_slowness = st.number_input("Slowness", placeholder="Slowness for total-field/scattered-field source", key='t_srt_slowness', value=default_srt_slowness)
            temp_srt_int = st.checkbox("Make it integral of current", key='t_srt_int', value=default_srt_int)
        
        x, y, z = st.columns(3)
        temp_src_center = [None] * 3
        temp_src_center[0] = x.number_input("Center", label_visibility='visible', placeholder="X", value=default_center[0], key='t_src_center_x')
        temp_src_center[1] = y.number_input("Center", label_visibility='hidden', placeholder="Y", value=default_center[1], key='t_src_center_y')
        temp_src_center[2] = z.number_input("Center", label_visibility='hidden', placeholder="Z", value=default_center[2], key='t_src_center_z')
        x1, y1, z1 = st.columns(3)
        temp_src_size = [None] * 3
        temp_src_size[0] = x1.number_input("Size", label_visibility='visible', placeholder="X", value=default_size[0], key='t_src_size_x')
        temp_src_size[1] = y1.number_input("Size", label_visibility='hidden', placeholder="Y", value=default_size[1], key='t_src_size_y')
        temp_src_size[2] = z1.number_input("Size", label_visibility='hidden', placeholder="Z", value=default_size[2], key='t_src_size_z')
        with st.expander("Amplitude parameters"):
            temp_src_amp = st.text_input("Amplitude", placeholder="1.0", key='t_src_amp',value=default_amp)
            if st.checkbox("More advanced amplitude", key='t_src_amp_adv',value=default_amp_adv):
                amp_type_list = ["function", "file"]
                temp_src_amp_set = st.radio("Defined by", amp_type_list, horizontal=True, label_visibility='collapsed',key='t_src_amp_set', index=amp_type_list.index(default_amp_set))
                if temp_src_amp_set == "function":
                    st.text_area("Amplitude function", placeholder="e.g. exp(-t**2)", key='t_src_amp_func', value=default_amp_func)
                if temp_src_amp_set == "file":
                    st.file_uploader("Upload file", type=['h5', 'hdf5','npy'], key='t_src_amp_func_file', accept_multiple_files=False,value=default_amp_func_file)

    with src_right:
        st.write("Source parameters")
        if st.session_state.get('t_src_type') == None:
            st.error("Please specify source type.")
        if st.session_state.get('t_src_type') == "Custom":
            custom_comp_options = ["Ex", "Ey", "Ez", "Hx", "Hy", "Hz"]
            temp_src_comp = st.selectbox("Component", custom_comp_options, key='t_src_comp_custom',index=custom_comp_options.index(default_src_custom_comp))
        if st.session_state.get('t_src_type') == "Eigenmode":
            eig_comp_options = ['All', "Ex", "Ey", "Ez", "Hx", "Hy", "Hz"]
            temp_src_comp = st.selectbox("Component", eig_comp_options, key='t_src_comp_eig',index=eig_comp_options.index(default_src_eig_comp))
            temp_eig_band = st.number_input('Eigenband index', min_value=1, step=1, placeholder='The index of n of the desided band.', key='t_src_eig_band',value=default_src_eig_band)
            temp_eig_res = st.number_input('Eigenmode solver resolution', placeholder='Resolution for the eigenmode solver', key='t_src_eig_res',value=default_src_eig_res)
            temp_eig_tol = st.text_input('Eigenmode solver tolerance', placeholder='Tolerance for the eigenmode solver.', key='t_src_eig_tol',default = default_src_eig_tol)
            with st.expander("Eigenmode lattice"):
                x, y, z = st.columns(3)
                temp_eig_lat_size = [None] * 3
                temp_eig_lat_size[0] = x.number_input("Lattice size", label_visibility='visible', placeholder="X",key='t_src_eig_lat_sx',value=default_src_eig_lattice[0])
                temp_eig_lat_size[1] = y.number_input("Lattice size", label_visibility='hidden', placeholder="Y", key='t_src_eig_lat_sy',value=default_src_eig_lattice[1])
                temp_eig_lat_size[2] = z.number_input("Lattice size", label_visibility='hidden', placeholder="Z", key='t_src_eig_lat_sz',value=default_src_eig_lattice[2])
                temp_eig_lat_center = [None] * 3
                temp_eig_lat_center[0] = x.number_input("Lattice center", label_visibility='visible', placeholder="X",key='t_src_eig_lat_cx',value=default_src_eig_lattice_center[0])
                temp_eig_lat_center[1] = y.number_input("Lattice center", label_visibility='hidden', placeholder="Y", key='t_src_eig_lat_cy',value=default_src_eig_lattice_center[1])
                temp_eig_lat_center[2] = z.number_input("Lattice center", label_visibility='hidden', placeholder="Z", key='t_src_eig_lat_cz',value=default_src_eig_lattice_center[2])
            with st.expander("Eigenmode parity"):
                temp_eig_par = st.multiselect("Parity", ["No parity", "Even Z", "Odd Z", "Even Y", "ODD Y"], key='t_src_eig_parity', value=default_src_eig_parity)
            with st.expander("Direction, frequency and reciprocal for eigenmode"):
                temp_eig_match_freq = st.checkbox("Match frequency", key='t_src_eig_match_freq', value=default_src_eig_match_freq)
                eigen_dir_options = ["Auto", "X", "Y", "Z"]
                temp_eig_dir = st.selectbox("Direction", eigen_dir_options, key='t_src_eig_dir', index=eigen_dir_options.index(default_src_eig_dir))
                x, y, z = st.columns(3)
                temp_eig_kpt = [None] * 3
                temp_eig_kpt[0] = x.number_input("k-point", label_visibility='visible', placeholder="kx", key='t_src_eig_kptx', value=default_src_eig_kpt[0])
                temp_eig_kpt[1] = y.number_input("k-point", label_visibility='hidden', placeholder="ky", key='t_src_eig_kpty', value=default_src_eig_kpt[1])
                temp_eig_kpt[2] = z.number_input("k-point", label_visibility='hidden', placeholder="kz", key='t_src_eig_kptz', value=default_src_eig_kpt[2])
        if st.session_state.get('t_src_type') == "Gaussian":
            gau_comp_options = ['All', "Ex", "Ey", "Ez", "Hx", "Hy", "Hz"]
            temp_src_comp = st.selectbox("Component", gau_comp_options, index=gau_comp_options.index(default_src_gau_comp), key='t_src_comp_gau')
            temp_gau_w0 = st.number_input("Beam waist w0", key='t_src_gau_w0', value=default_src_gau_w0)
            temp_gau_x0 = [None] * 3
            temp_gau_kdir = [None] * 3
            temp_gau_E0 = [None] * 3

            with st.expander("Beam Vectors"):
                x, y, z = st.columns(3)
                temp_gau_x0[0] = x.number_input("Focus", label_visibility='visible', placeholder="X", key='t_src_gau_x0x', value=default_src_gau_x0[0])
                temp_gau_x0[1] = y.number_input("Focus", label_visibility='hidden', placeholder="Y",  key='t_src_gau_x0y', value=default_src_gau_x0[1])
                temp_gau_x0[2] = z.number_input("Focus", label_visibility='hidden', placeholder="Z", key='t_src_gau_x0z', value=default_src_gau_x0[2])
                temp_gau_kdir[0] = x.number_input("k direction", label_visibility='visible', placeholder="X", key='t_src_gau_kdirx', value=default_src_gau_kdir[0])
                temp_gau_kdir[1] = y.number_input("k direction", label_visibility='hidden', placeholder="Y", key='t_src_gau_kdiry', value=default_src_gau_kdir[1])
                temp_gau_kdir[2] = z.number_input("k direction", label_visibility='hidden', placeholder="Z", key='t_src_gau_kdirz', value=default_src_gau_kdir[2])
                temp_gau_E0[0] = x.number_input("Polarization", label_visibility='visible', placeholder="Ex", key='t_src_gau_E0x', value=default_src_gau_E0[0])
                temp_gau_E0[1] = y.number_input("Polarization", label_visibility='hidden', placeholder="Ey", key='t_src_gau_E0y', value=default_src_gau_E0[1])
                temp_gau_E0[2] = z.number_input("Polarization", label_visibility='hidden', placeholder="Ez", key='t_src_gau_E0z', value=default_src_gau_E0[2])

            temp_gau_2d = st.checkbox("Make it 2D", key='t_src_gau_2d')
