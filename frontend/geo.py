
import uuid
import numpy as np
import plotly.graph_objects as go


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
            opacity=0.7,
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
        opacity=0.6,
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
        opacity=0.6,      # 半透明方便观察内部
        name=name,
        showlegend=True   # 在图例中显示
    )


from scipy.spatial import distance

def get_meep_prism_mesh(vertices_list, height, prism_axis, sidewall_angle, 
                        bottom_center=None, color="purple", name="Prism"):
    """
    专门用于生成 Meep Prism 的 Plotly Trace (go.Mesh3d)
    """
    pts = np.array(vertices_list) # (N, 2)
    N = len(pts)
    if N < 3:
        raise ValueError("Prism base must have at least 3 vertices.")
    
    # 1. 计算底面几何中心并对齐到 bottom_center
    geom_center_2d = np.mean(pts, axis=0)
    if bottom_center is not None:
        bc_3d = np.array(bottom_center)
        # 局部底面顶点平移，使几何中心在 (0,0,0)
        pts_centered = pts - geom_center_2d
    else:
        # 如果未提供 bottom_center，默认其几何中心在局部原点
        pts_centered = pts - geom_center_2d
        bc_3d = np.array([0, 0, 0])

    # 2. 生成 3D 局部顶点 (Bottom z=0, Top z=height)
    # 计算侧壁倾斜导致的缩放偏移量
    delta_r = height * np.tan(sidewall_angle)
    
    local_vertices = []
    
    # 底面顶点 (z=0)
    for p in pts_centered:
        local_vertices.append([p[0], p[1], 0])
        
    # 顶面顶点 (z=height)
    for p in pts_centered:
        # 径向单位向量
        r_norm = np.linalg.norm(p)
        if r_norm == 0: # 处理顶点就在中心的情况
            local_vertices.append([0, 0, height])
        else:
            r_unit = p / r_norm
            # 根据倾斜角缩放：顶面半径 = 底面半径 - delta_r
            # Meep定义：正角度表示向内收缩 (tapering input)
            scaled_p = p - delta_r * r_unit
            local_vertices.append([scaled_p[0], scaled_p[1], height])
            
    local_vertices = np.array(local_vertices) # (2N, 3)

    # 3. 应用 Meep Axis 旋转和 Bottom Center 平移
    # 构建旋转矩阵：将局部 z 轴转到 prism_axis
    z_axis = np.array([0, 0, 1])
    target_axis = np.array(prism_axis)
    target_axis = target_axis / np.linalg.norm(target_axis) # 归一化
    
    if np.allclose(z_axis, target_axis):
        R = np.eye(3) # 无旋转
    elif np.allclose(z_axis, -target_axis):
        # 旋转 180 度
        R = np.diag([1, -1, -1])
    else:
        # 使用罗德里格旋转公式计算
        v = np.cross(z_axis, target_axis)
        s = np.linalg.norm(v)
        c = np.dot(z_axis, target_axis)
        I = np.eye(3)
        v_x = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        R = I + v_x + np.dot(v_x, v_x) * ((1 - c) / (s**2))
        
    # 变换到全局坐标：Global = R * Local + Bottom_Center
    # 注意：这里假设 vertices_list 定义在与 axis 垂直的平面上，
    # 且 bottom_center 指向底面的几何中心。
    global_vertices = (R @ local_vertices.T).T + bc_3d
    
    # 拆分坐标
    x, y, z = global_vertices[:, 0], global_vertices[:, 1], global_vertices[:, 2]

    # 4. 构建三角面片索引 (i, j, k)
    idx_i, idx_j, idx_k = [], [], []
    
    # 索引规则：前 N 个是底面，后 N 个是顶面 (即 N 到 2N-1)
    
    # A. 侧面三角形 (每个侧面 2 个)
    for i in range(N):
        next_i = (i + 1) % N
        # 侧面 1 (底i, 底next, 顶i)
        idx_i.append(i)
        idx_j.append(next_i)
        idx_k.append(i + N)
        # 侧面 2 (底next, 顶next, 顶i)
        idx_i.append(next_i)
        idx_j.append(next_i + N)
        idx_k.append(i + N)

    # B. 底面和顶面三角形 (使用“风扇法”简化三角剖分，仅适用于凸多边形)
    # Meep 的 Prism 通常处理凸多边形，如果需要支持凹多边形，需要用复杂算法
    for i in range(1, N - 1):
        # 底面 (0 是中心点，连接 0, i, i+1)
        idx_i.append(0)
        idx_j.append(i)
        idx_k.append(i + 1)
        # 顶面 (N 是顶面中心点，连接 N, i+N, i+1+N)
        idx_i.append(N)
        idx_j.append(i + N)
        idx_k.append(i + 1 + N)

    return go.Mesh3d(
        x=x, y=y, z=z, i=idx_i, j=idx_j, k=idx_k,
        color=color, opacity=0.7, name=name,
        showlegend=True,
        # 确保面片的法线朝外，这对于 Mesh3d 渲染很重要
        flatshading=True 
    )

import numpy as np
import plotly.graph_objects as go

def get_meep_cylindrical_shape(center, radius, height, axis, 
                               radius1=None, wedge_angle=2*np.pi, 
                               wedge_start=(1,0,0), color="cyan", name="Shape"):
    """
    通用函数处理 Cylinder, Cone 和 Wedge
    """
    c = np.array(center)
    h = height
    r0 = radius
    r1 = radius1 if radius1 is not None else radius # 如果是圆柱，r1=r0
    
    # 1. 生成参数网格
    # 如果是圆柱/圆锥，u 从 0 到 2pi；如果是 Wedge，根据角度范围
    res_u = 40
    res_v = 2
    
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

    # 变换所有点
    flat_coords = np.stack([x_loc.flatten(), y_loc.flatten(), z_loc.flatten()])
    global_coords = (R @ flat_coords).T + c
    
    x = global_coords[:, 0].reshape(U.shape)
    y = global_coords[:, 1].reshape(U.shape)
    z = global_coords[:, 2].reshape(U.shape)

    # 4. 返回 Surface Trace
    return go.Surface(
        x=x, y=y, z=z,
        colorscale=[[0, color], [1, color]],
        showscale=False,
        opacity=0.7,
        name=name
    )

def get_meep_cylinder(center, radius, height, axis, color="blue"):
    return get_meep_cylindrical_shape(center, radius, height, axis, color=color, name="Cylinder")

def get_meep_cone(center, radius, radius1, height, axis, color="orange"):
    return get_meep_cylindrical_shape(center, radius, height, axis, radius1=radius1, color=color, name="Cone")

def get_meep_wedge(center, radius, height, axis, wedge_angle, wedge_start, color="yellow"):
    # 注意：Wedge 在 Meep 中通常也是一个圆柱体的一部分
    return get_meep_cylindrical_shape(
        center, radius, height, axis, 
        wedge_angle=wedge_angle, 
        wedge_start=wedge_start, 
        color=color, name="Wedge"
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
        return get_meep_wedge(obj.center, obj.radius, obj.height, obj.axis, color=obj.color)
    elif isinstance(obj, Cone):
        return get_meep_cone(obj.center, obj.radius, obj.radius1, obj.height, obj.axis, color=obj.color)
    elif isinstance(obj, Cylinder):
        return get_meep_cylinder(obj.center, obj.radius, obj.height, obj.axis, obj.wedge_angle, obj.wedge_start, color=obj.color)
    else:
        raise ValueError(f"Unsupported geometry type: {type(obj)}")