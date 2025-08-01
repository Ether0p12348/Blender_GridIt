# Grid Mesh Generator for Blender (GridIt)

This repository contains a Python script for Blender that generates a regular grid inside a selected planar mesh, aligning the grid to world‑space intervals (default 5 mm) and conforming the boundary to the shape’s outline. The script creates a new object with a clean quad‑based interior and minimal triangulation along the perimeter.

## Features

* **Automatic grid generation** – Fills the interior of any selected planar mesh with a square grid at a specified spacing (default: `0.005` world units).
* **Boundary conformity** – Calculates intersections between the mesh outline and the grid lines, then uses these intersection points to approximate the boundary, avoiding heavy fragmentation from the original mesh vertices.
* **Clean topology** – Uses Blender’s BMesh operators (`edgenet_prepare` and `edgenet_fill`) to connect grid vertices and fill faces, resulting in a quad‑dominated mesh with triangles only where necessary along the boundary.
* **Custom spacing** – Adjust the `STEP` value in the script to change the grid density.

## Usage

1. Open your Blender project and select a planar mesh object. The mesh should be flat in the XY plane for best results.
2. In Blender’s **Text Editor**, load the file `blender_grid_script.py` from this repository.
3. At the bottom of the script, adjust the `STEP` value if you need a different spacing (the default is `0.005` units, or 5 mm).
4. Press **Run Script**. A new object will be created in your scene, suffixed with `_grid`, containing the generated grid mesh. The new object is placed on the same plane as the source mesh.

## How it Works

1. The script uses Blender’s BMesh API to extract the boundary loop of the selected object. Only the outer boundary is considered.
2. It computes the intersections of the boundary edges with vertical and horizontal grid lines spaced at the chosen increment. These intersection points become the new boundary vertices. Original boundary vertices are not used unless absolutely necessary, ensuring a clean outline.
3. Interior grid points are generated at every multiple of the spacing that lies inside the original shape using a point‑in‑polygon test. Each grid point becomes a vertex in the new mesh.
4. Boundary vertices are connected to the nearest interior grid point to form triangular “fans” along the perimeter. Horizontal and vertical grid edges are created between interior vertices to form a uniform grid.
5. BMesh operations `edgenet_prepare` and `edgenet_fill` are used to automatically create faces from the resulting edge network.

## Example

The images below show a transformation to a shape filled with a 5 mm (0.005 m) grid. Notice how the interior remains a uniform quad grid while the outer edge conforms to the original shape using intersections with the grid lines.

Original Shape (SVG converted to Mesh):<br>
![Original](https://github.com/Ether0p12348/Blender_GridIt/blob/main/original.png)

Generated:<br>
![Generated](https://github.com/Ether0p12348/Blender_GridIt/blob/main/generated.png)

Generated (Details):<br>
![Generated Close-up](https://github.com/Ether0p12348/Blender_GridIt/blob/main/generated_closeup.png)

## Credits

This script was created with the assistance of **ChatGPT**, an AI language model developed by OpenAI. Feel free to adapt or improve the script to suit your own workflows. If you find this tool useful, contributions and feedback are welcome!
