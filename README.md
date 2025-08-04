# GridIt — Modular Grid Tools for Blender

**GridIt** is a modular Blender add-on designed to generate and manipulate clean, efficient grid-based geometry inside arbitrary 2D mesh boundaries. Built with expandability and performance in mind, GridIt aims to provide artists, engineers, and procedural designers with precise control over grid creation in both world and shape-based contexts.

> Designed and maintained by [Ethan Robins (Ether0p12348)](https://github.com/Ether0p12348).
> 
> **GridIt** was initially created for personal use and prototyping. Some features (_pretty much all of the mathematical stuff_) were rapidly developed with help from [ChatGPT (OpenAI)](https://chat.openai.com), and updates may be irregular. Thanks for checking it out!

---

## Installation

1. Download the latest `.zip` file from the [GitHub Releases](https://github.com/Ether0p12348/Blender_GridIt/releases).
2. In Blender, go to **Edit > Preferences > Add-ons**.
3. Click **Install…**, then select the downloaded `.zip`.
4. Enable **GridIt** from the list.
5. The panel will appear in the **3D Viewport > Sidebar (N-panel) > GridIt tab**.

---

## System Requirements

GridIt is lightweight, but high-density grids can become computationally expensive.

- Minimum: Blender 4.5+, 8 GB RAM
- Recommended: 16 GB RAM, modern CPU/GPU
- You can set your update channel or manually limit max settings in the Preferences.

---

## Grid by World

- Generates a uniform quad grid aligned to world-space intervals (default 5 mm).
- Fills the interior of any selected planar mesh, conforming to the boundary shape.
- Ensures clean, quad-dominant topology using BMesh operators.

### Usage
1. Select a **flat mesh object** (XY-plane preferred).
2. Open the **GridIt** panel.
3. Set the **grid spacing** (default is `0.1 m`).
4. Click **Generate Grid**.
5. A new object will be created with the suffix `_grid`.

### Example

<p>
  <img title="Original Shape" src="https://github.com/Ether0p12348/Blender_GridIt/blob/main/images/original.png" height="250">
  <img title="Generated Grid (0.005 m)" src="https://github.com/Ether0p12348/Blender_GridIt/blob/main/images/generated.png" height="250">
  <img title="Generated Close-up (0.005 m)" src="https://github.com/Ether0p12348/Blender_GridIt/blob/main/images/generated_closeup.png" height="250">
</p>

---

## Updates

GridIt supports automatic updates directly from GitHub. Updates will be downloaded and installed based on your selected release channel:

| Channel | Description | Access |
|---------|-------------|--------|
| `Stable` | Fully tested builds | Default |
| `Beta` | New features, less tested | Open |
| `Dev` | Experimental builds | Password-gated (future support) |

Release tags follow this pattern:
- `vX.Y.Z` → stable
- `vX.Y.Z-beta` → beta
- `vX.Y.Z-dev` → dev

**You may opt out of automatic updates at any time via the Add-on Preferences.**

When an update is installed, the add-on will automatically reload without requiring you to restart Blender — allowing you to continue your work uninterrupted.

---

## Contributing

Pull requests, ideas, and feedback are welcome! If you'd like to contribute tools or fixes, feel free to fork the project.

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](./LICENSE) file for details.
