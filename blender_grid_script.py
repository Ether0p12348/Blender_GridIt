"""
blender_grid_script.py
======================

This script creates a new mesh object filled with a regular 2D grid of quads
inside the outline of the currently selected mesh object.  The grid spacing is
defined in world‐space by the ``step`` argument (defaults to 0.001 units).  The
algorithm proceeds as follows:

1.  A boundary loop is extracted from the selected object.  A boundary edge in
    Blender is one that is attached to exactly one face.  According to the
    Blender Python API, the :class:`bmesh.types.BMEdge.is_boundary` property
    returns ``True`` when an edge is on the boundary of a face【104200153471113†L2668-L2673】.  These
    edges collectively outline the silhouette of the mesh on the selected
    side.
2.  The boundary vertices are transformed into world space so the grid can be
    aligned with world coordinates.  We then compute the bounding box of this
    outline projected onto the XY plane.  From this box we derive a set of
    vertical and horizontal grid lines spaced by ``step``.
3.  Each boundary edge is sliced at the points where it crosses a grid line.
    The function :func:`mathutils.geometry.intersect_line_line_2d` is used to
    calculate the intersection between a boundary segment and a grid line.  This
    function accepts two 2D segments and returns the intersection point if it
    exists【696737194934486†L2346-L2369】.  Intersections falling within the segment endpoints are
    stored.
4.  The boundary edges are ordered into a closed loop.  A simple adjacency
    traversal is used to connect the boundary edges in sequence.  For meshes
    containing holes, only the first (outermost) loop is considered.
5.  A point‐in‐polygon test (winding number algorithm) determines whether
    candidate grid points lie inside the boundary.  Only points inside the
    polygon are kept.
6.  A new bmesh is created and populated with vertices at the retained grid
    points.  Neighbouring vertices are connected to form edges in a grid
    pattern, and quads are created for each cell.  Finally, the new geometry
    is written out to a new mesh object.

**Note:** A grid spacing of small units produces very high vertex counts for
moderately sized objects.  Consider increasing ``step`` to a larger value
depending on your needs.  Running this script on complex meshes may take a
significant amount of time and power.

Usage:

    In Blender's text editor, load this file and adjust the ``STEP`` value
    if necessary.  Select a planar mesh object in the scene and press ``Run
    Script``.  A new object suffixed with ``_grid`` will appear containing
    the generated grid.
"""

import bpy
import bmesh
from mathutils import Vector
from mathutils import geometry
from collections import defaultdict
import math


def extract_boundary_loop(bm: bmesh.types.BMesh, obj: bpy.types.Object) -> list[Vector]:
    """Return an ordered list of boundary vertices in world space.

    Only the first (outermost) loop is returned.  The orientation of the
    loop is arbitrary but consistent.

    Parameters
    ----------
    bm : :class:`bmesh.types.BMesh`
        The bmesh from which to extract boundary edges.
    obj : :class:`bpy.types.Object`
        The object whose world matrix is applied.

    Returns
    -------
    list[:class:`mathutils.Vector`]
        A list of 2D vectors representing the boundary in world XY space.
    """
    # Build adjacency mapping from vertices to their boundary edges
    boundary_edges = [e for e in bm.edges if e.is_boundary]
    if not boundary_edges:
        return []

    adj: defaultdict[int, list[bmesh.types.BMEdge]] = defaultdict(list)
    for e in boundary_edges:
        v0 = e.verts[0].index
        v1 = e.verts[1].index
        adj[v0].append(e)
        adj[v1].append(e)

    # Choose an arbitrary starting edge and vertex
    start_edge = boundary_edges[0]
    start_vert_idx = start_edge.verts[0].index

    loop_indices = [start_vert_idx]
    current_vert = start_vert_idx
    visited_edges: set[int] = set()

    while True:
        # find next unvisited boundary edge incident to current vertex
        next_edge = None
        for e in adj[current_vert]:
            if e.index not in visited_edges:
                next_edge = e
                break
        if next_edge is None:
            break
        visited_edges.add(next_edge.index)
        # determine other vertex of the edge
        v0 = next_edge.verts[0].index
        v1 = next_edge.verts[1].index
        next_vert_idx = v1 if v0 == current_vert else v0
        current_vert = next_vert_idx
        if current_vert == loop_indices[0]:
            # Closed loop
            break
        loop_indices.append(current_vert)

    # Convert vertex indices to world‐space XY coordinates
    world_coords = []
    for vi in loop_indices:
        v = bm.verts[vi]
        world_co = obj.matrix_world @ v.co
        world_coords.append(Vector((world_co.x, world_co.y)))
    return world_coords


def point_in_polygon(point: Vector, polygon: list[Vector]) -> bool:
    """Determine whether a 2D point is inside a polygon.

    Implements the winding number algorithm.  Points exactly on the
    boundary return True.

    Parameters
    ----------
    point : :class:`mathutils.Vector`
        The point to test (x,y).
    polygon : list[:class:`mathutils.Vector`]
        A sequence of vertices describing the polygon.

    Returns
    -------
    bool
        True if the point lies inside or on the boundary, False otherwise.
    """
    """
    Implementation notes:

    The winding number is incremented or decremented whenever the horizontal
    ray emanating from ``point`` crosses an edge of the polygon.  Before
    computing the winding number we test if ``point`` lies exactly on any
    polygon edge.  This is done by checking colinearity (zero area of the
    triangle) and bounding box containment.
    """
    wn = 0
    num = len(polygon)
    for i in range(num):
        v1 = polygon[i]
        v2 = polygon[(i + 1) % num]
        # Check if point lies exactly on the segment (v1, v2)
        if abs(is_left(v1, v2, point)) < 1e-9:
            if (min(v1.x, v2.x) - 1e-9) <= point.x <= (max(v1.x, v2.x) + 1e-9) and \
               (min(v1.y, v2.y) - 1e-9) <= point.y <= (max(v1.y, v2.y) + 1e-9):
                return True
        # Winding number algorithm
        if v1.y <= point.y:
            if v2.y > point.y:  # upward crossing
                if is_left(v1, v2, point) > 0:
                    wn += 1
        else:
            if v2.y <= point.y:  # downward crossing
                if is_left(v1, v2, point) < 0:
                    wn -= 1
    return wn != 0


def is_left(p0: Vector, p1: Vector, p2: Vector) -> float:
    """Return the z-component of the cross product (p1 - p0) x (p2 - p0).

    Positive when p2 is left of the line p0->p1, negative when right, zero if
    collinear.
    """
    return (p1.x - p0.x) * (p2.y - p0.y) - (p2.x - p0.x) * (p1.y - p0.y)


def slice_boundary_at_grid(boundary: list[Vector], step: float) -> list[tuple[Vector, int, float]]:
    """Compute intersections of the boundary edges with the grid lines.

    This function identifies where the polygon boundary intersects vertical and
    horizontal grid lines spaced at ``step`` intervals.  Each intersection is
    associated with the index of the boundary segment that produced it and the
    parameter ``t`` along that segment (0 at the start vertex and 1 at the
    end).  The output list is sorted in ascending order by segment index and
    parameter.

    Parameters
    ----------
    boundary : list[:class:`mathutils.Vector`]
        Ordered list of boundary vertices (2D world coordinates).
    step : float
        Grid spacing.

    Returns
    -------
    list[tuple[:class:`mathutils.Vector`, int, float]]
        A list of intersection data: (point, segment index, param).
    """
    # Determine bounding box
    xs = [v.x for v in boundary]
    ys = [v.y for v in boundary]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    # Compute grid lines
    start_x = math.floor(min_x / step) * step
    end_x = math.ceil(max_x / step) * step
    start_y = math.floor(min_y / step) * step
    end_y = math.ceil(max_y / step) * step
    x_lines = [start_x + i * step for i in range(int(round((end_x - start_x) / step)) + 1)]
    y_lines = [start_y + j * step for j in range(int(round((end_y - start_y) / step)) + 1)]
    # Dictionary to collect unique intersections keyed by rounded coordinate
    inter_dict: dict[tuple[float, float], tuple[Vector, int, float]] = {}
    num = len(boundary)
    for i in range(num):
        p1 = boundary[i]
        p2 = boundary[(i + 1) % num]
        segment_vec = p2 - p1
        # Skip degenerate edges
        if segment_vec.length < 1e-12:
            continue
        # Check intersections with vertical lines x = const
        for x_val in x_lines:
            # Does the segment cross the vertical line?
            if (p1.x - x_val) * (p2.x - x_val) <= 0:
                # Compute intersection parameter t
                # If p1.x == p2.x (vertical segment) avoid division by zero
                if abs(p2.x - p1.x) > 1e-12:
                    t = (x_val - p1.x) / (p2.x - p1.x)
                    if 0.0 <= t <= 1.0:
                        y_int = p1.y + t * (p2.y - p1.y)
                        # Ensure the intersection lies on the segment (check y bounds)
                        if (min(p1.y, p2.y) - 1e-9) <= y_int <= (max(p1.y, p2.y) + 1e-9):
                            pt = Vector((float(x_val), float(y_int)))
                            key = (round(pt.x, 8), round(pt.y, 8))
                            # Keep the first occurrence for this coordinate
                            if key not in inter_dict:
                                inter_dict[key] = (pt, i, t)
                else:
                    # Segment is vertical and coincides with the grid line; handle intersections at endpoints only
                    if abs(p1.x - x_val) < 1e-9:
                        # Add both endpoints (t=0 and t=1)
                        for t_val, y_val in [(0.0, p1.y), (1.0, p2.y)]:
                            pt = Vector((float(x_val), float(y_val)))
                            key = (round(pt.x, 8), round(pt.y, 8))
                            if key not in inter_dict:
                                inter_dict[key] = (pt, i, t_val)
        # Check intersections with horizontal lines y = const
        for y_val in y_lines:
            if (p1.y - y_val) * (p2.y - y_val) <= 0:
                if abs(p2.y - p1.y) > 1e-12:
                    t = (y_val - p1.y) / (p2.y - p1.y)
                    if 0.0 <= t <= 1.0:
                        x_int = p1.x + t * (p2.x - p1.x)
                        if (min(p1.x, p2.x) - 1e-9) <= x_int <= (max(p1.x, p2.x) + 1e-9):
                            pt = Vector((float(x_int), float(y_val)))
                            key = (round(pt.x, 8), round(pt.y, 8))
                            if key not in inter_dict:
                                inter_dict[key] = (pt, i, t)
                else:
                    # Horizontal segment coinciding with grid line; handle endpoints only
                    if abs(p1.y - y_val) < 1e-9:
                        for t_val, x_val2 in [(0.0, p1.x), (1.0, p2.x)]:
                            pt = Vector((float(x_val2), float(y_val)))
                            key = (round(pt.x, 8), round(pt.y, 8))
                            if key not in inter_dict:
                                inter_dict[key] = (pt, i, t_val)
    # Convert dictionary to list and sort by segment index and parameter
    inter_list = list(inter_dict.values())
    # Sort by segment index, then parameter
    inter_list.sort(key=lambda x: (x[1], x[2]))
    return inter_list


def build_grid_mesh(boundary_points: list[Vector], step: float, name: str = "Grid", extra_points: list[Vector] | None = None, use_extra_as_boundary: bool = False) -> bpy.types.Object:
    """Construct a grid mesh inside a polygon and link it to the current collection.

    Parameters
    ----------
    boundary_points : list[:class:`mathutils.Vector`]
        Ordered boundary loop in world XY space.
    step : float
        Grid spacing.
    name : str, optional
        Name of the new mesh/object.

    Returns
    -------
    :class:`bpy.types.Object`
        The newly created object containing the grid mesh.
    """
    # Determine bounding box
    xs = [v.x for v in boundary_points]
    ys = [v.y for v in boundary_points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    # Generate candidate grid points
    start_x = math.floor(min_x / step) * step
    end_x = math.ceil(max_x / step) * step
    start_y = math.floor(min_y / step) * step
    end_y = math.ceil(max_y / step) * step
    candidate_points = []
    x_count = int(round((end_x - start_x) / step)) + 1
    y_count = int(round((end_y - start_y) / step)) + 1
    for i in range(x_count):
        x_val = start_x + i * step
        for j in range(y_count):
            y_val = start_y + j * step
            pt = Vector((x_val, y_val))
            if point_in_polygon(pt, boundary_points):
                candidate_points.append(pt)

    # Create a new mesh and object
    new_mesh = bpy.data.meshes.new(name)
    new_obj = bpy.data.objects.new(name, new_mesh)
    bpy.context.collection.objects.link(new_obj)
    bm_new = bmesh.new()

    # Map from 2D points (rounded) to BMVert objects for grid vertices.
    vert_map: dict[tuple[float, float], bmesh.types.BMVert] = {}
    for pt in candidate_points:
        key = (round(pt.x, 10), round(pt.y, 10))
        if key not in vert_map:
            v = bm_new.verts.new((pt.x, pt.y, 0.0))
            vert_map[key] = v
    bm_new.verts.index_update()
    bm_new.verts.ensure_lookup_table()

    # Build a 2D index mapping grid coordinates (i,j) to BMVert
    grid_map: dict[tuple[int, int], bmesh.types.BMVert] = {}
    for pt in candidate_points:
        i = int(round((pt.x - start_x) / step))
        j = int(round((pt.y - start_y) / step))
        key = (round(pt.x, 10), round(pt.y, 10))
        grid_map[(i, j)] = vert_map[key]

    # Create horizontal and vertical edges for the interior grid.  Do not
    # generate faces yet; faces will be created by the edgenet_fill operator.
    all_edges: list[bmesh.types.BMEdge] = []
    # Horizontal edges
    for i in range(x_count):
        for j in range(y_count - 1):
            if (i, j) in grid_map and (i, j + 1) in grid_map:
                v0 = grid_map[(i, j)]
                v1 = grid_map[(i, j + 1)]
                e = bm_new.edges.get((v0, v1)) or bm_new.edges.new((v0, v1))
                all_edges.append(e)
    # Vertical edges
    for i in range(x_count - 1):
        for j in range(y_count):
            if (i, j) in grid_map and (i + 1, j) in grid_map:
                v0 = grid_map[(i, j)]
                v1 = grid_map[(i + 1, j)]
                e = bm_new.edges.get((v0, v1)) or bm_new.edges.new((v0, v1))
                all_edges.append(e)

    # Depending on use_extra_as_boundary flag, decide how to create boundary vertices.
    boundary_verts: list[bmesh.types.BMVert] = []
    extra_verts: list[bmesh.types.BMVert] = []
    if use_extra_as_boundary and extra_points:
        # Use the provided extra_points as the boundary vertices instead of the
        # original boundary.  These points should already be ordered along the
        # boundary.  We create verts for each and connect them sequentially.
        for p in extra_points:
            bv = bm_new.verts.new((p.x, p.y, 0.0))
            boundary_verts.append(bv)
        bm_new.verts.index_update()
        bm_new.verts.ensure_lookup_table()
        # Connect boundary verts sequentially to form the outer edge
        for idx in range(len(boundary_verts)):
            v0 = boundary_verts[idx]
            v1 = boundary_verts[(idx + 1) % len(boundary_verts)]
            e = bm_new.edges.get((v0, v1)) or bm_new.edges.new((v0, v1))
            all_edges.append(e)
        # No separate extra verts
    else:
        # Add original boundary vertices and connect them
        for p in boundary_points:
            bv = bm_new.verts.new((p.x, p.y, 0.0))
            boundary_verts.append(bv)
        bm_new.verts.index_update()
        bm_new.verts.ensure_lookup_table()
        for idx in range(len(boundary_verts)):
            v0 = boundary_verts[idx]
            v1 = boundary_verts[(idx + 1) % len(boundary_verts)]
            e = bm_new.edges.get((v0, v1)) or bm_new.edges.new((v0, v1))
            all_edges.append(e)
        # Extra points are treated as additional vertices inside the mesh (e.g. intersection points)
        if extra_points:
            for p in extra_points:
                ev = bm_new.verts.new((p.x, p.y, 0.0))
                extra_verts.append(ev)
            bm_new.verts.index_update()
            bm_new.verts.ensure_lookup_table()

    # Connect each boundary vertex and extra intersection vertex to the
    # single nearest interior grid vertex.  This minimizes stray internal
    # diagonals by avoiding connections to multiple grid vertices.
    def find_nearest_grid_vert(pt: Vector) -> bmesh.types.BMVert | None:
        """Find the interior grid vertex closest to a given point."""
        # Estimate grid coordinate using floor to choose an interior cell
        xi = int(math.floor((pt.x - start_x) / step))
        yi = int(math.floor((pt.y - start_y) / step))
        best = None
        best_dist_sq = None
        # Search a small neighbourhood around the estimated cell
        for ii in range(xi - 1, xi + 2):
            for jj in range(yi - 1, yi + 2):
                if (ii, jj) in grid_map:
                    gv = grid_map[(ii, jj)]
                    dx = gv.co.x - pt.x
                    dy = gv.co.y - pt.y
                    dist_sq = dx * dx + dy * dy
                    if best is None or dist_sq < best_dist_sq:
                        best = gv
                        best_dist_sq = dist_sq
        return best

    for bv in boundary_verts + extra_verts:
        pt2d = Vector((bv.co.x, bv.co.y))
        gv = find_nearest_grid_vert(pt2d)
        if gv is not None and bv != gv:
            e = bm_new.edges.get((bv, gv)) or bm_new.edges.new((bv, gv))
            all_edges.append(e)

    # Prepare and fill the edge network with faces.  This will generate faces
    # defined by the combined grid, boundary, and bridging edges.  The 'sides'
    # parameter specifies the maximum number of sides per face.  We use 4 to
    # favour quads when possible.
    bm_new.verts.index_update()
    bm_new.verts.ensure_lookup_table()
    bm_new.edges.index_update()
    bm_new.edges.ensure_lookup_table()
    # Edgenet prepare may add additional edges to close loops
    ret = bmesh.ops.edgenet_prepare(bm_new, edges=all_edges)
    # Include the newly created edges from the prepare step
    prepared_edges = ret.get("edges", [])
    if prepared_edges:
        all_edges.extend(prepared_edges)  # might not be necessary but safe
    bmesh.ops.edgenet_fill(bm_new, edges=all_edges, mat_nr=0, use_smooth=False, sides=4)

    # Finish and write to mesh
    bm_new.normal_update()
    bm_new.to_mesh(new_mesh)
    bm_new.free()
    return new_obj


def run(step: float = 0.001) -> None:
    """Main entry point for the grid creation.

    Select a mesh object, then run this function.  It will generate a new
    grid object in the current collection.

    Parameters
    ----------
    step : float, optional
        Spacing of the grid in world units (default 0.001).
    """
    obj = bpy.context.active_object
    if obj is None or obj.type != 'MESH':
        print("Please select a mesh object before running the script.")
        return
    # Ensure we have evaluated mesh data
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh_eval = obj_eval.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh_eval)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    # Extract boundary loop
    boundary = extract_boundary_loop(bm, obj)
    if not boundary:
        print("Unable to find a boundary loop on the selected mesh.")
        bm.free()
        return
    # Slice boundary edges at grid lines and obtain ordered intersection points
    slice_info = slice_boundary_at_grid(boundary, step)
    # Extract the intersection points in order along the boundary
    if slice_info:
        ordered_intersections = [item[0] for item in slice_info]
    else:
        ordered_intersections = []
    # Build grid mesh using the original boundary for interior test and the
    # intersection points for the outer boundary.  When use_extra_as_boundary
    # is true, the extra points define the boundary vertices.
    grid_obj = build_grid_mesh(boundary, step, obj.name + "_grid", extra_points=ordered_intersections, use_extra_as_boundary=bool(ordered_intersections))
    # Move the grid object so that it lies in the same plane as the source object
    # We assume the source mesh is planar; align the grid's Z coordinate to the
    # first vertex's world Z value
    if boundary:
        z_val = (obj.matrix_world @ bm.verts[0].co).z
        grid_obj.location.z = z_val
    bm.free()


# When running inside Blender's scripting environment, this block is executed.
if __name__ == "__main__":
    # Adjust the step value here if necessary
    STEP = 0.005
    run(STEP)
