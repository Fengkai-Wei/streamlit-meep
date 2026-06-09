# MeepWeb: An Open-Source, Decoupled GUI Platform for the Meep Community

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/)
[![Framework: Streamlit](https://img.shields.io/badge/Framework-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Framework: FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)

**MeepWeb** is a modern, fully decoupled, cloud-ready graphical user interface (GUI) and simulation management platform built for the [**Meep (FDTD)**](https://github.com/NanoComp/meep). 

Unlike traditional, monolithic simulation scripts, MeepWeb separates the user interface, the backend orchestra, and the heavy physical solver into independent micro-layers. This architecture allows researchers and students to design complex 3D photonic structures (such as dielectric metasurfaces, qBIC cavities, and nano-arrays) in an intuitive web browser, while leveraging the raw power of high-performance computing (HPC) clusters or local servers seamlessly.

---

## 🏗️ Architecture Design

MeepWeb is structured around a **Stateless & Order-Preserving JSON Protocol**, ensuring complete decoupling between the UI and the solver:

```text
  [ Frontend GUI ]          [ Backend Orchestrator ]         [ HPC / Compute Node ]
 (Streamlit / OOP)              (FastAPI / Web)                (Meep / Slurm / H5)
         │                              │                               │
         │─── 1. Serializable JSON ────>│                               │
         │    (Order-Preserved Grid)    │─── 2. Dispatch Slurm Job ────>│
         │                              │    (Job Array / Multi-Core)   │
         │                              │                               │
         │                              │<── 3. Check & Sync Results ───│
         │<── 4. Render & Plot Slices ──│    (Lightweight Spectra JSON) │
         │    (On-Demand HDF5 Streaming)│    (Heavy Field Distribution) │
```

### Frontend (Streamlit):
Built using pure Object-Oriented Programming (OOP). All UI components (geometries, sces, monitors) are managed as high-level Python interactive classes inherited from a unified Serializable mixin.
### Orchestrator (FastAPI): 
Acts as the command center. It ingests the JSON payload, manages user accounts, communicates with HPC via SSH/SFTP, and schedules massive parallel parameter sweeps.
### Solver Layer (Meep):
Independent Python scripts executed on HPC compute nodes (e.g., managed by Slurm). It auto-parses the incoming JSON, executes parallel FDTD computations, dumps lightweight spectra to database-ready JSONs, and streams massive 3D DFT fields via localized HDF5 (`.h5`) slices.

## 🛠️ Tech Stack
### Frontend: 
Streamlit,  (Interactive 3D Preview), Requests.
### Backend Orchestrator:
FastAPI, Paramiko (SSH/SFTP), SQLite / PostgreSQL.
### Simulation Engine: 
Meep (Python API), NumPy, H5py (Lazy-loading HDF5 slicer), Slurm Workload Manager.

## 🗺️ Roadmap
My vision is to provide the global nanophotonics community with a free, cross-platform, and highly extensible alternative to commercial FDTD solutions.

### Phase 1: Foundation & Core Pipeline (Current Phase)
- [x] Standardize the Polymorphic JSON Protocol for geometric shapes, sources, and monitors.
- [x] Implement the Serializable class framework in the frontend to filter UI noise (_color, _opacity).
- [x] Design the auto-loop ingestion parser on the Meep computation side.
- [x] Establish order-preserving JSON Array sequence to match Meep's geometric stacking rules.

### Phase 2: HPC Integration & Infrastructure
- [ ] Implement the FastAPI SSH/SFTP task dispatcher with full Slurm support.
- [ ] Optimize Slurm Job Array scheduling for automated multi-dimensional parameter sweeps (e.g., radius vs. height scans for qBIC optimization).
- [ ] Establish the "Light/Heavy split" data storage policy: Spectra data goes to DB, while massive 3D fields stay in localized HDF5 disk blocks.
- [ ]  Build a background cron job to automatically purge expired heavy H5 files after 30 days to save server storage.

### Phase 3: Advanced Physics & Materials (Community Release Beta)
- [ ] Introduce a standardized dispersive Material Library supporting Lorentz-Drude models.
- [ ] Implement a refractiveindex.info API scraper integration to allow one-click material downloads.
- [ ]  Expand geometric models to support advanced meta-atoms (e.g., Cross Pillars, Elliptical Cylinders, Grating Slabs).
- [ ]   Support Near-to-Far field transformation (N2F) monitors for metasurface beam-shaping simulations.

### Phase 4: Full Ecosystem & Cloud Expansion
- [ ] Enable "Stateless Reproducibility" (One-click export/import of the design JSON configuration).
- [ ]  Wrap the entire backend compute layer into a lightweight Docker image for single-click local deployments.
- [ ]  Implement interactive 3D field slice visualization via [Plotly](https://github.com/plotly) on the Streamlit frontend with lazy-loaded HDF5 chunks.

##📝 Todo List (Immediate Sprints)
### Frontend (Streamlit)
- [ ] Implement st.session_state synchronization for dynamic lists (geoms, sources, monitors).
- [ ]  Add a to_dict() recursive loop trigger inside the main "Submit" button callback.
- [ ]  Design an interactive parameter grid generator sidebar for parameter sweeps.

### Backend (FastAPI)
- [ ] Setup endpoint /api/simulation/submit to handle heavy nested JSON validation.
- [ ] Create a basic Paramiko script to pipe .sh scripts onto the university's HPC cluster.
- [ ] Build a database schema to capture completed spectrum data from incoming JSONs.

### Computation (Meep Wrapper)
- [ ] Finalize the dictionary-based meep_monitors router inside run_simulation.py.
- [ ] Standardize the name-prefix rule (sim.dump_dft_fields(..., prefix=f"{name}_")) for multi-monitor H5 exports.
- [ ] Test order-preservation integrity under multi-layered geometric masking (e.g., Substrate vs. Pillar).

## 🤝 Contributing

Warmly welcome contributions from physicists, software engineers, and UI designers alike! Whether you want to add a new dispersion model, optimize the Slurm job pipeline, or improve the Streamlit UI, feel free to open an Issue or submit a Pull Request.
## 📄 License
This project is open-source and licensed under the MIT License. See the LICENSE file for more details.

Developed by Fengkai
