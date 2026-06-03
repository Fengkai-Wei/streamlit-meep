import streamlit as st
import pandas as pd


def clear_temp():
    pattern = ("temp_", "tg_","t_")
    for key in list(st.session_state.keys()):
        if key.startswith(pattern):
            del st.session_state[key]


def card_widget(obj, obj_type, idx, edit_callback=None, top=False, bottom=False):
    """
    Display object card widget with details and control buttons.
    
    Args:
        obj: The object to display (geometry or source)
        obj_type: Type of object ('geometry' or 'source')
        idx: Index in the list
        edit_callback: Callback function to call when edit button is pressed
        top: Whether this is the top item
        bottom: Whether this is the bottom item
    """
    # 注入局部 CSS，专门针对 popover 内部的控制按钮
    st.markdown("""
        <style>
            /* 定位 popover 内部的按钮 */
            div[data-testid="stPopoverBody"] div.stButton > button {
                background-color: transparent !important;
                color: #FFFFFF !important; /* 保持主题色图标 */
                border: none !important;
                width: auto !important;
                height: 2rem !important;
                padding: 0px 8px !important;
                transform: none !important; /* 禁用全局 CSS 中的位移效果 */
            }
            /* 悬停效果：轻微背景色 */
            div[data-testid="stPopoverBody"] div.stButton > button:hover {
                transform: scale(1.1) !important;
            }
        </style>
    """, unsafe_allow_html=True)

    key_prefix = f'{obj_type}list_{getattr(obj, "uid", idx)}'
    with st.popover(obj.name, width='stretch', key=key_prefix):
        rows = []
        
        # Skip these attributes based on object type
        skip_attrs = {'uid', 'name', 'color','opacity','volume'}
        if obj_type == 'geometry':
            #skip_attrs.update(['opacity'])
            pass
        
        for attr, value in obj.__dict__.items():
            print(attr,value)
            if attr in skip_attrs:
                continue
            rows.append([attr, value])

        if rows:
            df = pd.DataFrame(rows, columns=["attribute", "value"])
            st.table(df)
        else:
            st.write("No details available.")

        # Opacity slider for geometry
        if obj_type == 'geometry':
            opacity = st.slider(
                "Opacity", 
                min_value=0.0, 
                max_value=1.0, 
                value=getattr(obj, "opacity", 1.0), 
                step=0.05, 
                key=f"{key_prefix}_opacity"
            )
            if opacity != obj.opacity:
                obj.opacity = opacity
                if obj_type == 'geometry':
                    st.session_state.geoms[idx] = obj
                elif obj_type == 'source':
                    st.session_state.sources[idx] = obj

        # Control buttons
        with st.container(horizontal=True, border=False, gap='xxsmall'):
            edit_pressed = st.button("⚙️", type="secondary", key=f'{key_prefix}_edit')
            delete_pressed = st.button("🗑️", type="secondary", key=f'{key_prefix}_delete')
            move_up_pressed = False
            move_down_pressed = False
            if not top:
                move_up_pressed = st.button("🔼", type="secondary", key=f'{key_prefix}_move_up')
            if not bottom:
                move_down_pressed = st.button("🔽", type="secondary", key=f'{key_prefix}_move_down')

    if edit_pressed:
        if edit_callback:
            edit_callback(obj, idx)

    if delete_pressed:
        if obj_type == 'geometry':
            st.session_state.geoms.pop(idx)
        elif obj_type == 'source':
            st.session_state.sources.pop(idx)
        st.rerun()

    if move_up_pressed and idx > 0:
        if obj_type == 'geometry':
            st.session_state.geoms[idx - 1], st.session_state.geoms[idx] = st.session_state.geoms[idx], st.session_state.geoms[idx - 1]
        elif obj_type == 'source':
            st.session_state.sources[idx - 1], st.session_state.sources[idx] = st.session_state.sources[idx], st.session_state.sources[idx - 1]
        st.rerun()

    if move_down_pressed and idx < (len(st.session_state.geoms) if obj_type == 'geometry' else len(st.session_state.sources)) - 1:
        if obj_type == 'geometry':
            st.session_state.geoms[idx + 1], st.session_state.geoms[idx] = st.session_state.geoms[idx], st.session_state.geoms[idx + 1]
        elif obj_type == 'source':
            st.session_state.sources[idx + 1], st.session_state.sources[idx] = st.session_state.sources[idx], st.session_state.sources[idx + 1]
        st.rerun()
