import streamlit as st
import numpy as np
import pandas as pd
import uuid
import plotly.graph_objects as go
from utils import clear_temp


OPACITY = 0.4


def src_trace_checker(source):
    """根据 Source 对象的 center 和 size 生成 Plotly 轨迹。"""
    if isinstance(source, GaussianSource):
        return gaussian_trace(source)
    elif isinstance(source, EigenmodeSource):
        return eigenmode_trace(source)
    else:
        return source_trace(source)


def _get_common_source_traces(source):
    """私有辅助函数：处理所有光源通用的几何形态和 amp_func 热力图绘制。"""
    traces = []
    
    center = np.array([float(x) if x is not None else 0.0 for x in getattr(source, 'center', [0,0,0])])
    size = np.array([float(x) if x is not None else 0.0 for x in getattr(source, 'size', [0,0,0])])
    non_zero_thres = 1e-8
    name = getattr(source, 'name', 'unknown')
    color = getattr(source, 'color', 'yellow')
    opacity = getattr(source, 'opacity', 0.5)
    
    # 计算非零维度的数量
    active_dims = [i for i, s in enumerate(size) if s > non_zero_thres]
    dims = len(active_dims)
    
    if dims == 0:
        traces.append(go.Scatter3d(
            x=[center[0]], y=[center[1]], z=[center[2]],
            mode='markers',
            marker=dict(size=12, color=color, symbol='circle'),
            opacity=opacity,
            name=name, showlegend=True
        ))
    elif dims == 1:
        idx = np.argmax(size > non_zero_thres)
        p0, p1 = center.copy(), center.copy()
        p0[idx] -= size[idx] / 2
        p1[idx] += size[idx] / 2
        traces.append(go.Scatter3d(
            x=[p0[0], p1[0]], y=[p0[1], p1[1]], z=[p0[2], p1[2]],
            mode='lines',
            line=dict(width=6, color=color),
            opacity=opacity,
            name=name, showlegend=True
        ))
    elif dims == 2:  # 面光源：统一使用 Surface 实现 Heatmap
        res = 50  # 热力图采样分辨率
        d1, d2 = active_dims
        v1 = np.linspace(-size[d1]/2, size[d1]/2, res)
        v2 = np.linspace(-size[d2]/2, size[d2]/2, res)
        V1, V2 = np.meshgrid(v1, v2)

        # 构建 3D 坐标阵列
        X = np.full((res, res), center[0])
        Y = np.full((res, res), center[1])
        Z = np.full((res, res), center[2])
        grids = [X, Y, Z]
        grids[d1] = center[d1] + V1
        grids[d2] = center[d2] + V2

        # 计算 amp_func
        surfacecolor = None
        customdata = None
        if getattr(source, 'amp_func', None):
            amps, phases = [], []
            # 展开进行批量计算
            pts_rel = np.zeros((res*res, 3))
            pts_rel[:, d1] = V1.flatten()
            pts_rel[:, d2] = V2.flatten()
            
            for p in pts_rel:
                try:
                    val = complex(source.amp_func(p))
                    amps.append(abs(val))
                    phases.append(np.angle(val))
                except:
                    amps.append(1.0); phases.append(0.0)
            
            surfacecolor = np.array(phases).reshape(res, res)
            customdata = np.array(amps).reshape(res, res)

        traces.append(go.Surface(
            x=grids[0], y=grids[1], z=grids[2],
            surfacecolor=surfacecolor,
            colorscale='Twilight' if surfacecolor is not None else [[0, color], [1, color]],
            cmin=-np.pi, cmax=np.pi,
            opacity=opacity,
            name=name,
            showscale=True if surfacecolor is not None else False,
            colorbar=dict(title="Phase", x=1.1, len=0.5) if surfacecolor is not None else None,
            customdata=customdata,
            hovertemplate="Phase: %{surfacecolor:.3f} rad<br>Amp: %{customdata:.3f}<extra></extra>" if customdata is not None else None,
            showlegend=True
        ))

    elif dims == 3:  # 体光源：使用 Volume 实现 3D Heatmap
        res = 50
        v1 = np.linspace(-size[0]/2, size[0]/2, res)
        v2 = np.linspace(-size[1]/2, size[1]/2, res)
        v3 = np.linspace(-size[2]/2, size[2]/2, res)
        V1, V2, V3 = np.meshgrid(v1, v2, v3)
        
        val_field = np.zeros_like(V1)
        if getattr(source, 'amp_func', None):
            for i in range(res):
                for j in range(res):
                    for k in range(res):
                        p = np.array([v1[i], v2[j], v3[k]])
                        val_field[j, i, k] = np.angle(complex(source.amp_func(p)))
        
        traces.append(go.Volume(
            x=(V1 + center[0]).flatten(),
            y=(V2 + center[1]).flatten(),
            z=(V3 + center[2]).flatten(),
            value=val_field.flatten(),
            isomin=-np.pi, isomax=np.pi,
            opacity=0.2,
            surface_count=10,
            colorscale='Twilight',
            name=f"{name} (Vol Heatmap)",
            showscale=False
        ))
    return traces


def _get_direction_vector(source):
    """私有辅助函数：根据 source.direction 或 size 平面自动获取法线向量。"""
    # 显式检查 direction 属性，如果没有则默认为 'No'
    dir_val = getattr(source, 'direction', 'No') or 'No'
    name = getattr(source, 'name', 'unknown')

    if dir_val == 'No' or dir_val not in ['X', 'Y', 'Z', 'Auto']:
        return None
    
    if dir_val == 'Auto':
        size = np.array([float(x) if x is not None else 0.0 for x in getattr(source, 'size', [0,0,0])])
        zeros = np.where(size < 1e-8)[0]
        v = np.zeros(3)
        if len(zeros) > 0:
            v[zeros[0]] = 1.0
        else:
            v[2] = 1.0
        res_vec = v
    else:
        dir_map = {'X': [1,0,0], 'Y': [0,1,0], 'Z': [0,0,1]}
        res_vec = np.array(dir_map.get(dir_val, [0,0,1]), dtype=float)

    # 如果你想确认，取消下面一行的注释。你会看到不同光源的输出。
    # print(f"DEBUG [{name}]: dir_vec is {res_vec}")
    return res_vec


def _get_pol_vector_traces(source, vec, color='red', origin=None, kdir=None):
    """私有辅助函数：绘制偏振方向矢量箭头。"""
    traces = []
    name = getattr(source, 'name', 'unknown')

    if origin is None:
        origin = np.array([float(x) if x is not None else 0.0 for x in getattr(source, 'center', [0,0,0])])
    
    # 获取归一化的传播方向用于并行检查
    k_norm_check = None
    if kdir is not None and np.linalg.norm(kdir) > 1e-8:
        k_norm_check = kdir / np.linalg.norm(kdir)

    comp = getattr(source, 'component', 'Ex')

    # 0. 绘制 Direction 辅助线段 (黑虚线双头箭头)
    dir_vec = _get_direction_vector(source)

    if dir_vec is not None:
        is_parallel = False
        if k_norm_check is not None:
            # 使用较宽松的阈值 (0.99) 处理浮点数误差
            is_parallel = np.abs(np.dot(dir_vec, k_norm_check)) > 0.99
        
        # 线段长度 1.5，中点在 origin
        p0 = origin - 2/3 * dir_vec
        p1 = origin + 2/3 * dir_vec
        
        # 绘制虚线

        d_text = ["", f"<b>{name} dir</b>"] if not is_parallel else ["", ""]
        traces.append(go.Scatter3d(
            x=[p0[0], p1[0]], y=[p0[1], p1[1]], z=[p0[2], p1[2]],
            mode='lines+text' if not is_parallel else 'lines',
            line=dict(color='black', width=3, dash='dash'),
            text=d_text,
            textposition="top center",
            textfont=dict(size=8, color='black', weight='bold'),
            name=f"{name} Direction", showlegend=False
        ))

        # 绘制两端的箭头
        for tip_p, tip_v in [(p1, dir_vec), (p0, -dir_vec)]:
            traces.append(go.Cone(
                x=[tip_p[0]], y=[tip_p[1]], z=[tip_p[2]],
                u=[tip_v[0]], v=[tip_v[1]], w=[tip_v[2]],
                sizemode="absolute", sizeref=0.2, anchor="tip",
                showscale=False, colorscale=[[0, 'black'], [1, 'black']],
                name="Direction Head", showlegend=False
            ))


    # 1. 颜色与长度映射
    arrow_len = 1.0
    if comp in ['Ex', 'Ey', 'Ez']:
        color = 'orange'
        arrow_len = 0.5
    elif comp in ['Hx', 'Hy', 'Hz']:
        color = 'blue'
        arrow_len = 0.5

    # 2. 检查相位螺旋 (针对复数向量，如 beam_E0)
    v_numeric = np.array(vec, dtype=complex)
    if np.any(np.abs(np.imag(v_numeric)) > 1e-8):
        # 获取传播方向 k
        k_vec = np.array([0, 0, 1])
        if kdir is not None and np.linalg.norm(kdir) > 1e-8:
            k_vec = np.array(kdir, dtype=float)
        elif hasattr(source, 'beam_kdir'):
            k_vec = np.array(source.beam_kdir, dtype=float)
        elif hasattr(source, 'eig_kpoint'):
            k_raw = np.array(source.eig_kpoint, dtype=float)
            if np.linalg.norm(k_raw) > 1e-8: k_vec = k_raw
            else:
                d_map = {'X':[1,0,0],'Y':[0,1,0],'Z':[0,0,1]}
                k_vec = np.array(d_map.get(getattr(source, 'direction', 'Z'), [0,0,1]))
        
        k_norm = k_vec / (np.linalg.norm(k_vec) + 1e-12)
        
        # 强制旋转轴为 kdir：通过投影确保极化矢量垂直于传播方向
        v_trans = v_numeric - np.sum(v_numeric * k_norm) * k_norm
        v_target = v_trans if np.linalg.norm(v_trans) > 1e-8 else v_numeric

        # 采样生成螺旋线 (正弦螺线效果，展示 2 个周期，旋转轴与方向设为 kdir)
        num_pts = 100
        cycles = 2
        t = np.linspace(0, 1, num_pts)
        spiral_pts = []
        for val_t in t:
            # 旋转相位: exp(1j * ...)，使旋转轴和方向与 kdir 耦合
            phi = 2 * np.pi * cycles * val_t
            phase = np.exp(1j * phi)
            offset = np.real(v_target * phase)
            if np.linalg.norm(v_target) > 1e-8:
                offset = (offset / np.linalg.norm(v_target)) * 0.3
            spiral_pts.append(origin + val_t * arrow_len * k_norm + offset)
        
        spiral_pts = np.array(spiral_pts)
        traces.append(go.Scatter3d(
            x=spiral_pts[:, 0], y=spiral_pts[:, 1], z=spiral_pts[:, 2],
            mode='lines', line=dict(color=color, width=5),
            name=f"{name} phase spiral", showlegend=False
        ))
        # 末端箭头
        tip = spiral_pts[-1]
        v_tip = spiral_pts[-1] - spiral_pts[-2]
        v_tip /= (np.linalg.norm(v_tip) + 1e-12)
        traces.append(go.Cone(
            x=[tip[0]], y=[tip[1]], z=[tip[2]],
            u=[v_tip[0]], v=[v_tip[1]], w=[v_tip[2]],
            sizemode="absolute", sizeref=0.15, anchor="tip",
            showscale=False, colorscale=[[0, color], [1, color]],
            name="Spiral Head", showlegend=False
        ))
        return traces

    # 3. 'All' 情况：灰色球壳 (仅在非螺旋线时触发)
    if comp == 'All':
        r = 0.1
        theta = np.linspace(0, 2*np.pi, 20)
        phi = np.linspace(0, np.pi, 20)
        THETA, PHI = np.meshgrid(theta, phi)
        sp_x = origin[0] + r * np.sin(PHI) * np.cos(THETA)
        sp_y = origin[1] + r * np.sin(PHI) * np.sin(THETA)
        sp_z = origin[2] + r * np.cos(PHI)
        traces.append(go.Surface(
            x=sp_x, y=sp_y, z=sp_z,
            colorscale=[[0, 'gray'], [1, 'gray']],
            showscale=False, opacity=0.5,
            name=f"{name} (All)", showlegend=False
        ))
        return traces

    # 4. 普通实数矢量箭头
    vec_real = np.real(v_numeric)
    if np.linalg.norm(vec_real) > 1e-8:
        vec_norm = (vec_real / np.linalg.norm(vec_real)) * arrow_len
        
        traces.append(go.Scatter3d(
            x=[origin[0], origin[0] + vec_norm[0]],
            y=[origin[1], origin[1] + vec_norm[1]],
            z=[origin[2], origin[2] + vec_norm[2]],
            mode='lines+text',
            text=["", f"<b>{name} pol</b>"],
            textposition="top center",
            textfont=dict(size=14, color='black', weight='bold'),
            line=dict(width=5, color=color),
            name=f"{name} Pol ({comp})", showlegend=False
        ))

        traces.append(go.Cone(
            x=[origin[0] + vec_norm[0]], y=[origin[1] + vec_norm[1]], z=[origin[2] + vec_norm[2]],
            u=[vec_norm[0]], v=[vec_norm[1]], w=[vec_norm[2]],
            sizemode="absolute", sizeref=0.3 * arrow_len, anchor="tip",
            showscale=False, colorscale=[[0, color], [1, color]],
            name="Polarization Head", showlegend=False
        ))
    return traces


def source_trace(source):
    """通用 Source 轨迹计算。"""
    traces = _get_common_source_traces(source)
    
    comp = getattr(source, 'component', 'Ex')
    vec = np.array([0.0, 0.0, 0.0])
    comp_map = {
        'Ex': [1,0,0], 'Ey': [0,1,0], 'Ez': [0,0,1],
        'Hx': [1,0,0], 'Hy': [0,1,0], 'Hz': [0,0,1]
    }
    
    if comp in comp_map:
        vec = np.array(comp_map[comp], dtype=float)

    traces += _get_pol_vector_traces(source, vec)
    return traces


def eigenmode_trace(source):
    """EigenmodeSource 轨迹计算。"""
    # 1. 获取通用的几何轨迹 (Point/Line/Surface/Volume)
    traces = _get_common_source_traces(source)
    
    center = np.array([float(x) if x is not None else 0.0 for x in getattr(source, 'center', [0,0,0])])
    name = getattr(source, 'name', 'Eigenmode')

    # 2. 绘制传播方向 (k-vector)
    # 传播方向仅根据 eig_kpoint 绘制，不再回退到 direction
    k_vec = np.array([float(x) if x is not None else 0.0 for x in getattr(source, 'eig_kpoint', [0,0,0])])
    
    if np.linalg.norm(k_vec) > 1e-8:
        k_norm = k_vec / np.linalg.norm(k_vec)

        # 检查是否与 solver direction 平行
        dir_v = _get_direction_vector(source)
        k_suffix = " (same dir)" if dir_v is not None and np.abs(np.dot(dir_v, k_norm)) > 1-1e-8 else ""

        traces.append(go.Scatter3d(
            x=[center[0], center[0] + k_norm[0]],
            y=[center[1], center[1] + k_norm[1]],
            z=[center[2], center[2] + k_norm[2]],
            mode='lines+text',
            text=["", f"<b>{name} k-dir</b>" + k_suffix],
            textposition="top center",
            textfont=dict(size=14, color='black', weight='bold'),
            line=dict(width=5, color='blue'),
            name=f"{name} k-dir",
            showlegend=False
        ))
        traces.append(go.Cone(
            x=[center[0] + k_norm[0]], y=[center[1] + k_norm[1]], z=[center[2] + k_norm[2]],
            u=[k_norm[0]], v=[k_norm[1]], w=[k_norm[2]],
            sizemode="absolute", sizeref=0.3, anchor="tip", showscale=False,
            colorscale=[[0, 'blue'], [1, 'blue']],
            name="k-dir Head", showlegend=False
        ))

    # 3. 绘制偏振方向 (Component)
    comp = getattr(source, 'component', 'Ex')
    comp_map = {'Ex':[1,0,0],'Ey':[0,1,0],'Ez':[0,0,1],'Hx':[1,0,0],'Hy':[0,1,0],'Hz':[0,0,1]}
    if comp in comp_map:
        traces += _get_pol_vector_traces(source, np.array(comp_map[comp], dtype=float), kdir=k_vec if np.linalg.norm(k_vec) > 1e-8 else None)
    elif comp == 'All':
        traces += _get_pol_vector_traces(source, np.array([0.0, 0.0, 0.0]), kdir=k_vec if np.linalg.norm(k_vec) > 1e-8 else None)


    # 4. 可选：绘制 Eigenmode Lattice (计算网格范围)
    lat_size = np.array([float(x) if x is not None else 0.0 for x in getattr(source, 'eig_lattice_size', [0,0,0])])
    if np.any(lat_size > 1e-8):
        # 如果没设置 lattice_center，默认跟随 source.center
        lat_center = np.array([float(x) if x is not None else 0.0 for x in getattr(source, 'eig_lattice_center', center)])
        
        # 构建 12 条边的线框
        x_r = [lat_center[0] - lat_size[0]/2, lat_center[0] + lat_size[0]/2]
        y_r = [lat_center[1] - lat_size[1]/2, lat_center[1] + lat_size[1]/2]
        z_r = [lat_center[2] - lat_size[2]/2, lat_center[2] + lat_size[2]/2]
        
        bx, by, bz = [], [], []
        # 定义路径 (底面 -> 顶面 -> 立柱)
        path = [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1),(0,0,1),None,(1,0,0),(1,0,1),None,(1,1,0),(1,1,1),None,(0,1,0),(0,1,1)]
        for p in path:
            if p is None: bx.append(None); by.append(None); bz.append(None)
            else: bx.append(x_r[p[0]]); by.append(y_r[p[1]]); bz.append(z_r[p[2]])
            
        traces.append(go.Scatter3d(
            x=bx, y=by, z=bz, mode='lines',
            line=dict(color='gray', width=2, dash='dot'),
            name=f"{name} Lattice", showlegend=False
        ))

    return traces


def gaussian_trace(source):
    """GaussianSource 轨迹计算，特殊处理 'All' 分量的矢量显示。"""
    #traces = _get_common_source_traces(source)
    traces = []
    center = np.array([float(x) if x is not None else 0.0 for x in getattr(source, 'center', [0,0,0])])
    
    # 提前计算全局焦点坐标 (center + beam_x0)
    rel_x0 = np.array(getattr(source, 'beam_x0', [0,0,0]), dtype=float)
    global_x0 = center + rel_x0

    # 提前定义 kdir，供 _get_pol_vector_traces 和后续外壳绘制使用，防止 NameError
    kdir = np.array(getattr(source, 'beam_kdir', [0,0,0]), dtype=float)

    comp = getattr(source, 'component', 'All')
    vec = np.array([0.0, 0.0, 0.0])
    comp_map = {'Ex': [1,0,0], 'Ey': [0,1,0], 'Ez': [0,0,1], 'Hx': [1,0,0], 'Hy': [0,1,0], 'Hz': [0,0,1]}

    if comp in comp_map:
        vec = np.array(comp_map[comp], dtype=float)
    elif comp == 'All' and hasattr(source, 'beam_E0'):
        vec = np.array([complex(x) if x is not None else 0.0j for x in source.beam_E0])

    # 将偏振矢量箭头起始点设在焦点的全局坐标处
    traces += _get_pol_vector_traces(source, vec, origin=global_x0, kdir=kdir if np.linalg.norm(kdir) > 1e-8 else None)

    # --- 新增：绘制 Gaussian Beam 3D 外壳 ---
    w0 = getattr(source, 'beam_w0', None)
    
    if w0 and np.linalg.norm(kdir) > 1e-8:
        # 获取波长 (从 srct 中提取，默认为 1.0)
        srct = getattr(source, 'srct', None)
        freq = getattr(srct, 'frequency', 1.0) or 1.0
        
        # 计算瑞利距离 zR = pi * w0^2 * freq
        zr = np.pi * (float(w0)**2) * freq
        
        # 定义局部坐标系：z 为传播方向，采样范围设为 3 倍瑞利距离
        z_vals = np.linspace(-3 * zr, 3 * zr, 30)
        theta_vals = np.linspace(0, 2 * np.pi, 30)
        Z_loc, Theta = np.meshgrid(z_vals, theta_vals)
        
        # 计算随 z 变化的半径 W(z)
        W = float(w0) * np.sqrt(1 + (Z_loc / zr)**2)
        X_loc = W * np.cos(Theta)
        Y_loc = W * np.sin(Theta)
        
        # 构建旋转矩阵：将标准 Z 轴 [0,0,1] 旋转至 beam_kdir
        z_axis = np.array([0, 0, 1])
        target_k = kdir / np.linalg.norm(kdir)
        
        if np.allclose(z_axis, target_k):
            R = np.eye(3)
        elif np.allclose(z_axis, -target_k):
            R = np.diag([1, -1, -1])
        else:
            v = np.cross(z_axis, target_k)
            c = np.dot(z_axis, target_k)
            s = np.linalg.norm(v)
            v_x = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
            R = np.eye(3) + v_x + v_x @ v_x * ((1 - c) / (s**2))
            
        # 变换到全局坐标
        pts_loc = np.stack([X_loc.flatten(), Y_loc.flatten(), Z_loc.flatten()])
        pts_glob = (R @ pts_loc).T + global_x0
        
        X_glob = pts_glob[:, 0].reshape(Z_loc.shape)
        Y_glob = pts_glob[:, 1].reshape(Z_loc.shape)
        Z_glob = pts_glob[:, 2].reshape(Z_loc.shape)

        # 绘制 kdir 矢量箭头 (蓝色)，起点在 global_x0
        k_norm = kdir / np.linalg.norm(kdir)

        # 检查是否与 solver direction 平行
        dir_v = _get_direction_vector(source)
        k_suffix = " (same dir)" if dir_v is not None and np.abs(np.dot(dir_v, k_norm)) > 0.999 else ""

        traces.append(go.Scatter3d(
            x=[global_x0[0], global_x0[0] + k_norm[0]],
            y=[global_x0[1], global_x0[1] + k_norm[1]],
            z=[global_x0[2], global_x0[2] + k_norm[2]],
            mode='lines+text',
            line=dict(width=5, color='blue'),
            text=["", f"<b>{source.name} k-dir</b>" + k_suffix],
            textposition="top center",
            textfont=dict(size=14, color='black', weight='bold'),
            name=f"{source.name} k-dir",
            showlegend=False
        ))
        traces.append(go.Cone(
            x=[global_x0[0] + k_norm[0]],
            y=[global_x0[1] + k_norm[1]],
            z=[global_x0[2] + k_norm[2]],
            u=[k_norm[0]], v=[k_norm[1]], w=[k_norm[2]],
            sizemode="absolute", sizeref=0.3,
            anchor="tip",
            showscale=False,
            colorscale=[[0, 'blue'], [1, 'blue']],
            name="k-dir Head",
            showlegend=False
        ))
        
        traces.append(go.Surface(
            x=X_glob, y=Y_glob, z=Z_glob,
            colorscale=[[0, 'rgba(0,255,100,0.7)'], [1, 'rgba(0,255,100,0.3)']],
            showscale=False,
            name=f"{source.name} Envelope",
            opacity=0.3,
            showlegend=True
        ))

    return traces








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
        amp_func_file=None,
        k_vec = np.array([0, 0, 0]),
        #amp_data=None,
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
        #self.amp_data = amp_data
        self.uid = uuid.uuid4().hex

class EigenmodeSource(Source):
    def __init__(
        self,
        name,
        color,
        srct,
        opacity,
        amplitude=1.0,
        center=None,
        volume=None,
        eig_lattice_size=None,
        eig_lattice_center=None,
        component='All',
        direction='Auto',
        eig_band=1,
        eig_kpoint=np.array([0, 0, 0]),
        eig_match_freq=True,
        eig_parity='No parity',
        eig_resolution=0,
        eig_tolerance=1e-12,
        **kwargs,
    ):
        super().__init__(name, color, srct, component=component, center=center, volume=volume, amplitude=amplitude, opacity=opacity, **kwargs)
        self.eig_lattice_size = eig_lattice_size
        self.eig_lattice_center = eig_lattice_center
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
        opacity,
        amplitude=1.0,
        center=None,
        volume=None,
        component='All',
        beam_x0=np.array([0, 0, 0]),
        beam_kdir=np.array([0, 0, 0]),
        beam_w0=None,
        beam_E0=np.array([0, 0, 0]),
        **kwargs,
    ):
        super().__init__(name, color, srct, component=component, center=center, volume=volume, amplitude=amplitude, opacity=opacity, **kwargs)
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
        opacity,
        amplitude=1.0,
        center=None,
        volume=None,
        component='All',
        beam_x0=np.array([0, 0, 0]),
        beam_kdir=np.array([0, 0, 0]),
        beam_w0=None,
        beam_E0=np.array([0, 0, 0]),
        **kwargs,
    ):
        super().__init__(name, color, srct, component=component, center=center, volume=volume, amplitude=amplitude, opacity=opacity, **kwargs)
        self.beam_x0 = beam_x0
        self.beam_kdir = beam_kdir
        self.beam_w0 = beam_w0
        self.beam_E0 = beam_E0








@st.dialog("Source configuration", width='large')
def src_cfg(old_cfg=None, edit_idx=None):
    # --- 初始化默认值 ---
    # --- 1. Base values ---
    default_color = None
    default_src_type = None
    default_srt_type = None
    default_center = [None, None, None]
    default_size = [None, None, None]
    default_name = None
    # --- 2. Source-time related ---
    default_srt_func = None
    defualt_srt_freq = None
    default_srt_temp_width = 0.0
    default_srt_fwidth = 0.0
    default_width_option = None
    default_srt_custom_cfreq = None
    default_srt_custom_fwidth = None
    default_srt_start = 0.0
    default_srt_end = 1e20
    default_srt_cutoff = None
    default_srt_int = False
    default_srt_slowness = None
    # --- 3. Amplitude related ---
    default_amp = 1.0
    default_amp_adv = None
    default_amp_set = None
    default_amp_func = None
    default_amp_func_file = None
    # --- 4.1. Custom source
    default_src_custom_comp = None

    # --- 4.2. Eigenmode source
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
    # --- 4.3. Gaussian source
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
        default_amp_adv = hasattr(old_cfg, "amp_func") or hasattr(old_cfg, "amp_func_file")
        default_amp_set = "function" if hasattr(old_cfg, "amp_func") else ("file" if hasattr(old_cfg, "amp_func_file") else None)
        default_amp_func = getattr(old_cfg, "amp_func", None)
        default_amp_func_file = getattr(old_cfg, "amp_func_file", None)
        default_srt_func = getattr(old_cfg, "src_func", None)
        if old_cfg.center is not None: default_center = list(old_cfg.center)
        if old_cfg.size is not None: default_size = list(old_cfg.size)

        if cfg_type == 'EigenmodeSource': 
            default_src_type = 'Eigenmode'
            default_src_eig_comp = getattr(old_cfg, "component", 'All')
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
            default_src_gau_comp = getattr(old_cfg, "component", 'All')
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
                default_srt_cutoff = getattr(srct, 'cutoff')
                default_srt_slowness = getattr(srct, 'slowness', 3.0)
            elif srct_type == 'Custom_srct': 
                default_srt_type = 'Custom'
                default_srt_start = getattr(srct, 'start_time', -1e20)
                default_srt_end = getattr(srct, 'end_time', 1e20)
                default_srt_custom_cfreq = getattr(srct, 'center_frequency', 0.0)
                default_srt_custom_fwidth = getattr(srct, 'fwidth', 0.0)
            if hasattr(srct, 'wavelength'):
                defualt_srt_freq = getattr(srct, 'wavelength')
            elif hasattr(srct, 'frequency'):
                defualt_srt_freq = getattr(srct, 'frequency')
            if hasattr(srct, 'width'):
                default_srt_temp_width = getattr(srct, 'width')
                default_width_option = "Temporal"
            elif hasattr(srct, 'fwidth'):
                default_srt_fwidth = getattr(srct, 'fwidth')
                default_width_option = "Frequency"

            default_srt_int = getattr(srct, 'is_integrated', False)



    temp_src_type = st.session_state.get('t_src_type', default_src_type)
    temp_srt_type = st.session_state.get('t_srt_type', default_srt_type)
    temp_amp_adv = st.session_state.get('t_src_amp_adv', default_amp_adv)
    temp_amp_set = st.session_state.get('t_src_amp_set', default_amp_set)
    temp_amp_func = st.session_state.get('t_src_amp_func', default_amp_func)
    temp_amp_func_file = st.session_state.get('t_src_amp_func_file', default_amp_func_file)


    if st.button("Confirm", type='primary', use_container_width=True):
        if temp_src_type is None:
            st.toast("Please select source type!", icon="⚠️")
        elif temp_srt_type is None:
            st.toast("Please select time type!", icon="⚠️")
        else:
            if st.session_state.get('t_srt_wl_width_option') == "Temporal":
                wid = {
                        "width": st.session_state.get('t_srt_temp_width'),
                    }
            elif st.session_state.get('t_srt_wl_width_option') == "Frequency":
                wid = {
                    "fwidth": st.session_state.get('t_srt_fwidth'),
                }
            if temp_srt_type == "Custom":
                srct = Custom_srct(
                    src_func=st.session_state.get('t_src_time_func'),
                    start_time=st.session_state.get('t_srt_start', -1e20),
                    end_time=st.session_state.get('t_srt_end', 1e20),
                    is_integrated=st.session_state.get('t_srt_int', False),
                    center_frequency=st.session_state.get('t_srt_custom_cfreq', 0.0),
                    fwidth=st.session_state.get('t_srt_custom_fwidth', 0.0),
                )
            elif temp_srt_type == "Gaussian":

                srct = Gaussian_srct(
                    **wid,
                    start_time=st.session_state.get('t_srt_start', 0.0),
                    cutoff=st.session_state.get('t_srt_cutoff', 5.0),
                    is_integrated=st.session_state.get('t_srt_int', False),
                    frequency=st.session_state.get('t_srt_freq'),
                )
            elif temp_srt_type == "Continuous":
                srct = CW_srct(
                    **wid,
                    start_time=st.session_state.get('t_srt_start', 0.0),
                    end_time=st.session_state.get('t_srt_end', 1e20),
                    cutoff=st.session_state.get('t_srt_cutoff', None),
                    slowness=st.session_state.get('t_srt_slowness', 3.0),
                    frequency=st.session_state.get('t_srt_freq'),
                    is_integrated=st.session_state.get('t_srt_int', False),
                )

            # 根据类型创建具体对象
            upload_file = None
            if temp_amp_set == "file":
                if st.session_state.get('t_src_amp_func_file') is not None:
                    upload_file = st.session_state.get('t_src_amp_func_file')
                else:
                    upload_file = default_amp_func_file
            base_kwargs = {
                "name": st.session_state.get('t_src_name') if f" ({temp_src_type})" in st.session_state.get('t_src_name') else st.session_state.get('t_src_name') + f" ({temp_src_type})",
                "color": st.session_state.get('t_src_color') or default_color,
                "srct": srct,
                "opacity": OPACITY,
                "center": np.array([st.session_state.get('t_src_center_x'), st.session_state.get('t_src_center_y'), st.session_state.get('t_src_center_z')]),
                "size": np.array([st.session_state.get('t_src_size_x'), st.session_state.get('t_src_size_y'), st.session_state.get('t_src_size_z')]),
                "amplitude": st.session_state.get('t_src_amp') or 1.0,
            }

            if temp_src_type == "Eigenmode":
                new_source = EigenmodeSource(
                    **base_kwargs,
                    component=st.session_state.get('t_src_comp_eig'),
                    eig_lattice_size=np.array([st.session_state.get('t_src_eig_lat_sx'), st.session_state.get('t_src_eig_lat_sy'), st.session_state.get('t_src_eig_lat_sz')]),
                    eig_lattice_center=np.array([st.session_state.get('t_src_eig_lat_cx'), st.session_state.get('t_src_eig_lat_cy'), st.session_state.get('t_src_eig_lat_cz')]),
                    eig_parity=st.session_state.get('t_src_eig_parity'),
                    eig_match_freq=st.session_state.get('t_src_eig_match_freq'),
                    direction=st.session_state.get('t_src_eig_dir'),
                    eig_kpoint=np.array([st.session_state.get('t_src_eig_kptx'), st.session_state.get('t_src_eig_kpty'), st.session_state.get('t_src_eig_kptz')]),
                    eig_band=st.session_state.get('t_src_eig_band', 1),
                    eig_resolution=st.session_state.get('t_src_eig_res', 20),
                    eig_tolerance=st.session_state.get('t_src_eig_tol', '1e-12'),
                )
            elif temp_src_type == "Gaussian":
                new_source = GaussianSource(
                    **base_kwargs,
                    component=st.session_state.get('t_src_comp_gau'),
                    beam_x0=np.array([st.session_state.get('t_src_gau_x0x'), st.session_state.get('t_src_gau_x0y'), st.session_state.get('t_src_gau_x0z')]),
                    beam_kdir=np.array([st.session_state.get('t_src_gau_kdirx'), st.session_state.get('t_src_gau_kdiry'), st.session_state.get('t_src_gau_kdirz')]),
                    beam_E0=np.array([st.session_state.get('t_src_gau_E0x'), st.session_state.get('t_src_gau_E0y'), st.session_state.get('t_src_gau_E0z')]),
                    beam_2d=st.session_state.get('t_src_gau_2d', False),
                    beam_w0=st.session_state.get('t_src_gau_w0'),
                )
            elif temp_src_type == "Custom":
                new_source = Source(
                    **base_kwargs,
                    amp_func=st.session_state.get('t_src_amp_func') if temp_amp_set == "function" else None,
                    amp_func_file=upload_file,
                    component=st.session_state.get('t_src_comp_custom'),
                )

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
        st.text_input("Name", placeholder="Source name", key='t_src_name', value=default_name)
        src_type_options = ["Custom", "Eigenmode", "Gaussian"]
        temp_src_type_select = st.selectbox("Source type", src_type_options, 
                                     index=src_type_options.index(default_src_type) if default_src_type is not None else None, key='t_src_type')
        
        
        with st.expander("Source-time config"):

            srt_type_options = ["Gaussian", "Continuous", "Custom"]
            temp_srt_type_select = st.radio("Time type", srt_type_options, 
                                     index=srt_type_options.index(default_srt_type) if default_srt_type is not None else None,
                                     key='t_srt_type', horizontal=True)
            if temp_srt_type_select != "Custom":
                temp_srt_freq = st.number_input("Frequency", placeholder="Frequency of the source", key='t_srt_freq', value=defualt_srt_freq)
                width_list = ["Temporal", "Frequency"]
                width_option = st.radio("Frequency width defined by", width_list, key='t_srt_wl_width_option', horizontal=True,index=width_list.index(default_width_option) if default_width_option is not None else None)
                if width_option == "Temporal":
                    temp_srt_width = st.number_input("Temporal width", placeholder="Temporal width", key='t_srt_temp_width', value=default_srt_temp_width)
                elif width_option == "Frequency":
                    temp_srt_width = st.number_input("Frequency width", placeholder="Frequency width", key='t_srt_fwidth',value=default_srt_fwidth)
            elif temp_srt_type_select == "Custom":
                temp_srt_custom_cfreq = st.number_input("Center frequency", placeholder="Center frequency", key='t_srt_custom_cfreq', value=default_srt_custom_cfreq)
                temp_srt_custom_fwidth = st.number_input("Frequency width", placeholder="Frequency width", key='t_srt_custom_fwidth', value=default_srt_custom_fwidth)

            if temp_srt_type == "Custom":
                temp_srt_func = st.text_area("Time function", placeholder="A custom time function of the source, e.g. exp(-t**2)", key='t_srt_time_func', value=default_srt_func)
            if temp_srt_type:
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
            if st.session_state.get('t_src_type') == 'Custom':
                if st.checkbox("More advanced amplitude", key='t_src_amp_adv',value=default_amp_adv):
                    amp_type_list = ["function", "file"]
                    temp_src_amp_set = st.radio("Defined by", amp_type_list, horizontal=True, label_visibility='collapsed',key='t_src_amp_set', index=amp_type_list.index(default_amp_set) if default_amp_set is not None else None)
                    if temp_src_amp_set == "function":
                        st.text_area("Amplitude function", placeholder="e.g. exp(-t**2)", key='t_src_amp_func', value=default_amp_func)
                    if temp_src_amp_set == "file":
                        temp_src_amp_func_file = st.file_uploader("Upload file", type=['h5', 'hdf5','npy'], key='t_src_amp_func_file', accept_multiple_files=False)
                        if temp_src_amp_func_file is not None:
                            st.success(f"Uploaded file: {temp_src_amp_func_file.name}")
                        elif default_amp_func_file is not None:
                            st.success(f"Previously uploaded file: {default_amp_func_file.name}")
                        else:
                            st.info("No amplitude function file uploaded.")
            else:
                st.info('In-bulit amplitude function from source type.')
        
        temp_src_color = st.color_picker("Pick a color", value=default_color or "#000000", key="t_src_color")
                    


    with src_right:
        st.write("Source parameters")
        if st.session_state.get('t_src_type') == None:
            st.error("Please specify source type.")
        if st.session_state.get('t_src_type') == "Custom":
            custom_comp_options = ["Ex", "Ey", "Ez", "Hx", "Hy", "Hz"]
            temp_src_comp = st.selectbox("Component", custom_comp_options, key='t_src_comp_custom',index=custom_comp_options.index(default_src_custom_comp) if default_src_custom_comp is not None else None)
        if st.session_state.get('t_src_type') == "Eigenmode":
            eig_comp_options = ['All', "Ex", "Ey", "Ez", "Hx", "Hy", "Hz"]
            temp_src_comp = st.selectbox("Component", eig_comp_options, key='t_src_comp_eig',index=eig_comp_options.index(default_src_eig_comp) if default_src_eig_comp != None else 0,disabled=True)
            temp_eig_band = st.number_input('Eigenband index', min_value=1, step=1, placeholder='The index of n of the desided band.', key='t_src_eig_band',value=default_src_eig_band)
            temp_eig_res = st.number_input('Eigenmode solver resolution', placeholder='Resolution for the eigenmode solver', key='t_src_eig_res',value=default_src_eig_res)
            temp_eig_tol = st.number_input('Eigenmode solver tolerance', placeholder='Tolerance for the eigenmode solver.', key='t_src_eig_tol',value=default_src_eig_tol)
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
                temp_eig_par = st.multiselect("Parity", ["No parity", "Even Z", "Odd Z", "Even Y", "ODD Y"], key='t_src_eig_parity', default=default_src_eig_parity)
            with st.expander("Direction, frequency and reciprocal for eigenmode"):
                temp_eig_match_freq = st.checkbox("Match frequency", key='t_src_eig_match_freq', value=default_src_eig_match_freq if default_src_eig_match_freq is not None else True)
                eigen_dir_options = ["Auto", "X", "Y", "Z"]
                temp_eig_dir = st.selectbox("Direction", eigen_dir_options, key='t_src_eig_dir', index=eigen_dir_options.index(default_src_eig_dir) if default_src_eig_dir is not None else None)
                x, y, z = st.columns(3)
                temp_eig_kpt = [None] * 3
                temp_eig_kpt[0] = x.number_input("k-point", label_visibility='visible', placeholder="kx", key='t_src_eig_kptx', value=default_src_eig_kpt[0])
                temp_eig_kpt[1] = y.number_input("k-point", label_visibility='hidden', placeholder="ky", key='t_src_eig_kpty', value=default_src_eig_kpt[1])
                temp_eig_kpt[2] = z.number_input("k-point", label_visibility='hidden', placeholder="kz", key='t_src_eig_kptz', value=default_src_eig_kpt[2])
        if st.session_state.get('t_src_type') == "Gaussian":
            gau_comp_options = ['All', "Ex", "Ey", "Ez", "Hx", "Hy", "Hz"]
            temp_src_comp = st.selectbox("Component", gau_comp_options, index=gau_comp_options.index(default_src_gau_comp) if default_src_gau_comp != 'All' else 'All', key='t_src_comp_gau',disabled=True)
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
