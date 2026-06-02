"""
Unified geometry configuration module.
Combines geometry classes, mesh generation, configuration dialog, and utilities.
"""

import streamlit as st
import numpy as np
import pandas as pd
import uuid
import plotly.graph_objects as go
from scipy.spatial import distance
from mat import MATERIAL_KEYS
from utils import clear_temp, card_widget

# ============================================================================
# GEOMETRY CLASSES AND MESH GENERATION (from geo_mesh3d.py)
# ============================================================================

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

def get_meep_prism_mesh(vertices_list, height, prism_axis, sidewall_angle, 
                        bottom_center=None, color="purple", name="Prism", opacity=OPACITY):
    """
    Generate Plotly Trace (go.Mesh3d) for a Meep Prism.
    """
    pts = np.array(vertices_list)
    N = len(pts)
    if N < 3:
        raise ValueError("Prism base must have at least 3 vertices.")
    
    geom_center_2d = np.mean(pts, axis=0)
    if bottom_center is not None:
        bc_3d = np.array(bottom_center)
        pts_centered = pts - geom_center_2d
    else:
        pts_centered = pts - geom_center_2d
        bc_3d = np.array([0, 0, 0])

    delta_r = height * np.tan(sidewall_angle)
    
    local_vertices = []
    
    for p in pts_centered:
        local_vertices.append([p[0], p[1], 0])
        
    for p in pts_centered:
        r_norm = np.linalg.norm(p)
        if r_norm == 0:
            local_vertices.append([0, 0, height])
        else:
            r_unit = p / r_norm
            scaled_p = p - delta_r * r_unit
            local_vertices.append([scaled_p[0], scaled_p[1], height])
            
    local_vertices = np.array(local_vertices)

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
        
    global_vertices = (R @ local_vertices.T).T + bc_3d
    
    x, y, z = global_vertices[:, 0], global_vertices[:, 1], global_vertices[:, 2]

    idx_i, idx_j, idx_k = [], [], []
    
    for i in range(N):
        next_i = (i + 1) % N
        idx_i.append(i)
        idx_j.append(next_i)
        idx_k.append(i + N)
        idx_i.append(next_i)
        idx_j.append(next_i + N)
        idx_k.append(i + N)

    for i in range(1, N - 1):
        idx_i.append(0)
        idx_j.append(i)
        idx_k.append(i + 1)
        idx_i.append(N)
        idx_j.append(i + N)
        idx_k.append(i + 1 + N)

    return go.Mesh3d(
        x=x, y=y, z=z, i=idx_i, j=idx_j, k=idx_k,
        color=color, opacity=opacity, name=name,
        showlegend=True,
        flatshading=True 
    )

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


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

@st.cache_data
def get_mesh(sx, sy, sz, nx, ny, nz):
    """Generate mesh grid for simulation results visualization."""
    x, y, z = np.meshgrid(np.linspace(-sx/2, sx/2, nx), 
                         np.linspace(-sy/2, sy/2, ny), 
                         np.linspace(-sz/2, sz/2, nz), indexing='ij')
    return x.flatten(), y.flatten(), z.flatten()


# ============================================================================
# VALIDATION AND UI FUNCTIONS
# ============================================================================

def _validate_geom(geom):
    """Validate geometry parameters."""
    if not isinstance(geom.center, tuple) or len(geom.center) != 3:
        return False, "Geometry center must be a tuple of 3 values."
    if not all(isinstance(v, (int, float)) for v in geom.center):
        return False, "Geometry center values must be numeric(int or float)."

    if isinstance(geom, Sphere):
        if not isinstance(geom.radius, (int, float)) or geom.radius < 0:
            return False, "Sphere radius must be a non-negative number."
    if isinstance(geom, Block) or isinstance(geom, Ellipsoid):
        if not all(isinstance(v, (int, float)) for v in geom.size):
            return False, "Block / Ellipsoid size values must be numeric(int or float)."
        if any(v <= 0 for v in geom.size):
            return False, "Block / Ellipsoid size values must be greater than 0."
        if (np.all(np.isclose(geom.e1, 0.0, atol=1e-7)) or 
            np.all(np.isclose(geom.e2, 0.0, atol=1e-7)) or 
            np.all(np.isclose(geom.e3, 0.0, atol=1e-7))):
            return False, "Block / Ellipsoid axes cannot be the zero vector."
        if (np.allclose(np.cross(geom.e1, geom.e2), 0.0, atol=1e-7) or
            np.allclose(np.cross(geom.e2, geom.e3), 0.0, atol=1e-7) or
            np.allclose(np.cross(geom.e1, geom.e3), 0.0, atol=1e-7)):
            return False, "Block / Ellipsoid axes must be mutually non-collinear (cannot be parallel)."
    if isinstance(geom, Cylinder):
        if not isinstance(geom.radius, (int, float)) or geom.radius < 0:
            return False, "Cylinder radius must be a non-negative number."
        if not isinstance(geom.height, (int, float)) or geom.height < 0:
            return False, "Cylinder height must be a non-negative number."
        if geom.axis == (0, 0, 0):
            return False, "Cylinder axis cannot be the zero vector."
        if isinstance(geom, Cone):
            if not isinstance(geom.radius1, (int, float)) or geom.radius1 < 0:
                return False, "Cone top radius must be a non-negative number."
        if isinstance(geom, Wedge):
            if not isinstance(geom.wedge_angle, (int, float)) or geom.wedge_angle < 0:
                return False, "Wedge angle must be a non-negative number."
            if geom.wedge_angle >= 2*np.pi:
                return False, "Wedge angle must be less than 360 degrees (2*pi radians)."
            if geom.wedge_start == (0, 0, 0):
                return False, "Wedge start vector cannot be the zero vector."
            if np.allclose(np.cross(geom.axis, geom.wedge_start), 0.0, atol=1e-6):
                return False, "Wedge start vector cannot be parallel to the axis." 
        if isinstance(geom, Prism):
            pass

    return True, None


@st.dialog("Geometry configuration", width='medium')
def geo_cfg(old_cfg=None, edit_idx=None):
    """Geometry configuration dialog."""
    default_type = None
    default_name = None
    default_color = None
    default_material = None
    default_center = [None, None, None]
    default_sphere_r = None
    default_block_sx = None
    default_block_sy = None
    default_block_sz = None
    default_block_e1 = (1.0, 0.0, 0.0)
    default_block_e2 = (0.0, 1.0, 0.0)
    default_block_e3 = (0.0, 0.0, 1.0)
    default_block_ellipsoid = False
    default_cylinder_r = None
    default_cylinder_h = None
    default_cylinder_axis = (0.0, 0.0, 1.0)
    default_cylinder_subclass = False
    default_cylinder_subclass_type = "Cone"
    default_cylinder_radius2 = None
    default_cylinder_wedge_angle = None
    default_cylinder_wedge_vec = (1.0, 0.0, 0.0)
    default_prism_vertices = None
    default_prism_h = None
    default_prism_axis = (0.0, 0.0, 1.0)
    default_prism_center_checkbox = False
    default_prism_center = (None, None, None)
    default_prism_sidewall_angle = 0

    if old_cfg is not None:
        cfg_type = type(old_cfg).__name__
        default_color = getattr(old_cfg, 'color', None)
        default_name = getattr(old_cfg, 'name', None)
        default_material = getattr(old_cfg, 'material', None)
        if hasattr(old_cfg, 'center'):
            center = getattr(old_cfg, 'center')
            if center is not None:
                default_center = list(center)
        if cfg_type == 'Sphere':
            default_type = 'Sphere'
            default_sphere_r = getattr(old_cfg, 'radius', None)
        elif cfg_type == 'Ellipsoid':
            default_type = 'Block'
            default_block_ellipsoid = True
            default_block_sx, default_block_sy, default_block_sz = getattr(old_cfg, 'size', (None, None, None))
            default_block_e1 = getattr(old_cfg, 'e1', default_block_e1)
            default_block_e2 = getattr(old_cfg, 'e2', default_block_e2)
            default_block_e3 = getattr(old_cfg, 'e3', default_block_e3)
        elif cfg_type == 'Block':
            default_type = 'Block'
            default_block_sx, default_block_sy, default_block_sz = getattr(old_cfg, 'size', (None, None, None))
            default_block_e1 = getattr(old_cfg, 'e1', default_block_e1)
            default_block_e2 = getattr(old_cfg, 'e2', default_block_e2)
            default_block_e3 = getattr(old_cfg, 'e3', default_block_e3)
        elif cfg_type == 'Cone':
            default_type = 'Cylinder'
            default_cylinder_subclass = True
            default_cylinder_subclass_type = 'Cone'
            default_cylinder_r = getattr(old_cfg, 'radius', None)
            default_cylinder_h = getattr(old_cfg, 'height', None)
            default_cylinder_axis = getattr(old_cfg, 'axis', default_cylinder_axis)
            default_cylinder_radius2 = getattr(old_cfg, 'radius1', None)
        elif cfg_type == 'Wedge':
            default_type = 'Cylinder'
            default_cylinder_subclass = True
            default_cylinder_subclass_type = 'Wedge'
            default_cylinder_r = getattr(old_cfg, 'radius', None)
            default_cylinder_h = getattr(old_cfg, 'height', None)
            default_cylinder_axis = getattr(old_cfg, 'axis', default_cylinder_axis)
            default_cylinder_wedge_angle = getattr(old_cfg, 'wedge_angle', None)
            default_cylinder_wedge_vec = getattr(old_cfg, 'wedge_start', default_cylinder_wedge_vec)
        elif cfg_type == 'Cylinder':
            default_type = 'Cylinder'
            default_cylinder_r = getattr(old_cfg, 'radius', None)
            default_cylinder_h = getattr(old_cfg, 'height', None)
            default_cylinder_axis = getattr(old_cfg, 'axis', default_cylinder_axis)
            default_cylinder_subclass = False
        elif cfg_type == 'Prism':
            default_type = 'Prism'
            default_prism_vertices = getattr(old_cfg, 'vertices_list', None) or getattr(old_cfg, 'vertices', None)
            default_prism_h = getattr(old_cfg, 'height', None)
            default_prism_axis = getattr(old_cfg, 'prism_axis', getattr(old_cfg, 'axis', default_prism_axis))
            default_prism_center_checkbox = getattr(old_cfg, 'shift_center', None) is not None
            if default_prism_center_checkbox:
                default_prism_center = tuple(getattr(old_cfg, 'shift_center', default_prism_center))
            default_prism_sidewall_angle = getattr(old_cfg, 'sidewall_angle', default_prism_sidewall_angle)

    temp_geo_type = st.session_state.get('tg_type', default_type or "Block")
    temp_geo_name = st.session_state.get('tg_name', default_name or "")
    temp_geo_mat = st.session_state.get('tg_mat', default_material if default_material in MATERIAL_KEYS else MATERIAL_KEYS[0])
    temp_geo_center = [
        st.session_state.get('tg_cx', default_center[0]),
        st.session_state.get('tg_cy', default_center[1]),
        st.session_state.get('tg_cz', default_center[2]),
    ]
    temp_geo_color = st.session_state.get('tg_color', default_color or "#000000")
    if st.button("Confirm", type="primary", use_container_width=True):
        new_geom = None
        if temp_geo_type == "Sphere":
            new_geom = Sphere(
                color=temp_geo_color,
                name=temp_geo_name + " (Sphere)" if " (Sphere)" not in temp_geo_name else temp_geo_name,
                material=temp_geo_mat,
                center=tuple(temp_geo_center),
                radius=st.session_state.get('t_sphere_r'),
            )
        if temp_geo_type == "Block":
            if st.session_state.get("t_block_ellipsoid"):
                new_geom = Ellipsoid(
                    color=temp_geo_color,
                    name=temp_geo_name + " (Ellipsoid)" if " (Ellipsoid)" not in temp_geo_name else temp_geo_name,
                    material=temp_geo_mat,
                    center=tuple(temp_geo_center),
                    size=(
                        st.session_state.get('t_block_sx'),
                        st.session_state.get('t_block_sy'),
                        st.session_state.get('t_block_sz'),
                    ),
                    e1=(
                        st.session_state.get('t_block_e1x'),
                        st.session_state.get('t_block_e1y'),
                        st.session_state.get('t_block_e1z'),
                    ),
                    e2=(
                        st.session_state.get('t_block_e2x'),
                        st.session_state.get('t_block_e2y'),
                        st.session_state.get('t_block_e2z'),
                    ),
                    e3=(
                        st.session_state.get('t_block_e3x'),
                        st.session_state.get('t_block_e3y'),
                        st.session_state.get('t_block_e3z'),
                    ),
                )
            else:
                new_geom = Block(
                    color=temp_geo_color,
                    name=temp_geo_name + " (Block)" if " (Block)" not in temp_geo_name else temp_geo_name,
                    material=temp_geo_mat,
                    center=tuple(temp_geo_center),
                    size=(
                        st.session_state.get('t_block_sx'),
                        st.session_state.get('t_block_sy'),
                        st.session_state.get('t_block_sz'),
                    ),
                    e1=(
                        st.session_state.get('t_block_e1x'),
                        st.session_state.get('t_block_e1y'),
                        st.session_state.get('t_block_e1z'),
                    ),
                    e2=(
                        st.session_state.get('t_block_e2x'),
                        st.session_state.get('t_block_e2y'),
                        st.session_state.get('t_block_e2z'),
                    ),
                    e3=(
                        st.session_state.get('t_block_e3x'),
                        st.session_state.get('t_block_e3y'),
                        st.session_state.get('t_block_e3z'),
                    ),
                )
        if temp_geo_type == "Cylinder":
            if st.session_state.get("t_cylinder_subclass"):
                if st.session_state.get('t_cylinder_subclass_type') == "Cone":
                    new_geom = Cone(
                        color=temp_geo_color,
                        name=temp_geo_name + " (Cone)" if " (Cone)" not in temp_geo_name else temp_geo_name,
                        material=temp_geo_mat,
                        center=tuple(temp_geo_center),
                        radius=st.session_state.get('t_cylinder_r'),
                        radius1=st.session_state.get('t_cylinder_radius2'),
                        height=st.session_state.get('t_cylinder_h'),
                        axis=(
                            st.session_state.get('t_cylinder_axis_x'),
                            st.session_state.get('t_cylinder_axis_y'),
                            st.session_state.get('t_cylinder_axis_z'),
                        ),
                    )
                else:
                    new_geom = Wedge(
                        color=temp_geo_color,
                        name=temp_geo_name + " (Wedge)" if " (Wedge)" not in temp_geo_name else temp_geo_name,
                        material=temp_geo_mat,
                        center=tuple(temp_geo_center),
                        radius=st.session_state.get('t_cylinder_r'),
                        height=st.session_state.get('t_cylinder_h'),
                        axis=(
                            st.session_state.get('t_cylinder_axis_x'),
                            st.session_state.get('t_cylinder_axis_y'),
                            st.session_state.get('t_cylinder_axis_z'),
                        ),
                        wedge_angle=st.session_state.get('t_cylinder_wedge_angle'),
                        wedge_start=(
                            st.session_state.get('t_cylinder_wedge_x'),
                            st.session_state.get('t_cylinder_wedge_y'),
                            st.session_state.get('t_cylinder_wedge_z'),
                        ),
                    )
            else:
                new_geom = Cylinder(
                    color=temp_geo_color,
                    name=temp_geo_name + " (Cylinder)" if " (Cylinder)" not in temp_geo_name else temp_geo_name,
                    material=temp_geo_mat,
                    center=tuple(temp_geo_center),
                    radius=st.session_state.get('t_cylinder_r'),
                    height=st.session_state.get('t_cylinder_h'),
                    axis=(
                        st.session_state.get('t_cylinder_axis_x'),
                        st.session_state.get('t_cylinder_axis_y'),
                        st.session_state.get('t_cylinder_axis_z'),
                    ),
                )
        if temp_geo_type == "Prism":
            new_geom = Prism(
                color=temp_geo_color,
                name=temp_geo_name + " (Prism)" if " (Prism)" not in temp_geo_name else temp_geo_name,
                material=temp_geo_mat,
                center=tuple(temp_geo_center),
                vertices_list=st.session_state.get('t_prism_vertices'),
                height=st.session_state.get('t_prism_h'),
                prism_axis=(
                    st.session_state.get('t_prism_axis_x'),
                    st.session_state.get('t_prism_axis_y'),
                    st.session_state.get('t_prism_axis_z'),
                ),
                sidewall_angle=st.session_state.get('t_prism_sidewall_angle'),
                shift_center=(
                    st.session_state.get('t_prism_x'),
                    st.session_state.get('t_prism_y'),
                    st.session_state.get('t_prism_z'),
                ) if st.session_state.get('t_prism_center_checkbox') else None,
            )
        if new_geom is not None:
            valid, err = _validate_geom(new_geom)
            if valid:
                if edit_idx is not None and 0 <= edit_idx < len(st.session_state.geoms):
                    st.session_state.geoms[edit_idx] = new_geom
                else:
                    st.session_state.geoms.append(new_geom)
                    st.toast(f"**Geometry {new_geom.name} added.**", icon="✔️")
                clear_temp()
                st.rerun()
            else:
                st.toast(f"**Invalid geometry:** {err}", icon="⚠️")

    geo_left, geo_right = st.columns(2)
    with geo_left:
        st.write("General parameters")
        temp_geo_type = st.selectbox(
            "Type",
            ["Block", "Sphere", "Cylinder", "Prism"],
            index=0 if default_type is None else ["Block", "Sphere", "Cylinder", "Prism"].index(default_type),
            key='tg_type',
        )
        temp_geo_name = st.text_input("Name", placeholder="Name of the geometry", key='tg_name', value=default_name or "")
        temp_geo_mat = st.selectbox(
            "Material",
            MATERIAL_KEYS,
            index=0 if default_material not in MATERIAL_KEYS else MATERIAL_KEYS.index(default_material),
            key='tg_mat',
        )
        x, y, z = st.columns(3)
        temp_geo_center = [None] * 3
        temp_geo_center[0] = x.number_input("Center", label_visibility='visible', placeholder="X", value=default_center[0], key='tg_cx')
        temp_geo_center[1] = y.number_input("Center", label_visibility='hidden', placeholder="Y", value=default_center[1], key='tg_cy')
        temp_geo_center[2] = z.number_input("Center", label_visibility='hidden', placeholder="Z", value=default_center[2], key='tg_cz')
        temp_geo_color = st.color_picker("Pick a color", value=default_color or "#000000", key="tg_color")

    with geo_right:
        st.write("Type parameters")
        if temp_geo_type is None:
            st.error("Please specify geometry type.")
        else:
            if temp_geo_type == "Sphere":
                temp_radius = st.number_input("Radius", value=default_sphere_r, key="t_sphere_r")
            elif temp_geo_type == "Block":
                size_x, size_y, size_z = st.columns(3)
                temp_s = [None] * 3
                temp_s[0] = size_x.number_input("Size", label_visibility='visible', placeholder="Size X", value=default_block_sx, key="t_block_sx")
                temp_s[1] = size_y.number_input("Size", label_visibility='hidden', placeholder="Size Y", value=default_block_sy, key="t_block_sy")
                temp_s[2] = size_z.number_input("Size", label_visibility='hidden', placeholder="Size Z", value=default_block_sz, key="t_block_sz")
                with st.expander("Block axes", expanded=False):
                    axes_x, axes_y, axes_z = st.columns(3)
                    temp_e1 = [None] * 3
                    temp_e2 = [None] * 3
                    temp_e3 = [None] * 3
                    temp_e1[0] = axes_x.number_input(r"$\vec{e_1}$", label_visibility='visible', placeholder="X", value=default_block_e1[0], key="t_block_e1x")
                    temp_e1[1] = axes_y.number_input(r"$\vec{e_1}$", label_visibility='hidden', placeholder="Y", value=default_block_e1[1], key="t_block_e1y")
                    temp_e1[2] = axes_z.number_input(r"$\vec{e_1}$", label_visibility='hidden', placeholder="Z", value=default_block_e1[2], key="t_block_e1z")
                    temp_e2[0] = axes_x.number_input(r"$\vec{e_2}$", label_visibility='visible', placeholder="X", value=default_block_e2[0], key="t_block_e2x")
                    temp_e2[1] = axes_y.number_input(r"$\vec{e_2}$", label_visibility='hidden', placeholder="Y", value=default_block_e2[1], key="t_block_e2y")
                    temp_e2[2] = axes_z.number_input(r"$\vec{e_2}$", label_visibility='hidden', placeholder="Z", value=default_block_e2[2], key="t_block_e2z")
                    temp_e3[0] = axes_x.number_input(r"$\vec{e_3}$", label_visibility='visible', placeholder="X", value=default_block_e3[0], key="t_block_e3x")
                    temp_e3[1] = axes_y.number_input(r"$\vec{e_3}$", label_visibility='hidden', placeholder="Y", value=default_block_e3[1], key="t_block_e3y")
                    temp_e3[2] = axes_z.number_input(r"$\vec{e_3}$", label_visibility='hidden', placeholder="Z", value=default_block_e3[2], key="t_block_e3z")
                ellipsoid = st.checkbox("Make it Ellipsoid", value=default_block_ellipsoid, key="t_block_ellipsoid")

            elif temp_geo_type == "Cylinder":
                temp_radius = st.number_input("Radius", value=default_cylinder_r, key="t_cylinder_r")
                temp_height = st.number_input("Height", value=default_cylinder_h, key="t_cylinder_h")
                with st.expander("Cylinder axis", expanded=False):
                    axis_x, axis_y, axis_z = st.columns(3)
                    temp_cylinder_axis = [None] * 3
                    temp_cylinder_axis[0] = axis_x.number_input("Axis", label_visibility='visible', placeholder="X", value=default_cylinder_axis[0], key="t_cylinder_axis_x")
                    temp_cylinder_axis[1] = axis_y.number_input("Axis", label_visibility='hidden', placeholder="Y", value=default_cylinder_axis[1], key="t_cylinder_axis_y")
                    temp_cylinder_axis[2] = axis_z.number_input("Axis", label_visibility='hidden', placeholder="Z", value=default_cylinder_axis[2], key="t_cylinder_axis_z")

                with st.expander("Subclass", expanded=False):
                    if st.checkbox("Make it subclass", value=default_cylinder_subclass, key="t_cylinder_subclass"):
                        subs = st.radio("Subclass type", ["Cone", "Wedge"], key="t_cylinder_subclass_type", index=0 if default_cylinder_subclass_type == "Cone" else 1)
                        if subs == "Cone":
                            radius2 = st.number_input("Top radius", value=default_cylinder_radius2, key="t_cylinder_radius2")
                        if subs == "Wedge":
                            angle = st.number_input("Wedge angle", placeholder='Degree or radian in unit of pi', value=default_cylinder_wedge_angle, key="t_cylinder_wedge_angle")
                            wedge_vec_x, wedge_vec_y, wedge_vec_z = st.columns(3)
                            temp_wedge_vec = [None] * 3
                            temp_wedge_vec[0] = wedge_vec_x.number_input("Wedge vector", label_visibility='visible', placeholder="X", value=default_cylinder_wedge_vec[0], key="t_cylinder_wedge_x")
                            temp_wedge_vec[1] = wedge_vec_y.number_input("Wedge vector", label_visibility='hidden', placeholder="Y", value=default_cylinder_wedge_vec[1], key="t_cylinder_wedge_y")
                            temp_wedge_vec[2] = wedge_vec_z.number_input("Wedge vector", label_visibility='hidden', placeholder="Z", value=default_cylinder_wedge_vec[2], key="t_cylinder_wedge_z")
            elif temp_geo_type == "Prism":
                vertices = st.text_area("Vertices list", value=default_prism_vertices or "", placeholder="Enter vertices as (x,y,z) per line. They must lie in a plane that's perpendicular to the axis.", key="t_prism_vertices")
                temp_height = st.number_input("Height", value=default_prism_h, key="t_prism_h")
                with st.expander("Prism axis", expanded=False):
                    axis_x, axis_y, axis_z = st.columns(3)
                    temp_prism_axis = [None] * 3
                    temp_prism_axis[0] = axis_x.number_input("Axis", label_visibility='visible', placeholder="X", value=default_prism_axis[0], key="t_prism_axis_x")
                    temp_prism_axis[1] = axis_y.number_input("Axis", label_visibility='hidden', placeholder="Y", value=default_prism_axis[1], key="t_prism_axis_y")
                    temp_prism_axis[2] = axis_z.number_input("Axis", label_visibility='hidden', placeholder="Z", value=default_prism_axis[2], key="t_prism_axis_z")
                with st.expander("Center and angle", expanded=False):
                    if st.checkbox("Shift center", value=default_prism_center_checkbox, key="t_prism_center_checkbox"):
                        prism_x, prism_y, prism_z = st.columns(3)
                        temp_prism_center = [None] * 3
                        temp_prism_center[0] = prism_x.number_input("Bottom center", label_visibility='visible', placeholder="X", value=default_prism_center[0], key="t_prism_x")
                        temp_prism_center[1] = prism_y.number_input("Bottom center", label_visibility='hidden', placeholder="Y", value=default_prism_center[1], key="t_prism_y")
                        temp_prism_center[2] = prism_z.number_input("Bottom center", label_visibility='hidden', placeholder="Z", value=default_prism_center[2], key="t_prism_z")
                    temp_sidewall_angle = st.number_input("Sidewall angle", placeholder='Degree or radian in unit of pi', value=default_prism_sidewall_angle, key="t_prism_sidewall_angle")
