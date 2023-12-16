# HAMPPSterS: Hybrid PC-HPC Automated Monitoring and Post-processing: Parametric Study Scheduler for Simulations

## Overview
HAMPPSterS is a Python-based repository designed to facilitate the orchestration of simulations in a hybrid environment, utilising both a local PC and a remote High-Performance Computing (HPC) system. This tool streamlines the simulation workflow, covering parametric run generation, job submission, monitoring, convergence checks, restarting, file conversion, and post-processing.

## Features
1. **Parametric Run Generation**
   - Utilises Design of Experiments (DOE) Latin Hypercube Sampling (LHS) to create a parametric run based on a defined sample space.

2. **Remote HPC Job Submission**
   - Sets up and submits simulation runs on a remote HPC system using the provided `job.sh` script.

3. **Job Monitoring and Convergence Checks**
   - Monitors the status of the HPC job during queuing and execution.
   - Executes scheduled convergence checks to ensure simulation progress.

4. **Automatic Job Restarting**
   - Verifies restarting conditions and re-submits the job accordingly.
   - Restarts the monitoring loop to ensure continuous progress.

5. **File Conversion**
   - Converts simulation files from VTK to VTR format upon job completion.

6. **Local Post-Processing**
   - Transfers final converted files to the local PC.
   - Executes post-processing operations using PvPython to obtain desired outputs.

## Getting Started
1. Clone the repository:
   ```bash
   git clone https://github.com/jpv219/HAMPPSterS.git
   cd HAMPPSterS_main
   
   ```bash
   pip install -r requirements.txt
