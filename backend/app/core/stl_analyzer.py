"""
STL geometry analyzer with six-direction machining support.

Rotates the mesh so each face points toward +Z, then analyzes
the bounding box / features for that orientation.
"""
import base64
import io
import logging

import numpy as np
import trimesh

logger = logging.getLogger(__name__)

# Six standard machining directions — each rotates the indicated face
# toward +Z.  Rotation matrices are 4×4 homogeneous transforms.
DIRECTIONS = {
    '+Z': np.eye(4),                                              # top
    '-Z': trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]),  # bottom
    '+X': trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]),  # right
    '-X': trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0]),  # left
    '+Y': trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]),  # front
    '-Y': trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]),  # back
}

DIRECTION_LABELS = {
    '+Z': '顶面(+Z)', '-Z': '底面(-Z)',
    '+X': '右面(+X)', '-X': '左面(-X)',
    '+Y': '前面(+Y)', '-Y': '后面(-Y)',
}


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def load_mesh(stl_base64: str) -> trimesh.Trimesh:
    if not stl_base64:
        raise ValueError("STL数据为空")
    try:
        stl_bytes = base64.b64decode(stl_base64)
    except Exception as e:
        raise ValueError(f"Base64解码失败: {e}")
    if not stl_bytes:
        raise ValueError("STL内容为空")
    mesh = trimesh.load(io.BytesIO(stl_bytes), file_type='stl')
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("非三角网格，请确认是STL格式")
    if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
        raise ValueError("无顶点/面片数据")
    return mesh


def analyze_stl(stl_base64: str, direction: str = '+Z') -> dict:
    """Analyze an STL after orienting the requested machining direction to +Z."""
    mesh = load_mesh(stl_base64)
    if direction not in DIRECTIONS:
        raise ValueError(f"不支持的加工方向: {direction}")
    if direction != '+Z':
        mesh.apply_transform(DIRECTIONS[direction])
    result = _analyze_mesh(mesh)
    result['direction'] = direction
    result['label'] = DIRECTION_LABELS[direction]
    return result


def analyze_all_directions(stl_base64: str) -> dict:
    """Analyze the part from all six machining directions."""
    mesh = load_mesh(stl_base64)
    directions = {}
    for name, transform in DIRECTIONS.items():
        oriented_mesh = mesh.copy()
        if name != '+Z':
            oriented_mesh.apply_transform(transform)
        directions[name] = _analyze_mesh(oriented_mesh)
        directions[name]['direction'] = name
        directions[name]['label'] = DIRECTION_LABELS[name]

    # Determine which directions are actually needed
    needed = _filter_needed_directions(directions)

    logger.info(
        "六方向分析完成: 共%d方向, 需加工%d方向: %s",
        len(directions), len(needed),
        ', '.join(needed.keys()),
    )
    return {
        'directions': directions,
        'needed_directions': list(needed.keys()),
    }


# ---------------------------------------------------------------------------
# internal analysis
# ---------------------------------------------------------------------------

def _analyze_mesh(mesh: trimesh.Trimesh) -> dict:
    bounds = mesh.bounds
    size = bounds[1] - bounds[0]
    w, h, d = float(size[0]), float(size[1]), float(size[2])
    is_watertight = bool(mesh.is_watertight)

    return {
        'width': round(w, 2),
        'height': round(h, 2),
        'depth': round(d, 2),
        'bounds': [[round(float(v), 2) for v in bounds[0]],
                   [round(float(v), 2) for v in bounds[1]]],
        'vertex_count': len(mesh.vertices),
        'face_count': len(mesh.faces),
        'surface_area': round(float(mesh.area), 2),
        'is_watertight': is_watertight,
        'volume': round(float(mesh.volume) if is_watertight else 0, 2),
        'shape_profile': _classify_shape(w, h, d),
        'face_distribution': _classify_faces(mesh),
        'cross_sections': _cross_sections(mesh, bounds[0][2], bounds[1][2]),
        'boundary_loops': _detect_boundary_loops(mesh),
    }


def _filter_needed_directions(directions: dict) -> dict:
    """Filter out directions that don't need machining.

    A direction is NOT needed if:
    - The face is essentially flat (depth < 0.5mm)
    - It's the opposite of another identical face (symmetric)
    """
    needed = {}
    for name, info in directions.items():
        if info['depth'] < 0.5:
            continue
        # simple faces (thin wall) don't need separate machining
        if info['shape_profile']['is_flat'] and info['depth'] < 1.0:
            continue
        needed[name] = info

    # Always include +Z if nothing else qualifies
    if not needed and '+Z' in directions:
        needed['+Z'] = directions['+Z']

    return needed


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _classify_shape(w, h, d):
    aspect_ratio = max(w, h) / max(min(w, h), 0.001)
    return {
        'aspect_ratio': round(aspect_ratio, 2),
        'is_flat': d < max(w, h) * 0.25,
        'is_cubic': max(w, h, d) / max(min(w, h, d), 0.001) < 1.5,
        'is_deep_pocket': d > 30 or d > max(w, h) * 0.5,
    }


def _classify_faces(mesh):
    normals = mesh.face_normals
    areas = mesh.area_faces
    total = float(areas.sum()) or 1.0
    zc = np.abs(normals[:, 2])
    return {
        'top_pct': round(float(areas[zc > 0.9].sum() / total * 100), 1),
        'side_pct': round(float(areas[zc < 0.1].sum() / total * 100), 1),
        'angled_pct': round(float(areas[(zc >= 0.1) & (zc <= 0.9)].sum() / total * 100), 1),
    }


def _cross_sections(mesh, z_min, z_max, num=6):
    if z_max - z_min < 0.01:
        return []
    sections = []
    for z in np.linspace(z_min + 0.01, z_max - 0.01, min(num, 10)):
        try:
            sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        except Exception:
            continue
        if sec is None:
            continue
        verts_2d = sec.vertices[:, :2]
        if len(verts_2d) < 3:
            continue
        try:
            from scipy.spatial import ConvexHull
            hull = ConvexHull(verts_2d)
            sec_area = float(hull.volume)
        except Exception:
            mm = verts_2d.min(axis=0)
            mx = verts_2d.max(axis=0)
            sec_area = float((mx[0] - mm[0]) * (mx[1] - mm[1]))
        sections.append({'z': round(float(z), 2), 'cross_section_area': round(sec_area, 2)})
    return sections


def _detect_boundary_loops(mesh):
    if not hasattr(mesh, 'edges_unique'):
        return []
    try:
        edges = mesh.edges_unique
        edges_face = getattr(mesh, 'edges_face', None)
    except Exception:
        return []
    if edges_face is None or len(edges_face) == 0:
        return []
    ef = np.asarray(edges_face)
    if ef.ndim == 1:
        return []
    boundary_mask = ef[:, 1] == -1
    boundary_edges = edges[boundary_mask]
    if len(boundary_edges) < 6:
        return []
    loops = _group_boundary_loops(boundary_edges, mesh.vertices)
    result = []
    for verts in loops:
        if len(verts) < 6:
            continue
        pts = mesh.vertices[verts]
        center = pts.mean(axis=0)
        radius = float(np.linalg.norm(pts - center, axis=1).mean())
        result.append({
            'center_x': round(float(center[0]), 2),
            'center_y': round(float(center[1]), 2),
            'approx_diameter': round(float(radius * 2), 2),
            'vertex_count': len(verts),
        })
    return result


def _group_boundary_loops(edges, vertices):
    n = len(vertices)
    adj = {i: [] for i in range(n)}
    for e in edges:
        a, b = int(e[0]), int(e[1])
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    visited = set()
    loops = []
    for start in adj:
        if start in visited or len(adj[start]) != 2:
            continue
        loop = []
        cur = start
        while cur not in visited:
            visited.add(cur)
            loop.append(cur)
            nbrs = [x for x in adj[cur] if x not in visited]
            if not nbrs:
                break
            cur = nbrs[0]
        if len(loop) >= 4:
            loops.append(loop)
    return loops


# ---------------------------------------------------------------------------
# operation planner
# ---------------------------------------------------------------------------

def plan_operations(geom: dict, tool_diameter: float = 10.0) -> list:
    """Generate machining operations for one direction."""
    w, h, d = geom['width'], geom['height'], geom['depth']
    is_deep = geom.get('shape_profile', {}).get('is_deep_pocket', d > 30)
    is_flat = geom.get('shape_profile', {}).get('is_flat', d < max(w, h) * 0.25)
    step_over = tool_diameter * 0.7
    max_doc = 3.0
    ops, seq = [], 1

    if is_deep and not is_flat:
        ops += _plan_pocket(w, h, d, step_over, max_doc, seq, tool_diameter)
    else:
        ops += _plan_face_roughing(w, h, d, step_over, max_doc, seq)
        seq = ops[-1]['sequence'] + 1 if ops else 1
        # finishing pass
        ops.append({
            'sequence': seq,
            'content': '精加工-轮廓铣削',
            'parameters': f'X=0, Y=0, WIDTH={w:.2f}, HEIGHT={h:.2f}, Z={-d:.2f}, F=120',
            'equipment': '立铣刀',
            'remark': f'精加工轮廓 | {w:.1f}×{h:.1f}×{d:.1f}mm',
        })
        seq += 1

    ops.append({
        'sequence': seq,
        'content': '返回安全高度',
        'parameters': 'Z=50', 'equipment': 'CNC加工中心', 'remark': '',
    })

    logger.info("工序(%s策略): %d条 | %.1f×%.1f×%.1fmm",
                "型腔" if (is_deep and not is_flat) else "平板", len(ops), w, h, d)
    return ops


def _plan_pocket(w, h, d, step_over, max_doc, start_seq, tool_dia):
    """Production-grade pocket machining.

    Strategy:
    1. Rough each layer with 0.3mm wall stock (no per-layer wall finish!)
    2. Floor finish with ramp entry (no plunge)
    3. ONE final wall finish pass at full depth — eliminates step marks
    """
    ops = []
    seq = start_seq
    cur_z = 0.0
    stock = 0.3                     # wall stock for finishing
    r = tool_dia / 2                # tool radius
    rx = r + stock                  # roughing X start
    rx_end = w - r - stock          # roughing X end
    ry = r + stock                  # roughing Y start
    ry_end = h - r - stock          # roughing Y end

    # ---- roughing layers (no wall finish between layers!) ----
    while cur_z < d:
        pass_d = min(max_doc, d - cur_z)
        z_target = -(cur_z + pass_d)

        ops.append({
            'sequence': seq,
            'content': f'斜坡进刀-Z{abs(z_target):.1f}',
            'parameters': f'RAMP_X={r + 2:.1f}, RAMP_Y={r + 2:.1f}, Z={z_target:.2f}, F=200',
            'equipment': '立铣刀',
            'remark': f'斜坡进刀 | 壁面留{stock}mm余量',
        })
        seq += 1

        ops.append({
            'sequence': seq,
            'content': f'型腔粗加工-第{seq // 2}层',
            'parameters': (
                f'X={rx:.1f}, Y={ry:.1f},'
                f' X_END={rx_end:.1f}, Y_END={ry_end:.1f},'
                f' Z={z_target:.2f}, F=300, STEP={step_over:.1f}'
            ),
            'equipment': '立铣刀',
            'remark': f'粗加工Z={z_target:.1f} | 余量{stock}mm | DOC={pass_d:.1f}mm',
        })
        seq += 1
        cur_z += pass_d

    # ---- floor finish (ramp entry, then zigzag) ----
    ops.append({
        'sequence': seq,
        'content': '斜坡进刀-底面精加工',
        'parameters': f'RAMP_X={r:.1f}, RAMP_Y={r:.1f}, Z={-d:.2f}, F=150',
        'equipment': '立铣刀',
        'remark': '底面精加工斜坡进刀 (禁止直插)',
    })
    seq += 1

    ops.append({
        'sequence': seq,
        'content': '底面精加工',
        'parameters': (
            f'X={r:.1f}, Y={r:.1f},'
            f' X_END={w - r:.1f}, Y_END={h - r:.1f},'
            f' Z={-d:.2f}, F=120, STEP={step_over * 0.5:.1f}'
        ),
        'equipment': '立铣刀',
        'remark': f'底面光刀 | {w:.1f}×{h:.1f}mm | STEP={step_over * 0.5:.1f}mm',
    })
    seq += 1

    # ---- ONE final wall finish (eliminates all layer marks) ----
    ops.append({
        'sequence': seq,
        'content': '侧壁精修-最终',
        'parameters': (
            f'X={r:.1f}, Y={r:.1f},'
            f' WIDTH={w - r:.1f}, HEIGHT={h - r:.1f},'
            f' Z={-d:.2f}, F=120'
        ),
        'equipment': '立铣刀',
        'remark': f'最终壁面精修 | 刀径补偿{r:.1f}mm | 一刀消除所有层痕',
    })

    return ops


def _plan_face_roughing(w, h, d, step_over, max_doc, start_seq):
    """Standard top-down face milling (for flat/shallow parts)."""
    ops = []
    seq = start_seq
    cur_z = 0.0
    while cur_z < d:
        pass_d = min(max_doc, d - cur_z)
        z_target = -(cur_z + pass_d)
        ops.append({
            'sequence': seq,
            'content': f'粗加工-平面铣削(第{seq}刀)',
            'parameters': (
                f'X=0, Y=0, X_END={w:.2f}, Y_END={h:.2f},'
                f' Z={z_target:.2f}, F=300, STEP={step_over:.2f}'
            ),
            'equipment': '立铣刀',
            'remark': f'切深{pass_d:.1f} | 累计{cur_z + pass_d:.1f}/{d:.1f}mm',
        })
        seq += 1
        cur_z += pass_d
    return ops
