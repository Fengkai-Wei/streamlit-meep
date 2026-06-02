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








@st.dialog("Source configuration", width='medium')
def src_cfg(old_cfg=None):
    if st.button("Confirm", type='primary', use_container_width=True):
        temp_src_type = st.session_state.get('t_src_type')
        temp_srt_type = st.session_state.get('t_srt_type')
        temp_src_center = [
            st.session_state.get('t_src_center_x'),
            st.session_state.get('t_src_center_y'),
            st.session_state.get('t_src_center_z'),
        ]
        temp_src_size = [
            st.session_state.get('t_src_size_x'),
            st.session_state.get('t_src_size_y'),
            st.session_state.get('t_src_size_z'),
        ]
        if temp_src_type is None:
            st.toast("Please select source type!", icon="⚠️")
        else:
            if temp_src_type == "Custom":
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
            else:
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

            new_source = Source(
                name=f"{temp_src_type} source",
                color="#ffffff",
                srct=srct,
                component=st.session_state.get('t_src_comp_custom') if temp_src_type == 'Custom' else st.session_state.get('t_src_comp_eig') if temp_src_type == 'Eigenmode' else st.session_state.get('t_src_comp_gau'),
                center=tuple(temp_src_center) if all(v is not None for v in temp_src_center) else None,
                volume=tuple(temp_src_size) if all(v is not None for v in temp_src_size) else None,
                amplitude=float(st.session_state.get('t_src_amp') or 1.0),
            )
            if 'sources' not in st.session_state:
                st.session_state.sources = []
            st.session_state.sources.append(new_source)
            st.toast(f"Source added: {new_source.name}", icon="✔️")
            clear_temp()
            st.rerun()

    src_left, divider, src_right = st.columns([1, 0.1, 1])
    with src_left:
        temp_src_type = st.selectbox("Type", ["Custom", "Eigenmode", "Gaussian"], index=None, key='t_src_type')
        with st.expander("Source-time config"):
            temp_srt_type = st.radio("Time type", ["Gaussian", "Continuous", "Custom",], key='t_srt_type', label_visibility='collapsed', horizontal=True)
            if temp_srt_type != "Custom":
                temp_srt_wl = st.number_input("Wavelength", placeholder="Wavelength of the source", key='t_src_f')
                temp_srt_width = st.number_input("Wavelength width", placeholder="Wavelength width", key='t_src_fd', value=0.0)
            else:
                temp_srt_func = st.text_area("Time function", placeholder="A custom time function of the source, e.g. exp(-t**2)", key='t_src_time_func')
                temp_srt_f = st.number_input("Frequency", placeholder="Frequency of the source", key='t_src_f_custom', value=0.0)
                temp_srt_fwidth = st.number_input("Frequency width", placeholder="Frequency width", key='t_src_fd_custom', value=1e50)
            with st.expander("Time responce"):
                temp_srt_start = st.number_input("Start time", placeholder="Time to turn on the source", key='t_src_time_start', value=0.0 if temp_srt_type != "Custom" else -1e20)
                temp_srt_end = st.number_input("End time", placeholder="Time to turn off the source", key='t_src_time_end', value=1e20)
                if temp_srt_type != "Custom":
                    temp_srt_cutoff = st.number_input("Cutoff", placeholder="Cutoff for continuous source", key='t_src_time_cutoff', value=None if temp_srt_type == "Continuous" else 5.0)
                if temp_srt_type == "Continuous":
                    temp_srt_slowness = st.number_input("Slowness", placeholder="Slowness for total-field/scattered-field source", key='t_src_time_slowness', value=3.0)
            temp_srt_int = st.checkbox("Make it integral of current", key='t_src_time_int', value=False)
        x, y, z = st.columns(3)
        temp_src_center = [None] * 3
        temp_src_center[0] = x.number_input("Center", label_visibility='visible', placeholder="X", value=None, key='t_src_center_x')
        temp_src_center[1] = y.number_input("Center", label_visibility='hidden', placeholder="Y", value=None, key='t_src_center_y')
        temp_src_center[2] = z.number_input("Center", label_visibility='hidden', placeholder="Z", value=None, key='t_src_center_z')
        x1, y1, z1 = st.columns(3)
        temp_src_size = [None] * 3
        temp_src_size[0] = x1.number_input("Size", label_visibility='visible', placeholder="X", value=None, key='t_src_size_x')
        temp_src_size[1] = y1.number_input("Size", label_visibility='hidden', placeholder="Y", value=None, key='t_src_size_y')
        temp_src_size[2] = z1.number_input("Size", label_visibility='hidden', placeholder="Z", value=None, key='t_src_size_z')
        with st.expander("Amplitude parameters"):
            temp_src_amp = st.text_input("Amplitude", placeholder="1.0")
            if st.checkbox("More advanced amplitude", key='t_src_amp_adv'):
                temp_src_amp_set = st.radio("defined by", ["function", "file", "data"], horizontal=True, label_visibility='collapsed')
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
            temp_src_comp = st.selectbox("Component", ["Ex", "Ey", "Ez", "Hx", "Hy", "Hz"], index=None, key='t_src_comp_custom')
        if st.session_state.get('t_src_type') == "Eigenmode":
            temp_src_comp = st.selectbox("Component", ['All', "Ex", "Ey", "Ez", "Hx", "Hy", "Hz"], index=0, key='t_src_comp_eig')

            temp_eig_band = st.number_input('Eigenband index', min_value=1, step=1, placeholder='The index of n of the desided band.', key='t_src_eig_band')
            temp_eig_res = st.number_input('Eigenmode solver resolution', placeholder='Resolution for the eigenmode solver', key='t_src_eig_res', value=2 * st.session_state.get('g_sim_res') if st.session_state.get('g_sim_res') != None else 20)
            temp_eig_tol = st.text_input('Eigenmode solver tolerance', placeholder='Tolerance for the eigenmode solver.', key='t_src_eig_tol', value='1e12')
            with st.expander("Eigenmode lattice"):
                x, y, z = st.columns(3)
                temp_eig_lat_size = [None] * 3
                temp_eig_lat_size[0] = x.number_input("Lattice size", label_visibility='visible', placeholder="X", value=None, key='t_src_eig_lat_sx')
                temp_eig_lat_size[1] = y.number_input("Lattice size", label_visibility='hidden', placeholder="Y", value=None, key='t_src_eig_lat_sy')
                temp_eig_lat_size[2] = z.number_input("Lattice size", label_visibility='hidden', placeholder="Z", value=None, key='t_src_eig_lat_sz')
                temp_eig_lat_center = [None] * 3
                temp_eig_lat_center[0] = x.number_input("Lattice center", label_visibility='visible', placeholder="X", value=None, key='t_src_eig_lat_cx')
                temp_eig_lat_center[1] = y.number_input("Lattice center", label_visibility='hidden', placeholder="Y", value=None, key='t_src_eig_lat_cy')
                temp_eig_lat_center[2] = z.number_input("Lattice center", label_visibility='hidden', placeholder="Z", value=None, key='t_src_eig_lat_cz')
            with st.expander("Eigenmode parity"):
                temp_eig_par = st.multiselect("Parity", ["No parity", "Even Z", "Odd Z", "Even Y", "ODD Y"], key='t_src_eig_parity', default=["No parity"])
            with st.expander("Direction, frequency and reciprocal for eigenmode"):
                temp_eig_match_freq = st.checkbox("Match frequency", key='t_src_eig_match_freq')
                temp_eig_dir = st.selectbox("Direction", ["Auto", "X", "Y", "Z"], key='t_src_eig_dir', index=0)
                x, y, z = st.columns(3)
                temp_eig_kpt = [None] * 3
                temp_eig_kpt[0] = x.number_input("k-point", label_visibility='visible', placeholder="kx", key='t_src_eig_kptx')
                temp_eig_kpt[1] = y.number_input("k-point", label_visibility='hidden', placeholder="ky", key='t_src_eig_kpty')
                temp_eig_kpt[2] = z.number_input("k-point", label_visibility='hidden', placeholder="kz", key='t_src_eig_kptz')
        if st.session_state.get('t_src_type') == "Gaussian":
            temp_src_comp = st.selectbox("Component", ['All', "Ex", "Ey", "Ez", "Hx", "Hy", "Hz"], index=0, key='t_src_comp_gau')
            temp_gau_w0 = st.number_input("Beam waist w0", value=None, key='t_src_gau_w0')
            temp_gau_2d = st.checkbox("Make it 2D", key='t_src_gau_2d')
            temp_gau_x0 = [None] * 3
            temp_gau_kdir = [None] * 3
            temp_gau_E0 = [None] * 3

            with st.expander("Focus, direction and polarization"):
                x, y, z = st.columns(3)
                temp_gau_x0[0] = x.number_input("Focus", label_visibility='visible', placeholder="X", value=None, key='t_src_gau_x0x')
                temp_gau_x0[1] = y.number_input("Focus", label_visibility='hidden', placeholder="Y", value=None, key='t_src_gau_x0y')
                temp_gau_x0[2] = z.number_input("Focus", label_visibility='hidden', placeholder="Z", value=None, key='t_src_gau_x0z')
                temp_gau_kdir[0] = x.number_input("Direction", label_visibility='visible', placeholder="X", value=None, key='t_src_gau_kdirx')
                temp_gau_kdir[1] = y.number_input("Direction", label_visibility='hidden', placeholder="Y", value=None, key='t_src_gau_kdiry')
                temp_gau_kdir[2] = z.number_input("Direction", label_visibility='hidden', placeholder="Z", value=None, key='t_src_gau_kdirz')
                temp_gau_E0[0] = x.number_input("Polarization", label_visibility='visible', placeholder="Ex", value=None, key='t_src_gau_E0x')
                temp_gau_E0[1] = y.number_input("Polarization", label_visibility='hidden', placeholder="Ey", value=None, key='t_src_gau_E0y')
                temp_gau_E0[2] = z.number_input("Polarization", label_visibility='hidden', placeholder="Ez", value=None, key='t_src_gau_E0z')

