import streamlit as st
import numpy as np
import pandas as pd
import uuid
import plotly.graph_objects as go
from utils import clear_temp,Serializable

OPACITY = 0.25


class MonitorLoader(Serializable):
    def __init__(
        self,
        name,
        color,
        fcen,
        df,
        nfreq,
        freq,
        **kwargs,
    ):
        self.name = name
        self.color = color
        self.fcen = fcen
        self.df = df
        self.nfreq = nfreq,
        self.freq = freq
        self.kwargs = kwargs


class FluxLoader(MonitorLoader):
    def __init__(
        self,
        name,
        color,
        fcen,
        df,
        nfreq,
        freq,
        FluxRegions,
        decimation_factor=0,
        **kwargs,
    ):
        super().__init__(
            name,color,fcen,df,nfreq,freq,**kwargs,
        )
        self.FluxRegions = FluxRegions
        self.decimation_factor = decimation_factor

class DFTLoader(MonitorLoader):
    def __init__(
        self,
        name,
        color,
        fcen,
        df,
        nfreq,
        freq,
        center,
        size,
        yee_grid=False,
        decimation_factor=0,
        persist=False,
        **kwargs,
    ):
        super().__init__(
            name, color, fcen, df, nfreq, freq, **kwargs,
            )
        self.center = center
        self.size = size
        self.yee_grid = yee_grid
        self.decimation_factor = decimation_factor
        self.persist = persist

class EnergyLoader(MonitorLoader):
    def __init__(
        self,
        name,
        color,
        fcen,
        df,
        nfreq,
        freq,
        EnergyRegions,
        decimation_factor=0,
        **kwargs,
    ):
        super().__init__(
            name,color,fcen,df,nfreq, freq, **kwargs,
        )
        self.EnergyRegions = EnergyRegions
        self.decimation_factor = decimation_factor



class ForceLoader(MonitorLoader):
    def __init__(
        self,
        name,
        color,
        fcen,
        df,
        nfreq,
        freq,
        ForceRegions,
        decimation_factor=0,
        **kwargs,
    ):
        super().__init__(
            name,color,fcen,df,nfreq,freq, **kwargs,
        )
        self.ForceRegions = ForceRegions
        self.decimation_factor = decimation_factor

class Near2FarLoader(MonitorLoader):
    def __init__(
        self,
        name,
        color,
        fcen,
        df,
        nfreq,
        freq,
        Near2FarRegions,
        nperiods=1,
        decimation_factor=0,
        **kwargs,
    ):
        super().__init__(
            name,color,fcen,df,nfreq,**kwargs,
        )
        self.freq = freq
        self.Near2FarRegions = Near2FarRegions
        self.nperiods = nperiods
        self.decimation_factor = decimation_factor

class FluxRegion(Serializable):
    def __init__(
        self,
        center,
        size,
        direction = 'Auto',
        weight = 1.0
    ):
        self.center = center
        self.size = size
        self.direction = direction
        self.weight = weight


ModeRegion = FluxRegion

Near2FarRegion = FluxRegion


class ForceRegion(FluxRegion):
    def __init__(
        self,
        center,
        size,
        direction = 'Auto',
        weight = 1.0,
    ):
        super().__init__(center, size, direction, weight)

class EnergyRegion(FluxRegion):
    def __init__(
        self,
        center,
        size,
        weight= 1.0,
    ):
        super().__init__(center, size, weight)


@st.dialog("Monitor configuration",width = 'medium')
def mnt_config(old_cfg=None,edit_idx=None):
    default_name = None
    default_color = None
    default_fcen = None
    default_df = None
    default_freq = None
    default_mnt_type = None
    default_freq_sweep_type = None
    default_nfreq = None
    default_flux_regions = None
    default_energy_regions = None
    default_force_regions = None
    default_near2far_regions = None
    default_mode_regions = None
    default_flux_decimation_factor = None
    default_energy_decimation_factor = None
    default_force_decimation_factor = None
    default_near2far_decimation_factor = None
    default_mode_decimation_factor = None
    default_near2far_nperiods = None
    default_dft_center = None
    default_dft_size = None
    default_dft_yee_grid = None
    default_dft_persist = None
    default_dft_decimation_factor = None
    if old_cfg is not None:
        default_color = getattr(old_cfg,'color',None)
        default_name = getattr(old_cfg,'name',None)

    if st.button("Confirm", type='primary', use_container_width=True):
        pass
    mnt_left,divider,mnt_right = st.columns([1, 0.1, 1])
    with mnt_left:
        st.text_input("Name", placeholder="Source name", key='t_src_name', value=default_name)
        temp_mnt_type_options = ['Flux', 'Energy', 'Force', 'Near2Far','DFT', 'Mode']
        temp_mnt_type = st.selectbox("Type", temp_mnt_type_options,index=temp_mnt_type_options.index(default_mnt_type) if default_mnt_type is not None else None, key='t_mnt_type')
        freq_options = ['cen+df','list']
        temp_freq_select = st.radio('Frequency sweep type',freq_options,index=freq_options.index(default_freq_sweep_type) if default_freq_sweep_type is not None else None,key='t_freq_sweep_type')
        if temp_freq_select == 'cen+df':
            temp_mnt_fcen = st.number_input('Center frequency',placeholder='Center frequency of monitor',key='t_mnt_fcen')
            temp_mnt_df = st.number_input('Bandwidth',placeholder='Bandwidth of monitor',key='t_mnt_df')
            temp_mnt_nfreq = st.number_input('Number of frequencies',placeholder='Number of frequencies',key='t_mnt_nfreq')
        elif temp_freq_select == 'list':
            temp_mnt_freq_list = st.text_area('List of frequencies',placeholder='List of frequencies. E.g. [np.sin(x) for x in [0,1,2,3]]',key='t_mnt_freq_list',value=default_freq)
        temp_mnt_color = st.color_picker("Pick a color", value=default_color or "#000000", key="t_mnt_color")
    
    with divider:
        pass

    with mnt_right:
        mnt_type = st.session_state.get('t_mnt_type')

        if mnt_type == 'Flux':
            pass
        elif mnt_type == 'Energy':
            pass
        elif mnt_type == 'Force':
            pass
        elif mnt_type == 'Near2Far':
            pass
        elif mnt_type == 'Mode':
            pass
        elif mnt_type == 'DFT':
            pass

        





