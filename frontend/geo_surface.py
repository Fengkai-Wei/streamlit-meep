
import uuid
import numpy as np
import plotly.graph_objects as go

OPACITY = 1.0
class BasicGeometry:
    def __init__(self, color, name, material, center):
        self.uid = uuid.uuid4().hex
        self.color = color
        self.name = name
        self.material = material
        self.center = center

class Block(BasicGeometry):
    def __init__(self, color, name, material, center, size, e1, e2, e3):
        super().__init__(color, name, material, center)
        self.size = size
        self.e1 = e1
        self.e2 = e2
        self.e3 = e3

class Ellipsoid(Block):
    def __init__(self, color, name, material, center, size, e1, e2, e3):
        super().__init__(color, name, material, center, size, e1, e2, e3)

class Sphere(BasicGeometry):
    def __init__(self, color, name, material, center, radius):
        super().__init__(color, name, material, center)
        self.radius = radius

class Prism(BasicGeometry):
    def __init__(self, color, name, material, center, vertices_list, height, prism_axis, sidewall_angle,shift_center=None):
        super().__init__(color, name, material, center)
        self.vertices_list = vertices_list
        self.height = height
        self.prism_axis = prism_axis
        self.sidewall_angle = sidewall_angle
        self.shift_center = shift_center if shift_center is not None else None

class Cylinder(BasicGeometry):
    def __init__(self, color, name, material, center, radius, height, axis):
        super().__init__(color, name, material, center)
        self.radius = radius
        self.height = height
        self.axis = axis

class Cone(Cylinder):
    def __init__(self, color, name, material, center, radius, radius1, height, axis):
        super().__init__(color, name, material, center, radius, height, axis)
        self.radius1 = radius1


class Wedge(Cylinder):
    def __init__(self, color, name, material, center, radius, height, axis, wedge_angle, wedge_start):
        super().__init__(color, name, material, center,radius,height,axis)
        self.wedge_angle = wedge_angle
        self.wedge_start = wedge_start 




def get_meep_block_trace(center, size, e1, e2, e3, color="blue", name="Block"):
    c = np.array(center)
    s = np.array(size)
    
    # 1. 构建变换矩阵 (归一化基向量作为列)
    E = np.array([e1, e2, e3]).T
    E_norm = E / np.linalg.norm(E, axis=0)
    
    # 2. 定义标准 1x1x1 立方体的 6 个面 (2x2 网格)
    r = [-0.5, 0.5]
    # 每个面由 x, y, z 三个 2x2 矩阵组成
    face_templates = [
        # 底面 & 顶面 (z轴方向)
        {'x': [[r[0], r[1]], [r[0], r[1]]], 'y': [[r[0], r[0]], [r[1], r[1]]], 'z': [[-0.5, -0.5], [-0.5, -0.5]]},
        {'x': [[r[0], r[1]], [r[0], r[1]]], 'y': [[r[0], r[0]], [r[1], r[1]]], 'z': [[0.5, 0.5], [0.5, 0.5]]},
        # 前面 & 后面 (y轴方向)
        {'x': [[r[0], r[1]], [r[0], r[1]]], 'y': [[-0.5, -0.5], [-0.5, -0.5]], 'z': [[r[0], r[0]], [r[1], r[1]]]},
        {'x': [[r[0], r[1]], [r[0], r[1]]], 'y': [[0.5, 0.5], [0.5, 0.5]], 'z': [[r[0], r[0]], [r[1], r[1]]]},
        # 左面 & 右面 (x轴方向)
        {'x': [[-0.5, -0.5], [-0.5, -0.5]], 'y': [[r[0], r[1]], [r[0], r[1]]], 'z': [[r[0], r[0]], [r[1], r[1]]]},
        {'x': [[0.5, 0.5], [0.5, 0.5]], 'y': [[r[0], r[1]], [r[0], r[1]]], 'z': [[r[0], r[0]], [r[1], r[1]]]}
    ]

    traces = []
    for i, template in enumerate(face_templates):
        # 3. 缩放并应用矩阵变换
        # 将 2x2 展开为 1x4 进行矩阵运算，然后再还原回 2x2
        local_pts = np.stack([
            np.array(template['x']).flatten() * s[0],
            np.array(template['y']).flatten() * s[1],
            np.array(template['z']).flatten() * s[2]
        ])
        
        # Global = M * Local + Center
        global_pts = (E_norm @ local_pts).T + c
        
        gx = global_pts[:, 0].reshape((2, 2))
        gy = global_pts[:, 1].reshape((2, 2))
        gz = global_pts[:, 2].reshape((2, 2))
        
        # 4. 创建 Surface Trace
        traces.append(go.Surface(
            x=gx, y=gy, z=gz,
            colorscale=[[0, color], [1, color]],
            showscale=False,
            opacity=OPACITY,
            name=name,
            # 优化图例：只显示第一个面的图例，并将所有面关联在一起
            showlegend=True if i == 0 else False,
            legendgroup=name
        ))
    
    return traces

def get_meep_ellipsoid_trace(center, size, e1, e2, e3, color="red", name="Ellipsoid"):
    # 1. 基础参数
    c = np.array(center)
    radii = np.array(size) / 2.0  # Meep的size是直径
    
    # 2. 生成球面参数网格 (经纬度)
    theta = np.linspace(0, 2*np.pi, 30) # 经度
    phi = np.linspace(0, np.pi, 20)    # 纬度
    theta, phi = np.meshgrid(theta, phi)
    
    # 3. 计算局部坐标 (标准椭球)
    x_loc = radii[0] * np.cos(theta) * np.sin(phi)
    y_loc = radii[1] * np.sin(theta) * np.sin(phi)
    z_loc = radii[2] * np.cos(phi)
    
    # 将坐标展平以便进行矩阵运算 (3, N)
    local_coords = np.stack([x_loc.flatten(), y_loc.flatten(), z_loc.flatten()])
    
    # 4. 应用基底变换 (e1, e2, e3)
    E = np.array([e1, e2, e3]).T
    E_norm = E / np.linalg.norm(E, axis=0) # 归一化轴向
    
    # 变换到全局坐标: Global = E_norm * Local + Center
    global_coords = (E_norm @ local_coords).T + c
    
    # 5. 重新整理回网格形状供 Plotly Surface 使用
    x = global_coords[:, 0].reshape(theta.shape)
    y = global_coords[:, 1].reshape(theta.shape)
    z = global_coords[:, 2].reshape(theta.shape)
    
    # 使用 go.Surface 绘制，设置单一颜色
    return go.Surface(
        x=x, y=y, z=z,
        colorscale=[[0, color], [1, color]],
        showscale=False,
        opacity=OPACITY,
        name=name,
        showlegend=True
    )

def get_meep_sphere(center, radius, color="green", name="Sphere",resolution=30):
    """
    专门用于生成 Meep 球体的 Plotly Trace
    :param center: (x, y, z) 元组或列表
    :param radius: 球体半径
    :param color: 颜色字符串 (如 "red", "#FFA500")
    :param name: 图例显示的名称
    :param resolution: 经纬度采样点数，数值越高球体越圆滑
    """
    c = np.array(center)
    
    # 1. 生成球面参数网格 (使用标准球面坐标系)
    # theta 是经度 (0 到 2pi)，phi 是纬度 (0 到 pi)
    theta = np.linspace(0, 2*np.pi, resolution)
    phi = np.linspace(0, np.pi, resolution)
    theta, phi = np.meshgrid(theta, phi)
    
    # 2. 计算标准球面坐标
    x = c[0] + radius * np.cos(theta) * np.sin(phi)
    y = c[1] + radius * np.sin(theta) * np.sin(phi)
    z = c[2] + radius * np.cos(phi)
    
    # 3. 使用 go.Surface 绘制
    return go.Surface(
        x=x, y=y, z=z,
        # 设置单一颜色：Plotly Surface 默认根据 Z 值着色，
        # 我们通过设置 colorscale 为固定颜色来覆盖它
        colorscale=[[0, color], [1, color]],
        showscale=False,  # 隐藏颜色条
        opacity=OPACITY,      # 半透明方便观察内部
        name=name,
        showlegend=True   # 在图例中显示
    )


from scipy.spatial import distance

def get_meep_prism_mesh(vertices_list, height, prism_axis, sidewall_angle, 
                        bottom_center=None, color="purple", name="Prism"):
    """
    专门用于生成 Meep Prism 的 Plotly Trace (go.Surface)
    """
    pts = np.array(vertices_list)  # (N, 2)
    N = len(pts)
    if N < 3:
        raise ValueError("Prism base must have at least 3 vertices.")

    # 1. 计算底面几何中心并对齐到 bottom_center
    geom_center_2d = np.mean(pts, axis=0)
    if bottom_center is not None:
        bc_3d = np.array(bottom_center)
        pts_centered = pts - geom_center_2d
    else:
        pts_centered = pts - geom_center_2d
        bc_3d = np.array([0, 0, 0])

    # 2. 生成 3D 局部顶点 (Bottom z=0, Top z=height)
    delta_r = height * np.tan(sidewall_angle)
    bottom_vertices = []
    top_vertices = []
    for p in pts_centered:
        bottom_vertices.append([p[0], p[1], 0])
        r_norm = np.linalg.norm(p)
        if r_norm == 0:
            top_vertices.append([0, 0, height])
        else:
            r_unit = p / r_norm
            scaled_p = p - delta_r * r_unit
            top_vertices.append([scaled_p[0], scaled_p[1], height])
    bottom_vertices = np.array(bottom_vertices)
    top_vertices = np.array(top_vertices)

    # 3. 应用 Meep Axis 旋转和 Bottom Center 平移
    z_axis = np.array([0, 0, 1])
    target_axis = np.array(prism_axis)
    target_axis = target_axis / np.linalg.norm(target_axis)
    if np.allclose(z_axis, target_axis):
        R = np.eye(3)
    elif np.allclose(z_axis, -target_axis):
        R = np.diag([1, -1, -1])
    else:
        v = np.cross(z_axis, target_axis)
        s = np.linalg.norm(v)
        c = np.dot(z_axis, target_axis)
        I = np.eye(3)
        v_x = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        R = I + v_x + np.dot(v_x, v_x) * ((1 - c) / (s**2))

    global_bottom = (R @ bottom_vertices.T).T + bc_3d
    global_top = (R @ top_vertices.T).T + bc_3d

    bottom_center_point = np.mean(global_bottom, axis=0)
    top_center_point = np.mean(global_top, axis=0)

    traces = []

    # 底面 Surface
    bottom_ring_x = np.append(global_bottom[:, 0], global_bottom[0, 0])
    bottom_ring_y = np.append(global_bottom[:, 1], global_bottom[0, 1])
    bottom_ring_z = np.full(N + 1, global_bottom[0, 2])
    x_bottom = np.vstack([np.full(N + 1, bottom_center_point[0]), bottom_ring_x])
    y_bottom = np.vstack([np.full(N + 1, bottom_center_point[1]), bottom_ring_y])
    z_bottom = np.vstack([np.full(N + 1, bottom_center_point[2]), bottom_ring_z])
    traces.append(go.Surface(
        x=x_bottom, y=y_bottom, z=z_bottom,
        colorscale=[[0, color], [1, color]],
        showscale=False,
        opacity=OPACITY,
        name=f"{name} bottom",
        showlegend=False
    ))

    # 顶面 Surface
    top_ring_x = np.append(global_top[:, 0], global_top[0, 0])
    top_ring_y = np.append(global_top[:, 1], global_top[0, 1])
    top_ring_z = np.full(N + 1, global_top[0, 2])
    x_top = np.vstack([np.full(N + 1, top_center_point[0]), top_ring_x])
    y_top = np.vstack([np.full(N + 1, top_center_point[1]), top_ring_y])
    z_top = np.vstack([np.full(N + 1, top_center_point[2]), top_ring_z])
    traces.append(go.Surface(
        x=x_top, y=y_top, z=z_top,
        colorscale=[[0, color], [1, color]],
        showscale=False,
        opacity=OPACITY,
        name=f"{name} top",
        showlegend=False
    ))

    # 侧面 Surface
    for i in range(N):
        j = (i + 1) % N
        x_side = np.array([
            [global_bottom[i, 0], global_bottom[j, 0]],
            [global_top[i, 0], global_top[j, 0]]
        ])
        y_side = np.array([
            [global_bottom[i, 1], global_bottom[j, 1]],
            [global_top[i, 1], global_top[j, 1]]
        ])
        z_side = np.array([
            [global_bottom[i, 2], global_bottom[j, 2]],
            [global_top[i, 2], global_top[j, 2]]
        ])
        traces.append(go.Surface(
            x=x_side, y=y_side, z=z_side,
            colorscale=[[0, color], [1, color]],
            showscale=False,
            opacity=OPACITY,
            name=f"{name} side {i}",
            showlegend=False
        ))

    return traces

def get_meep_cylindrical_shape(center, radius, height, axis, 
                               radius1=None, wedge_angle=2*np.pi, 
                               wedge_start=(1,0,0), color="cyan", name="Cylindrial shape"):
    """
    通用函数处理 Cylinder, Cone 和 Wedge
    """
    c = np.array(center)
    h = height
    r0 = radius
    r1 = radius1 if radius1 is not None else radius # 如果是圆柱，r1=r0
    
    # 1. 生成参数网格
    # 如果是圆柱/圆锥，u 从 start_angle 到 start_angle + wedge_angle
    res_u = 40
    res_v = 2
    res_r = 12
    
    # 计算起始角度 (从 wedge_start 向量计算)
    w_start = np.array(wedge_start)
    start_angle = np.arctan2(w_start[1], w_start[0])
    
    u = np.linspace(start_angle, start_angle + wedge_angle, res_u)
    v = np.linspace(0, h, res_v)
    U, V = np.meshgrid(u, v)

    # 2. 计算局部坐标 (轴向为 Z)
    # R(v) 随高度线性变化 (处理圆锥)
    R_v = r0 + (V / h) * (r1 - r0)
    
    x_loc = R_v * np.cos(U)
    y_loc = R_v * np.sin(U)
    z_loc = V - h/2 # Meep 的 center 通常在几何中心，所以 z 从 -h/2 到 h/2

    # 3. 坐标变换 (旋转到 axis)
    z_axis = np.array([0, 0, 1])
    target_axis = np.array(axis) / np.linalg.norm(axis)
    
    # 构建旋转矩阵 (罗德里格公式)
    if np.allclose(z_axis, target_axis):
        R = np.eye(3)
    elif np.allclose(z_axis, -target_axis):
        R = np.diag([1, -1, -1])
    else:
        vec = np.cross(z_axis, target_axis)
        s = np.linalg.norm(vec)
        cos_t = np.dot(z_axis, target_axis)
        v_x = np.array([[0, -vec[2], vec[1]], [vec[2], 0, -vec[0]], [-vec[1], vec[0], 0]])
        R = np.eye(3) + v_x + np.dot(v_x, v_x) * ((1 - cos_t) / (s**2))

    def transform_surface(x_s, y_s, z_s):
        flat_coords = np.stack([x_s.flatten(), y_s.flatten(), z_s.flatten()])
        global_coords = (R @ flat_coords).T + c
        x_g = global_coords[:, 0].reshape(x_s.shape)
        y_g = global_coords[:, 1].reshape(x_s.shape)
        z_g = global_coords[:, 2].reshape(x_s.shape)
        return x_g, y_g, z_g

    def build_surface(x_s, y_s, z_s, trace_name=None, showlegend=False):
        x_g, y_g, z_g = transform_surface(x_s, y_s, z_s)
        return go.Surface(
            x=x_g, y=y_g, z=z_g,
            colorscale=[[0, color], [1, color]],
            showscale=False,
            opacity=OPACITY,
            name=trace_name if trace_name is not None else name,
            showlegend=showlegend
        )

    side_trace = build_surface(x_loc, y_loc, z_loc, trace_name=name, showlegend=True)
    traces = [side_trace]

    r_grid_bottom = np.linspace(0, r0, res_r)
    U_grid_bottom, R_grid_bottom = np.meshgrid(u, r_grid_bottom)
    x_bottom = R_grid_bottom * np.cos(U_grid_bottom)
    y_bottom = R_grid_bottom * np.sin(U_grid_bottom)
    z_bottom = np.full_like(x_bottom, -h/2)
    traces.append(build_surface(x_bottom, y_bottom, z_bottom, trace_name=f"{name} bottom"))

    r_grid_top = np.linspace(0, r1, res_r)
    U_grid_top, R_grid_top = np.meshgrid(u, r_grid_top)
    x_top = R_grid_top * np.cos(U_grid_top)
    y_top = R_grid_top * np.sin(U_grid_top)
    z_top = np.full_like(x_top, h/2)
    traces.append(build_surface(x_top, y_top, z_top, trace_name=f"{name} top"))

    if wedge_angle < 2 * np.pi - 1e-6:
        r_edge = np.linspace(0, 1, res_r)
        for edge_angle, edge_label in [(start_angle, "start"), (start_angle + wedge_angle, "end")]:
            x_edge = np.stack([
                (r_edge * r0) * np.cos(edge_angle),
                (r_edge * r1) * np.cos(edge_angle)
            ])
            y_edge = np.stack([
                (r_edge * r0) * np.sin(edge_angle),
                (r_edge * r1) * np.sin(edge_angle)
            ])
            z_edge = np.stack([
                np.full_like(r_edge, -h/2),
                np.full_like(r_edge, h/2)
            ])
            traces.append(build_surface(x_edge, y_edge, z_edge, trace_name=f"{name} {edge_label}"))

    return traces

def get_meep_cylinder(center, radius, height, axis, color="blue", name="Cylinder"):
    return get_meep_cylindrical_shape(center, radius, height, axis, color=color, name=name)

def get_meep_cone(center, radius, radius1, height, axis, color="orange", name="Cone"):
    return get_meep_cylindrical_shape(center, radius, height, axis, radius1=radius1, color=color, name=name)

def get_meep_wedge(center, radius, height, axis, wedge_angle, wedge_start, color="yellow", name="Wedge"):
    # 注意：Wedge 在 Meep 中通常也是一个圆柱体的一部分
    return get_meep_cylindrical_shape(
        center, radius, height, axis, 
        wedge_angle=wedge_angle, 
        wedge_start=wedge_start, 
        color=color, name=name
    )

def geo_trace_checker(obj: BasicGeometry):
    if isinstance(obj, Ellipsoid):
        return get_meep_ellipsoid_trace(obj.center, obj.size, obj.e1, obj.e2, obj.e3, color=obj.color, name=obj.name)
    elif isinstance(obj, Block):
        return get_meep_block_trace(obj.center, obj.size, obj.e1, obj.e2, obj.e3, color=obj.color, name=obj.name)
    elif isinstance(obj, Sphere):
        return get_meep_sphere(obj.center, obj.radius, color=obj.color, name=obj.name)
    elif isinstance(obj, Prism):
        return get_meep_prism_mesh(obj.vertices_list, obj.height, obj.prism_axis, obj.sidewall_angle, 
                                   bottom_center=obj.center, color=obj.color, name=obj.name)
    elif isinstance(obj, Wedge):
        return get_meep_wedge(obj.center, obj.radius, obj.height, obj.axis, wedge_angle=obj.wedge_angle, wedge_start=obj.wedge_start, color=obj.color, name=obj.name)
    elif isinstance(obj, Cone):
        return get_meep_cone(obj.center, obj.radius, obj.radius1, obj.height, obj.axis, color=obj.color, name=obj.name)
    elif isinstance(obj, Cylinder):
        return get_meep_cylinder(obj.center, obj.radius, obj.height, obj.axis, color=obj.color, name=obj.name)
    else:
        raise ValueError(f"Unsupported geometry type: {type(obj)}")