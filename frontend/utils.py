import streamlit as st
import pandas as pd

FRONTEND_ONLY_ATTRS = {"name", "uid", "color", "opacity"}
class Serializable:
    def to_dict(self) -> dict:
        backend_data = {}
        for key, value in self.__dict__.items():
            if key.startswith("_"):
                continue
            if key not in FRONTEND_ONLY_ATTRS:
                if hasattr(value, "to_dict"):
                    backend_data[key] = value.to_dict()
                elif: isinstance(value, (list, tuple)):
                    backend_data[key] = [item.to_dict() if hasattr(item, "to_dict") else item for item in value]
                else:
                    backend_data[key] = value
        backend_data['type'] = type(self).__name__.lower()
        return backend_data


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
        main_rows = []
        sub_rows = []
        main_rows.append(["Type", type(obj).__name__])
        
        # Skip these attributes based on object type
        skip_attrs = {'uid', 'name', 'color','opacity','volume','srct'}
        
        for attr, value in obj.__dict__.items():         
            if attr in skip_attrs:
                continue
            display_value = str(value)  # 转换为字符串以确保 Arrow 兼容性
            if obj_type == 'geometry':
                geo_main_attr = {'material','center'}
                if attr in geo_main_attr:                 
                    main_rows.append([attr, display_value])
                else:
                    sub_rows.append([attr, display_value])

            if obj_type == 'source':
                src_main_attr = {'center','size','amplitude','amp_func','amp_func_file'}
                if attr in src_main_attr:
                    main_rows.append([attr, display_value])
                else:
                    sub_rows.append([attr, display_value])
        
        with st.expander("Main details",expanded=True):
            if main_rows:
                df_main = pd.DataFrame(main_rows, columns=["attribute", "value"])
                st.table(df_main)
            else:
                st.write("No details available.")
        if obj_type == 'source':
            with st.expander("Source-time config"):
                srct = obj.srct
                srct_type = type(srct).__name__
                srct_rows = []
                srct_rows.append(["Type", srct_type])
                for attr, value in srct.__dict__.items():
                    srct_rows.append([attr, str(value)])
                df_srct = pd.DataFrame(srct_rows, columns=["attribute", "value"])
                st.table(df_srct)

        with st.expander("Sub details"):
            if sub_rows:
                df_sub = pd.DataFrame(sub_rows, columns=["attribute", "value"])
                st.table(df_sub)
            else:
                st.write("No details available.")


        # Color configuration for geometry and source
        if obj_type in ['geometry', 'source']:
            # Color Picker
            new_color = st.color_picker("Color", value=obj.color, key=f"{key_prefix}_color")
            if new_color != obj.color:
                obj.color = new_color
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
