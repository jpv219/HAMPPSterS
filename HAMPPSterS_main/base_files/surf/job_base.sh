#!/bin/bash
#PBS -N RUN_NAME
#PBS -o RUN_NAME.out
#PBS -j oe
#PBS -l select=1:ncpus=128:mem=256gb
#PBS -l walltime=8:00:00
set -vx
cd $PBS_O_WORKDIR

PROJECT="RUN_NAME"
PROGRAM=$PROJECT.x

# Build input data in Blue.nml file
cat > Blue.nml <<'EOF'
&BOX_SIZE
!--------------------------------------------------------------------------------------------------------------------------------
! Size of the domain
  !   box(1),    box(2)     box(3),    box(4)    box(5),     box(6)
  box=0.0d0   0.032d0   0.0d0  0.016d0   0.0d0  0.016d0
!--------------------------------------------------------------------------------------------------------------------------------  
/
&MPI_PROCESS_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  ! Process grid dimensions (MPI will do the job if profile=(0,0,0)).
  !         profile(1), profile(2), profile(3)
  profile = 8,          4,          4
  !
  ! Process grid Periodicity (true means periodic BCs.)
  !         periodic(1), periodic(2), periodic(3)
  periodic= .FALSE.,     .FALSE.,     .FALSE.
!--------------------------------------------------------------------------------------------------------------------------------  
/
&MESH_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
! Eulerian mesh size per subdomain (must be in power of two).
  !    cell(1), cell(2), cell(3)
  cell=64,      64,      64
!
! Guardcell size (ENO needs at least one in each direction).
  !         guardcell(1), guardcell(2), guardcell(3)
  guardcell=5,            5,            5

  ! Spacial 1st/2d order Dirichlet Boundary Conditions (select: 1 or 2).
  Dirichlet_bc_order=2
!--------------------------------------------------------------------------------------------------------------------------------  
/
&TIME_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
! Number of time steps,                Real Time Limit (s),         run time limit in hours (if <0, run time limit has nolimit)
  num_time_step=30000000                   real_time_limit=-1.0d0       run_time_limit=-1.0d0
!
! Fixed time step,                     If fixed, set dt.
  fixed_time_step=.TRUE.             dt=1.0D-4
!
! Time integeration scheme ("GEAR" order(2) or "CRANK-NICHOLSON" order(2) or "EULER" order(1) scheme).
  time_integration_scheme="GEAR"
  !
  sl_interpolation_option = 0      ! Semi-Lagrangian interpolation option: 0:linear ; 1:fm3 ; 2:Peskin ; 3:spline
  sl_runge_kutta_order    = 1      ! Semi-Lagrangian Runge-Kutta order: 1 or 2.
!
! Time step factor multipliers
  cfl_time_step_factor    =10.0d0
  visc_time_step_factor   =500.0d0 
  capi_time_step_factor   =10.0d0
  int_time_step_factor    =0.5d0
  cond_time_step_factor   =2.0d0
  diff_time_step_factor   =2.0d0
  surf_time_step_factor   =10.0d0
  global_time_step_factor =1.0d0
!--------------------------------------------------------------------------------------------------------------------------------  
/
&SURFACE_TENSION_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  surface_tension                          =  0.036d0      ! Surface Tension (kg/s2).
  !
  marangoni                                = .FALSE.       ! Marangoni approximation (on/off) => if true, set ENERGY_TRANSPORT=.true.
  marangoni_coeff                          = -3.6d-5       ! Marangoni Coefficient (kg/s2/K).    
!--------------------------------------------------------------------------------------------------------------------------------
/
&FLUID_DENSITY_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  density_phase_1                          =  1364.0d0     ! Density of phase_1  (kg/m3)
  density_phase_2                          =  960.0d0     ! Density of phase_2  (kg/m3)
  !
  boussinesq                               = .FALSE.       ! Boussinesq approximation (on/off) => if true, set ENERGY_TRANSPORT=.true.
  expan_phase_1                            = 1.0d-4        ! Expansion coeff. phase_1 (1/K)
  expan_phase_2                            = 1.0d-3        ! Expansion coeff. phase_2 (1/K)
  boussinesq_ref_temperature               = 294.0d0       ! Ambiant temperature (K).
!--------------------------------------------------------------------------------------------------------------------------------
/
&FLUID_VISCOSITY_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  viscosity_phase_1                        = 0.615d0        ! Default absolute viscosity of phase_1 (kg/m/s).
  viscosity_phase_2                        = 0.0984d0        ! Default absolute viscosity of phase_2 (kg/m/s).
  harmonic_viscosity                       = .FALSE.       ! if true, compute harmonic approximation of the viscosity for multiphase flow.
  !
  Non_Newtonian                            = .FALSE.       ! if true, Non-Newtonian vicosity model is assumed instead of Newtonian above (default).
  ! PHASE 1
  power_law_model_phase_1                  = 1             ! Power law model => 0:Ostwald ; 1:Carreau-Yasuda ; 2:Cross ; 3:Herschel-Bulkley
  power_law_index_phase_1                  = 0.31d0        ! model(0,1,2,3): Power law index for phase 1.
  consistency_phase_1                      = 10.0d0        ! model(0)      : Consistency coefficient for phase 1.
  min_viscosity_phase_1                    = 0.01d0        ! model(0,1,2)  : Viscosity at zero shear rate (Pa.s).
  max_viscosity_phase_1                    = 5.3d0         ! model(0,1)    : Viscosity at infinite shear rate of phase 1 (Pa.s).
  yield_stress_threshold_phase_1           = 0.001d0       ! model(3)      : Yield stress threshold for phase_1 (Pascal)
  critical_strain_rate_phase_1             = 0.01d0        ! model(3)      : Critical shear rate for phase_1 (1/s)
  first_power_law_transition_index_phase_1 = 2.0d0         ! model(1)      : Index of the first transtion between Newtonian and power law zone for phase 1.
  relaxation_time_phase_1                  = 28.5d0        ! model(1,2)    : Relaxation time of phase 1.
  ! PHASE 2
  power_law_model_phase_2                  = 1             ! Power law model => 0:Ostwald ; 1:Carreau-Yasuda ; 2:Cross ; 3:Herschel-Bulkley
  power_law_index_phase_2                  = 0.28d0        ! model(0,1,2,3): Power law index for phase 2.
  consistency_phase_2                      = 10.0d0        ! model(0)      : Consistency coefficient for phase 2.
  min_viscosity_phase_2                    = 0.01d0        ! model(0,1,2)  : Niscosity at zero shear rate of phase 2 (Pa.s).
  max_viscosity_phase_2                    = 10.0d0        ! model(0,1)    : Viscosity at infinite shear rate of phase 2 (Pa.s).
  yield_stress_threshold_phase_2           = 200.0d0       ! model(3)      : Yield stress threshold for phase_1 (Pascal)
  critical_strain_rate_phase_2             = 0.0001d0      ! model(3)      : Critical shear rate for phase_1 (1/s)
  first_power_law_transition_index_phase_2 = 2.0d0         ! model(1)      : Index of the first transtion between Newtonian and power law zone for phase 2.
  relaxation_time_phase_2                  = 21.8d0        ! model(1,2)    : Relaxation time of phase 2.
  !
  ! Temperature viscosity dependence, Arrhenius Law => set ENERGY_TRANSPORT=.TRUE.
  lowest_admissible_temperature            = 0.0d0         ! model(0,1,2,3): Lowest admissible temperature (K)
  !
  ! PHASE 1
  reference_temperature_phase_1            = 300.0d0       ! model(0,1,2,3): Reference temperature of phase_1 (K).
  activation_energy_ratio_phase_1          = 0.0d0         ! model(0,1,2,3): Ratio of the activation energy to the thermodynamic constant for phase 1.
  ! PHASE 2
  reference_temperature_phase_2            = 270.0d0       ! model(0,1,2,3): Reference temperature of phase_2 (K).
  activation_energy_ratio_phase_2          = 0.0d0         ! model(0,1,2,3): Ratio of the activation energy to the thermodynamic constant for phase 2.
!--------------------------------------------------------------------------------------------------------------------------------
/
&EXTERNAL_FORCE_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  gravity                                  =   -9.81d0, 0.0d0, 0.0d0  ! Gravity (x,y,z) (m/s2)
  omega                                    =   0.0d0                   ! Angular velocity (rad/s)
  rotcenter                                =   0.0d0, 0.0d0, 0.0d0     ! Center of rotation (x,y,z) (m)
  coriolis_exponential_method              =  .FALSE.       ! Coriolis integration method: true=exponential, false=Admas-Bashforth
  centripetal_force                        =  .FALSE.       ! Centripetal force (true/false) always false if omega=0
!--------------------------------------------------------------------------------------------------------------------------------
/
&TURBULENCE_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  turbulence                               = .FALSE.       ! If true, turbulence model is on.
  turbulence_model                         = 0             ! Choices => 0: Smagorinsky-Lilly ; 1: in-progress ; 2: in-progress.
  ! PHASE 1
  smagorinsky_filter_phase_1               = 0             ! model(0), phase 1 choices: 0 => (dx*dy*dz)**1/3 ; 1 => (dx**2+dy**2+dz**2)**1/2.
  smagorinsky_coeff_phase_1                = 0.1d0         ! model(0): phase 1 Smagorinsky coefficient in [0.1,0.3].
  ! PHASE 2
  smagorinsky_filter_phase_2               = 0             ! model(0), phase 2 choices: 0 => (dx*dy*dz)**1/3 ; 1 => (dx**2+dy**2+dz**2)**1/2.
  smagorinsky_coeff_phase_2                = 0.1d0         ! model(0): phase 2 Smagorinsky coefficient in [0.1,0.3].
!--------------------------------------------------------------------------------------------------------------------------------
/
&SOLID_OBJECT_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  subobj_number = 1                                        ! Number of immersed solid sub-objects.
  !
  ! collision (true/false),  Repulsion Coefficient
  collision = .FALSE.         repulsion_coefficient = 100.0d0 
!--------------------------------------------------------------------------------------------------------------------------------
/
&MOMENTUM_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  momentum_transport                     = .TRUE.
  !
  ! DEFAULT BOUNDARY CONDITIONS
  !                                            u,         v,        w
  velocity_bctype                          = "DNDDDD", "DNDDDD", "DNDDDD"
  adjust_velocity                          = .TRUE.        ! Adjust velocity on Neumann boundaries (true/false)
  ! Immersed solid boundary condition types
  !                                           u,   v,   w
  velocity_iso_bctype                      = "D", "D", "D"
  ! Faces: West          East
           Uwest =0.0d0  Ueast =0.0d0                      ! Default Dirichlet West/East boundary conditions
           Vwest =0.0d0  Veast =0.0d0
           Wwest =0.0d0  Weast =0.0d0
  ! Faces: Front         Back
           Ufront=0.0d0  Uback =0.0d0                      ! Default Dirichlet Front/Back boundary conditions
           Vfront=0.0d0  Vback =0.0d0
           Wfront=0.0d0  Wback =0.0d0
  ! Faces: South         North 
           Usouth=0.0d0  Unorth=0.0d0                      ! Default Dirichlet South/North boundary conditions
           Vsouth=0.0d0  Vnorth=0.0d0
           Wsouth=0.0d0  Wnorth=0.0d0
  !----------------------------
  ! SOLVER PARAMETERS
  ! Iterations.     Tolerance.        Relaxation.          Components (used by GMRES only).
  u_max_iter=50     u_tol=1.D-12      u_relax=1.25D0       u_max_comp=10
  v_max_iter=50     v_tol=1.D-12      v_relax=1.25D0       v_max_comp=10
  w_max_iter=50     w_tol=1.D-12      w_relax=1.25D0       w_max_comp=10
!--------------------------------------------------------------------------------------------------------------------------------
/
&PRESSURE_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  ! DEFAULT BOUNDARY CONDITIONS
  pressure_bctype                          = "NDNNNN"      ! Default domain boundary conditions types
  pressure_iso_bctype                      = "N"           ! Immersed solid boundary condition types
  ! Faces: West          East 
           Pwest=0.0d0   Peast=0.0d0                       ! Default Dirichlet West/East boundary conditions
  ! Faces: Front         Back
           Pfront=0.0d0  Pback=0.0d0                       ! Default Dirichlet Front/Back boundary conditions 
  ! Faces: South         North
           Psouth=0.0d0  Pnorth=0.0d0                      ! Default Dirichlet South/North boundary conditions
  !----------------------------
  ! SOLVER PARAMETERS
  ! Iterations.     Tolerance.          Relaxation.        components (used by GMRES only).
  p_max_iter=100    p_tol=1.0D-10         p_relax=1.05D0     p_max_comp=30
  !
  ! Nb grid.       relax_max_grid      Nn max cycles     Nb sweeps down.    Nb sweeps down (used by MG only)
  p_grids=5        p_relax_max=1.1d0  p_max_cycles=50   p_sweeps_down=20   p_sweeps_up=40
!--------------------------------------------------------------------------------------------------------------------------------
/
&ENERGY_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  energy_transport                         = .FALSE.       ! Energy transport (true/false)
  cond_phase_1                             =  0.6651d0     ! Conductivity phase_1 (kg m/K/s3)
  cond_phase_2                             =  0.025007d0   ! Conductivity phase_2 (kg m/K/s3)
  capa_phase_1                             = 4217.0d0      ! Specific heat capacity phase_1 (m2/K/s2) 
  capa_phase_2                             = 2044.0d0      ! Specific heat capacity phase_2 (m2/K/s2)
  !----------------------------
  ! PHASE CHANGE                                           ! Needs two-phase flow context.
  phase_change                             = .FALSE.       ! Phase change (true/false).
  latent_heat                              =   2.257d+6    ! Latent Heat (m2/s2).
  phase_coeff                              =   1.0d-3      ! phase coefficient for surface temperature  (kg/K/s/m2)
  micro_htc                                =   1.57d+7     ! Microlayer evaporation heat transfer coefficient (kg/K/s3)
  !----------------------------
  ! DEFAULT BOUNDARY CONDITIONS
  energy_bctype                            = "PPPPDD"      ! Default domain boundary condition types
  energy_iso_bctype                        = "D"           ! Immersed solid boundary condition type
  ! Faces: West          East           
           Ewest=0.0d0   Eeast=0.0d0                       ! Default Dirichlet West/East boundary conditions
  ! Faces: Front         Back
           Efront=0.0d0  Eback=0.0d0                       ! Default Dirichlet Front/Back boundary conditions
  ! Faces: South         North
           Esouth=0.0d0  Enorth=0.0d0                      ! Default Dirichlet South/North boundary conditions
  !
  solid_temperature=10.0d0                                  ! Default solid temperature (K). 
  !----------------------------
  ! SOLVER PARAMETERS
  ! Iterations.      Tolerance.        Relaxation.         Components (used by GMRES only).
   e_max_iter=60     e_tol=1.D-12      e_relax=1.25D0      e_max_comp=10
!--------------------------------------------------------------------------------------------------------------------------------
/
&SPECIES_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  species_transport                        = .FALSE.       ! Species transport (true/false)
  diff_phase_1                             =   2.1d-6      ! Mass diffusity phase_1 (m2/s)
  diff_phase_2                             =   1.687d-5    ! Mass diffusity phase_2 (m2/s) 
  !----------------------------
  ! DEFAULT BOUNDARY CONDITIONS
  species_bctype                           = "DDDDDD"      ! Default domain boundary condition types
  species_iso_bctype                       = "D"           ! Immersed solid boundary condition type
  ! Faces: West          East
           Cwest=1.0d0   Ceast=1.0d0                       ! Default Dirichlet West/East boundary conditions
  ! Faces: Front         Back
           Cfront=1.0d0  Cback=1.0d0                       ! Default Dirichlet Front/Back boundary conditions
  ! Faces: South         North
           Csouth=1.0d0  Cnorth=1.0d0                      ! Default Dirichlet South/North boundary conditions
  !----------------------------
  ! SOLVER PARAMETERS
  ! Iterations.      Tolerance.       Relaxation.          Components (used by GMRES only).
  c_max_iter=60      c_tol=1.D-12     c_relax=1.125D0      c_max_comp=10
!--------------------------------------------------------------------------------------------------------------------------------
/
&INTERFACE_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  ! CONTACT LINE PARAMETERS
  wall_contact                             =  .FALSE.       ! Wall contact model (true/false)
  reced_angle                              = 140.0d0       ! Receding  angle (degrees)
  advan_angle                              = 40.0d0       ! Advancing angle (degrees)
  slip_length                              =   1.0d0       ! Slip length at the wall (factor of grid size)
  display_virtual_interface                =  .FALSE.      ! Display (true/false) virtual interface if wall_contact is true.
  !----------------------------
  ! RUPTURE/COALLESCENCE PARAMETERS
  dist_merge_1                             = 0.5d0         ! merging distance critiria between interface.
  dist_merge_2                             = 0.5d0         ! merging distance critiria between interface and wall.
  dist_extend                              = 1.0d0         ! length of extended surface.
  !----------------------------
  ! DEFAULT BOUNDARY CONDITIONS
  interface_bctype                         = "NNNNNN"      ! Default domain boundary condition types
  !----------------------------
  ! SOLVER PARAMETERS
  nptfac                                   = 1             ! factor multiplicity of array interface dimension.
  ho_max_iter                              = 20            ! HO max. number of iterations.
  vol_cons                                 = 2             ! Volume conservation (0:as previous, 1:as previous+heaviside, 2:as initial)
  vol_max_iter                             = 50            ! Used only if vol_cons=2 to get volume conserved.
  vol_tol                                  = 1.0d-5        ! Used only if vol_cons=2 to get volume conserved.
  heaviside_option                         = 2             ! 
  int_num_subcycle                         = 1             ! Number of dt subcyles for interface advection
  hvside_num_iter                          = 70            ! Number of heaviside smoothing sweeps
  int_adv_option                           = 0             ! Interface advection option (0:linear, 1:peskin, 2:fm3, 3:spline).
  int_curv_option                          = 1             ! Curvature option (0:hybrid, 1:compact, 2:original).
  add_element                              = .FALSE.        ! Element addition (true/false).
  add_element_coef                         = 1.0d0         ! Divide element edge when distance is > add_element_coef*min_grid_size.
  dist_construct                           = 0.2d0         ! Interface moving distance for auto reconstruction.
  construct_frequency                      = 0            ! reconstruction frequency of the interface.
!--------------------------------------------------------------------------------------------------------------------------------  
/
&SURFACTANT_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  surfactant_transport                     = .TRUE.       ! Surfactant transport (true/false)
  surf_phase_1                             =   'diff1'd-20      ! Mass diffusity phase_1 (m2/s)
  surf_phase_2                             =   'diff2'd0    ! Mass diffusity phase_2 (m2/s)
  surf_adsorpt                             =   'ka'd0     ! Adsorption coefficient
  surf_desorpt                             =   'kd'd0    ! Desoprtion coefficient
  surf_Gm_inf                              =   'ginf'd0       ! Maximum packing concentration (infinite concentration)
  surf_Gm_ini                              =   'gini'd0       ! Initial surface concentration
  surf_Gm_diff                             =   'diffs'd0    ! Diffusion coefficient along interface
  surf_curv_option                         =   0           ! Surfactant curvature option (0:Langmuir, 1:Linear)
  surf_Ela_Num                             =   'beta'd0       ! Elastic number (R*T*Gm_inf)
  !----------------------------
  ! DEFAULT BOUNDARY CONDITIONS
  surfactant_bctype                        = "DDDDDD"      ! Default domain boundary condition types
  surfactant_iso_bctype                    = "D"           ! Immersed solid boundary condition type
  ! Faces: West          East
           Swest=1.0d0   Seast=1.0d0                       ! Default Dirichlet West/East boundary conditions
  ! Faces: Front         Back   
           Sfront=1.0d0  Sback=1.0d0                       ! Default Dirichlet Front/Back boundary conditions
  ! Faces: South         North  
           Ssouth=1.0d0  Snorth=1.0d0                      ! Default Dirichlet South/North boundary conditions
  !----------------------------
  ! SOLVER PARAMETERS                      
  ! Iterations.      Tolerance.       Relaxation.          Components (used by GMRES only).
  s_max_iter=60      s_tol=1.D-12     s_relax=1.125D0      s_max_comp=10
!--------------------------------------------------------------------------------------------------------------------------------
/
&OUTPUT_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
! Standard output         Loop Frequency.             Time interval (s)
  display=.TRUE.          display_frequency=1         display_time_interval=0.0025d0
!
! Output compression factors on I, J, K indices (allowed values 1, 2, 4, 8 applied to paraview and tecplot outputs).
  output_compression_factor=1, 1, 1
!
! Output box selection (for paraview and tecplot display. Could avoid heavy data output in massive parallel context).
  ! Box selection (true/false),      Selected box coordinates
  output_box_selection=.FALSE.       output_box_coordinates=0.0d0, 0.0d0, 0.0d0, 0.0d0, 0.0d0, 0.0d0
!
! If ParaView,               Format,                Loop Frequency,          Time interval (s),             Prefix.
  paraview_output=.TRUE.    paraview_format="vtk"   paraview_frequency=0    paraview_time_interval=5.0d-3   paraview_file_prefix="RUN_NAME"
!
! If tecplot,                Loop Frequency,        Time interval (s),        Prefix.
  tecplot_output=.FALSE.     tecplot_frequency=50  tecplot_time_interval=0.0d0   tecplot_file_prefix="RUN_NAME"
!
! If interface,              Format (raw/stl)         Loop Frequency,        Time interval (s),        Prefix.
  interface_output=.FALSE.    interface_format="stl"   interface_frequency=10   interface_time_interval=0.0d0    interface_file_prefix="RUN_NAME"
!
! If history,         Loop Frequency,        Time interval (s),        Prefix.
  history_output=.TRUE.     history_frequency=1   history_time_interval=0.0d0   history_file_prefix="RUN_NAME"
                      !                       X,          Y,          Z
                      center_reference_point= 0.064d0,      0.008d0,      0.008d0        ! Center reference.
                      axis_reference_point  = 0.0d0,      0.0d0                    ! z-axis reference.
                      !                       Z1          Z2
                      axis_segment          = -0.025d0,      0.01d0                   ! z-segment reference.
!
! If signal,          Number of points,      Loop Frequency,      Time interval (s),     Prefix,
  signal_output=.FALSE.     num_signal_points=1   signal_frequency=1  signal_time_interval=0.0d0 signal_file_prefix="RUN_NAME"
                                   !   X,       Y,       Z
                      signal_points=0.000D0, 0.000D0, 0.000D0,
                                    0.000D0, 0.000D0, 0.000D0,
                                    0.000D0, 0.000D0, 0.000D0,
                                    0.000D0, 0.000D0, 0.000D0,
                                    0.000D0, 0.000D0, 0.000D0,
                                    0.000D0, 0.000D0, 0.000D0,
                                    0.000D0, 0.000D0, 0.000D0,
                                    0.000D0, 0.000D0, 0.000D0,
                                    0.000D0, 0.000D0, 0.000D0,
                                    0.000D0, 0.000D0, 0.000D0
!
! If shape,           Number of points,      Frequency,             Prefix,
  shape_output=.FALSE.      num_shape_points=1    shape_frequency=1  shape_time_interval=0.0d0   shape_file_prefix="RUN_NAME"
                                  !   X,       Y,       Z
                      shape_points=0.000D0, 0.000D0, 0.000D0,
                                   0.000D0, 0.000D0, 0.000D0,
                                   0.000D0, 0.000D0, 0.000D0,
                                   0.000D0, 0.000D0, 0.000D0,
                                   0.000D0, 0.000D0, 0.000D0,
                                   0.000D0, 0.000D0, 0.000D0,
                                   0.000D0, 0.000D0, 0.000D0,
                                   0.000D0, 0.000D0, 0.000D0,
                                   0.000D0, 0.000D0, 0.000D0,
                                   0.000D0, 0.000D0, 0.000D0
!
! Restart Output Frequency,   Output time interval (s)      Output File Prefix.
  output_restart_frequency=0     output_restart_time_interval=1.0d-3     output_restart_file_prefix="RUN_NAME"
!
! Restart (true/false),        Input File Index,        Input File Prefix.
  restart=.FALSE.              input_file_index=0       input_file_prefix="RUN_NAME"
!--------------------------------------------------------------------------------------------------------------------------------  
/
EOF
#Create the project working directory
[ -d ~/../ephemeral/$PROJECT ] || mkdir -p ~/../ephemeral/$PROJECT
cp Blue.nml ~/../ephemeral/$PROJECT
cp $PROJECT.x ~/../ephemeral/$PROJECT
cp $PROJECT.csv ~/../ephemeral/$PROJECT
# [ -d ~/../ephemeral/$PROJECT/FILES ] || cp -r FILES ~/../ephemeral/$PROJECT/FILES
cd ~/../ephemeral/$PROJECT
# Run the program.
echo "... Run started @ $(date) ..."
module load mpi/intel-2019.6.166 intel-suite/2019.4
#pbsexec -grace 55 mpiexec ./$PROGRAM ; OK=$?
#mpirun -np $NBPROC ./$PROGRAM ; OK=$?
mpiexec ./$PROGRAM ; OK=$?
cp $PROJECT.csv  $PBS_O_WORKDIR
echo "... Run finished @ $(date) with error code $OK ..."
