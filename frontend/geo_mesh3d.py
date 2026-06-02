
import uuid
import numpy as np
import plotly.graph_objects as go

OPACITY = 1.0

def grid_to_mesh3d(x, y, z, color, name, opacity=OPACITY, showlegend=False, legendgroup=None):
    """Convert a rectangular grid of points into a Plotly Mesh3d trace."""
    x_flat = x.flatten()
    y_flat = y.flatten()
    z_flat = z.flatten()
    m, n = x.shape

    i = []
    j = []
    k = []
    for ui in range(m - 1):
        for vi in range(n - 1):
            idx = ui * n + vi
            a = idx
            b = idx + 1
            c = idx + n
            d = idx + n + 1
            i.extend([a, b])
            j.extend([c, c])
            k.extend([b, d])

    return go.Mesh3d(
        x=x_flat, y=y_flat, z=z_flat,
        i=i, j=j, k=k,
        color=color, opacity=opacity, name=name,
        showlegend=showlegend,
        legendgroup=legendgroup,
        flatshading=True
    )

class BasicGeometry:
    def __init__(self, color, name, material, center, opacity=1.0):
        self.uid = uuid.uuid4().hex
        self.color = color
        self.name = name
        self.material = material
        self.center = center
        self.opacity = opacity

class Block(BasicGeometry):
    def __init__(self, color, name, material, center, size, e1, e2, e3, opacity=1.0):
        super().__init__(color, name, material, center, opacity=opacity)
        self.size = size
        self.e1 = e1
        self.e2 = e2
        self.e3 = e3

class Ellipsoid(Block):
    def __init__(self, color, name, material, center, size, e1, e2, e3, opacity=1.0):
        super().__init__(color, name, material, center, size, e1, e2, e3, opacity=opacity)

class Sphere(BasicGeometry):
    def __init__(self, color, name, material, center, radius, opacity=1.0):
        super().__init__(color, name, material, center, opacity=opacity)
        self.radius = radius

class Prism(BasicGeometry):
    def __init__(self, color, name, material, center, vertices_list, height, prism_axis, sidewall_angle, shift_center=None, opacity=1.0):
        super().__init__(color, name, material, center, opacity=opacity)
        self.vertices_list = vertices_list
        self.height = height
        self.prism_axis = prism_axis
        self.sidewall_angle = sidewall_angle
        self.shift_center = shift_center if shift_center is not None else None

class Cylinder(BasicGeometry):
    def __init__(self, color, name, material, center, radius, height, axis, opacity=1.0):
        super().__init__(color, name, material, center, opacity=opacity)
        self.radius = radius
        self.height = height
        self.axis = axis

class Cone(Cylinder):
    def __init__(self, color, name, material, center, radius, radius1, height, axis, opacity=1.0):
        super().__init__(color, name, material, center, radius, height, axis, opacity=opacity)
        self.radius1 = radius1


class Wedge(Cylinder):
    def __init__(self, color, name, material, center, radius, height, axis, wedge_angle, wedge_start, opacity=1.0):
        super().__init__(color, name, material, center, radius, height, axis, opacity=opacity)
        self.wedge_angle = wedge_angle
        self.wedge_start = wedge_start 




def get_meep_block_trace(center, size, e1, e2, e3, color="blue", name="Block", opacity=OPACITY):
    """Generate a Mesh3d trace for a block with given orientation vectors."""
    c = np.array(center)
    s = np.array(size)

    E = np.array([e1, e2, e3]).T
    E_norm = E / np.linalg.norm(E, axis=0)

    local_vertices = np.array([
        [-0.5, -0.5, -0.5],
        [ 0.5, -0.5, -0.5],
        [ 0.5,  0.5, -0.5],
        [-0.5,  0.5, -0.5],
        [-0.5, -0.5,  0.5],
        [ 0.5, -0.5,  0.5],
        [ 0.5,  0.5,  0.5],
        [-0.5,  0.5,  0.5]
    ]) * s

    global_vertices = (E_norm @ local_vertices.T).T + c
    x = global_vertices[:, 0]
    y = global_vertices[:, 1]
    z = global_vertices[:, 2]

    faces = [
        (0, 1, 2), (0, 2, 3),
        (4, 6, 5), (4, 7, 6),
        (0, 4, 5), (0, 5, 1),
        (1, 5, 6), (1, 6, 2),
        (2, 6, 7), (2, 7, 3),
        (3, 7, 4), (3, 4, 0)
    ]
    i, j, k = zip(*faces)

    return go.Mesh3d(
        x=x, y=y, z=z,
        i=list(i), j=list(j), k=list(k),
        color=color, opacity=opacity, name=name,
        showlegend=True, legendgroup=name,
        flatshading=True
    )
def get_meep_ellipsoid_trace(center, size, e1, e2, e3, color="red", name="Ellipsoid", opacity=OPACITY):
    """Generate a Mesh3d trace for an oriented ellipsoid using basis vectors."""
    c = np.array(center)
    radii = np.array(size) / 2.0

    theta = np.linspace(0, 2 * np.pi, 40)
    phi = np.linspace(0, np.pi, 20)
    theta, phi = np.meshgrid(theta, phi)

    x_loc = radii[0] * np.cos(theta) * np.sin(phi)
    y_loc = radii[1] * np.sin(theta) * np.sin(phi)
    z_loc = radii[2] * np.cos(phi)

    local_coords = np.stack([x_loc.flatten(), y_loc.flatten(), z_loc.flatten()])
    E = np.array([e1, e2, e3]).T
    E_norm = E / np.linalg.norm(E, axis=0)
    global_coords = (E_norm @ local_coords).T + c

    x = global_coords[:, 0].reshape(theta.shape)
    y = global_coords[:, 1].reshape(theta.shape)
    z = global_coords[:, 2].reshape(theta.shape)

    return grid_to_mesh3d(x, y, z, color=color, name=name, opacity=opacity, showlegend=True, legendgroup=name)

def get_meep_sphere(center, radius, color="green", name="Sphere", resolution=30, opacity=OPACITY):
    """Generate a Mesh3d trace for a sphere by delegating to the ellipsoid generator."""
    return get_meep_ellipsoid_trace(
        center, [2 * radius, 2 * radius, 2 * radius],
        [1, 0, 0], [0, 1, 0], [0, 0, 1],
        color=color, name=name, opacity=opacity
    )


from scipy.spatial import distance

def get_meep_prism_mesh(vertices_list, height, prism_axis, sidewall_angle, 
                        bottom_center=None, color="purple", name="Prism", opacity=OPACITY):
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
        color=color, opacity=opacity, name=name,
        showlegend=True,
        # 确保面片的法线朝外，这对于 Mesh3d 渲染很重要
        flatshading=True 
    )

import numpy as np
import plotly.graph_objects as go

def get_meep_cylindrical_shape(center, radius, height, axis, 
                               radius1=None, wedge_angle=2*np.pi, 
                               wedge_start=(1,0,0), color="cyan", name="Cylindrial shape", opacity=OPACITY):
    """Generate Mesh3d traces for a cylinder, cone, or wedge-shaped body."""
    c = np.array(center)
    h = height
    r0 = radius
    r1 = radius1 if radius1 is not None else radius

    res_u = 40
    res_r = 20

    w_start = np.array(wedge_start)
    start_angle = np.arctan2(w_start[1], w_start[0])
    u = np.linspace(start_angle, start_angle + wedge_angle, res_u)
    v = np.linspace(0, h, 2)
    U, V = np.meshgrid(u, v)

    R_v = r0 + (V / h) * (r1 - r0)
    x_loc = R_v * np.cos(U)
    y_loc = R_v * np.sin(U)
    z_loc = V - h / 2

    z_axis = np.array([0, 0, 1])
    target_axis = np.array(axis) / np.linalg.norm(axis)
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

    def transform_table(x_s, y_s, z_s):
        flat_coords = np.stack([x_s.flatten(), y_s.flatten(), z_s.flatten()])
        global_coords = (R @ flat_coords).T + c
        return [arr.reshape(x_s.shape) for arr in global_coords.T]

    traces = []
    x_g, y_g, z_g = transform_table(x_loc, y_loc, z_loc)
    traces.append(grid_to_mesh3d(x_g, y_g, z_g, color=color, name=name, opacity=opacity, showlegend=True, legendgroup=name))

    r_grid_bottom = np.linspace(0, r0, res_r)
    U_grid_bottom, R_grid_bottom = np.meshgrid(u, r_grid_bottom)
    x_bottom = R_grid_bottom * np.cos(U_grid_bottom)
    y_bottom = R_grid_bottom * np.sin(U_grid_bottom)
    z_bottom = np.full_like(x_bottom, -h / 2)
    x_g, y_g, z_g = transform_table(x_bottom, y_bottom, z_bottom)
    traces.append(grid_to_mesh3d(x_g, y_g, z_g, color=color, name=f"{name} bottom", opacity=opacity, showlegend=False, legendgroup=name))

    r_grid_top = np.linspace(0, r1, res_r)
    U_grid_top, R_grid_top = np.meshgrid(u, r_grid_top)
    x_top = R_grid_top * np.cos(U_grid_top)
    y_top = R_grid_top * np.sin(U_grid_top)
    z_top = np.full_like(x_top, h / 2)
    x_g, y_g, z_g = transform_table(x_top, y_top, z_top)
    traces.append(grid_to_mesh3d(x_g, y_g, z_g, color=color, name=f"{name} top", opacity=opacity, showlegend=False, legendgroup=name))

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
                np.full_like(r_edge, -h / 2),
                np.full_like(r_edge, h / 2)
            ])
            x_g, y_g, z_g = transform_table(x_edge, y_edge, z_edge)
            traces.append(grid_to_mesh3d(x_g, y_g, z_g, color=color, name=f"{name} {edge_label}", opacity=opacity, showlegend=False, legendgroup=name))

    return traces

def get_meep_cylinder(center, radius, height, axis, color="blue", name="Cylinder", opacity=OPACITY):
    return get_meep_cylindrical_shape(center, radius, height, axis, color=color, name=name, opacity=opacity)

def get_meep_cone(center, radius, radius1, height, axis, color="orange", name="Cone", opacity=OPACITY):
    return get_meep_cylindrical_shape(center, radius, height, axis, radius1=radius1, color=color, name=name, opacity=opacity)

def get_meep_wedge(center, radius, height, axis, wedge_angle, wedge_start, color="yellow", name="Wedge", opacity=OPACITY):
    # 注意：Wedge 在 Meep 中通常也是一个圆柱体的一部分
    return get_meep_cylindrical_shape(
        center, radius, height, axis, 
        wedge_angle=wedge_angle, 
        wedge_start=wedge_start, 
        color=color, name=name, opacity=opacity
    )

def geo_trace_checker(obj: BasicGeometry):
    if isinstance(obj, Ellipsoid):
        return get_meep_ellipsoid_trace(obj.center, obj.size, obj.e1, obj.e2, obj.e3, color=obj.color, name=obj.name, opacity=obj.opacity)
    elif isinstance(obj, Block):
        return get_meep_block_trace(obj.center, obj.size, obj.e1, obj.e2, obj.e3, color=obj.color, name=obj.name, opacity=obj.opacity)
    elif isinstance(obj, Sphere):
        return get_meep_sphere(obj.center, obj.radius, color=obj.color, name=obj.name, opacity=obj.opacity)
    elif isinstance(obj, Prism):
        return get_meep_prism_mesh(obj.vertices_list, obj.height, obj.prism_axis, obj.sidewall_angle, 
                                   bottom_center=obj.center, color=obj.color, name=obj.name, opacity=obj.opacity)
    elif isinstance(obj, Wedge):
        return get_meep_wedge(obj.center, obj.radius, obj.height, obj.axis, wedge_angle=obj.wedge_angle, wedge_start=obj.wedge_start, color=obj.color, name=obj.name, opacity=obj.opacity)
    elif isinstance(obj, Cone):
        return get_meep_cone(obj.center, obj.radius, obj.radius1, obj.height, obj.axis, color=obj.color, name=obj.name, opacity=obj.opacity)
    elif isinstance(obj, Cylinder):
        return get_meep_cylinder(obj.center, obj.radius, obj.height, obj.axis, color=obj.color, name=obj.name, opacity=obj.opacity)
    else:
        raise ValueError(f"Unsupported geometry type: {type(obj)}")