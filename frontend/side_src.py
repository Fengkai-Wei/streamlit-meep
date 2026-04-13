@st.dialog("Source configuration",width = 'medium')
def src_cfg():
    src_left,src_right = st.columns(s)
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
                temp_src_amp_set = st.radio("Amplitude defined by:",["function","file","data"],horizontal=True)
                if temp_src_amp_set == "function":
                    st.write("function")
                if temp_src_amp_set == "file":
                    st.write("file")
                if temp_src_amp_set == "data":
                    st.write("data")
    with src_right:
        pass






