# Meep Web GUI

A world-class, web-based graphical user interface for **MEEP** (MIT Electromagnetic Equation Propagation), built with Python using **Streamlit** and **Plotly**.

This application provides an intuitive workspace to design, visualize, and analyze electromagnetic simulations in 3D without writing simulation scripts manually.

## 🚀 Features

### 1. 3D Scene Visualization
- Real-time 3D rendering of simulation setups using Plotly.
- Support for both **Mesh3D** and **Surface** rendering modes.
- Interactive camera controls and orthographic/perspective projection toggle.

### 2. Geometry Management
- Add and edit complex geometries: `Block`, `Sphere`, `Cylinder`, `Cone`, `Wedge`, and ~~`Prism`~~.
- Validation logic to ensure non-degenerate physical shapes.

### 3. Source Configuration
- Support for multiple source types:
    - **Gaussian Beam**: 3D envelope visualization with polarization and phase spiral rendering.
    - **Eigenmode Source**: Integrated solver settings, lattice definition, and k-vector visualization.
    - **Custom Sources**: Support for various time-domain functions (Gaussian, Continuous, Custom).
- Phase and amplitude heatmap visualization for surface/volume sources.

### 4. Results Analysis
- 3D Volume rendering of simulation results.
- Interactive field layer selection.

## 🛠️ Installation

1. Clone the repository to your local environment.
2. Install the required dependencies:
   ```bash
   pip install streamlit numpy pandas plotly scipy requests
   ```
3. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

## 📂 Project Structure
- `app.py`: Main entry point and UI layout.
- `geo_config.py`: Logic for geometry creation, visualization and validation.
- `src_config.py`: Logic for electromagnetic source definition and visualization.
- `mnt_config.py`: Logic for monitor creation, visualization and validation
- `geo_mesh3d.py` : Specialized 3D rendering engines for geometries.
- `utils.py`: UI helper components and state management.