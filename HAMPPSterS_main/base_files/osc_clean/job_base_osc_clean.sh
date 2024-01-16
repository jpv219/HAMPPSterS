#!/bin/bash
#PBS -N RUN_NAME
#PBS -o RUN_NAME.out
#PBS -j oe
#PBS -l select=1:ncpus=64:mem=100gb
#PBS -l walltime=08:00:00
set -vx
cd $PBS_O_WORKDIR

PROJECT="RUN_NAME"
PROGRAM=$PROJECT.x

# Build input data in Blue.nml file
cat > $PROJECT.nml <<'EOF'
&PROJECT
!--------------------------------------------------------------------------------------------------------------------------------
  project_name = "RUN_NAME"
!--------------------------------------------------------------------------------------------------------------------------------
/
&BOX_SIZE
!--------------------------------------------------------------------------------------------------------------------------------
! Size of the domain
  !   box(1), box(2)    box(3), box(4)    box(5), box(6)
  box=0.0d0,   14.031d0, 0.0d0,   14.031d0,  0.0d0,  14.031d0
!--------------------------------------------------------------------------------------------------------------------------------  
/
&MPI_PROCESS_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  ! Process grid dimensions (MPI will fix the process grid if profile=(0,0,0)).
  !         profile(1), profile(2), profile(3)
  profile = 4,          4,          4
  !
  ! Process grid Periodicity (true means periodic BCs.)
  !         periodic(1), periodic(2), periodic(3)  
  periodic= .FALSE., .FALSE., .FALSE.
!--------------------------------------------------------------------------------------------------------------------------------  
/
&MESH_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  ! Eulerian mesh size per subdomain (must be a power of two).
  !     cell(1), cell(2), cell(3)  
  cell= 64,      64,      64
  !
  ! Guardcell size (ENO needs at least one in each direction).
  !          guardcell(1), guardcell(2), guardcell(3)
  guardcell= 5,            5,            5
  !
  ! 1st/2d order accuracy of centred Dirichlet Boundary Conditions (select: 1 or 2).
  Dirichlet_bc_order=2 
!--------------------------------------------------------------------------------------------------------------------------------  
/
&TIME_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
! Number of time steps,                Real Time Limit (s),         run time limit in hours (if <0, run time has nolimit)
  num_time_step=2000000000                   real_time_limit=-1d0       run_time_limit=-1.0d0
!
! Fixed time step,                     If fixed, set dt.
  fixed_time_step=.FALSE.               dt=5.0D-5 
!
! Time integeration scheme ("GEAR" order(2) or "CRANK-NICHOLSON" order(2) or "EULER" order(1)).
  time_integration_scheme="GEAR"
!
  sl_interpolation_option = 0      ! Semi-Lagrangian interpolation option: 0:linear ; 1:fm3 ; 2:Peskin.
  sl_runge_kutta_order    = 1      ! Semi-Lagrangian Runge-Kutta order: 1 or 2.
!
! Time step factor multipliers
  cfl_time_step_factor    =0.1d0 
  visc_time_step_factor   =2.0d0  
  capi_time_step_factor   =2.0d0 
  int_time_step_factor    =0.04d0 
  cond_time_step_factor   =2.0d0 
  diff_time_step_factor   =2.0d0
  surf_time_step_factor   =2.0d0
  dfm_time_step_factor    =0.3d0        
  global_time_step_factor =0.98d0
!--------------------------------------------------------------------------------------------------------------------------------  
/
&SURFACE_TENSION_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  surface_tension                          =  'sigma_s_val'd0    ! Surface Tension (kg/s2).
  tangential_surface_force                 = .FALSE.       ! Contribution (True/False) of the tangiential surface force.
  !
  marangoni                                = .FALSE.      ! Marangoni approximation (on/off) => if true, set ENERGY_TRANSPORT=.true.
  marangoni_coeff                          =  0.0d0       ! Marangoni Coefficient (kg/s2/K).
  !
!--------------------------------------------------------------------------------------------------------------------------------
/
&FLUID_DENSITY_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  density_phase_1                          =  'rho_g_val'd0         ! Density of phase_1  (kg/m3)
  density_phase_2                          =  'rho_l_val'd0        ! Density of phase_2  (kg/m3)
  !
  boussinesq                               = .FALSE.       ! Boussinesq approximation (on/off) => if true, set ENERGY_TRANSPORT=.true.
  expan_phase_1                            = 1.0d-4        ! Expansion coeff. phase_1 (1/K)
  expan_phase_2                            = 1.0d-3        ! Expansion coeff. phase_2 (1/K)
  boussinesq_ref_temperature               = 294.0d0       ! Ambiant temperature (K).
!--------------------------------------------------------------------------------------------------------------------------------
/
&FLUID_VISCOSITY_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  viscosity_phase_1                        =  'mu_g_val'd0           ! Default absolute viscosity of phase_1 (kg/m/s).
  viscosity_phase_2                        =  'mu_l_val'd0        ! Default absolute viscosity of phase_2 (kg/m/s).
  harmonic_viscosity                       = .FALSE.            ! if true, compute harmonic approximation of the viscosity for multiphase flow.
  !
  Non_Newtonian                            = .FALSE.        ! if true, Non-Newtonian vicosity model is assumed instead of Newtonian above (default).
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
  gravity                                  =   0.0d0, 0.0d0, -'grav_val'd0     ! Gravity (x,y,z) (m/s2)
  Coriolis                                 =   .FALSE.                   ! Coriolis Force (true/false)
    coriolis_rotation_velocity             =   0.0d0                     ! Angular velocity (rad/s)
    coriolis_rotation_center               =   0.0d0, 0.0d0, 0.0d0       ! Center of rotation (x,y,z) (m)
    coriolis_exponential_method            =  .TRUE.                     ! Integration method: true=exponential, false=Adams-Bashforth
    coriolis_centripetal_force             =  .TRUE.                     ! Centripetal force. Always false if rotation_velocity=0
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
  subobj_number               = 1                          ! Number of immersed solid sub-objects.
  deformable                  = .FALSE.                    ! Set to true if one at least of the subobjs is deformable.
  ! If deformable, then:
      DFM_shear_modulus       = 1.0d5                      ! Shear modulus of the deformable solid.
      DFM_bctype              = "DDDDDD"                   ! Boundary Condition types.
      DFM_vol_cons            = 2                          ! Deformable Volume conservation (0:as previous, 1:as previous+heaviside, 2:as initial)
      DFM_vol_max_iter        = 50                         ! Used only if vol_cons=2 to get volume conserved.
      DFM_vol_tol             = 1.0d-5                     ! Used only if vol_cons=2 to get volume conserved.
      DFM_ho_max_iter         = 15                         ! Deformable High Order max number of iterations.
      DFM_dist_construct      = 0.0d0                      ! Deformable Moving distance for auto reconstruction.
      DFM_construct_frequency = 5 
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
  velocity_bctype                          = "DDDDDN", "DDDDDN", "DDDDDN"
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
  u_max_iter=60     u_tol=1.D-12      u_relax=1.25D0       u_max_comp=10
  v_max_iter=60     v_tol=1.D-12      v_relax=1.25D0       v_max_comp=10
  w_max_iter=60     w_tol=1.D-12      w_relax=1.25D0       w_max_comp=10
!--------------------------------------------------------------------------------------------------------------------------------
/
&PRESSURE_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  ! DEFAULT BOUNDARY CONDITIONS
  pressure_bctype                          = "NNNNND"      ! Default domain boundary conditions types
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
  p_max_iter=100    p_tol=1.D-10         p_relax=1.05D0     p_max_comp=20
  !
  ! Nb grids.       relax_max_grid       Nb max cycles     Nb sweeps down.    Nb sweeps down (used by MG only)
  p_grids =4        p_relax_max=1.1d0   p_max_cycles=50  p_sweeps_down=20  p_sweeps_up=40
!--------------------------------------------------------------------------------------------------------------------------------
/
&ENERGY_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  energy_transport                         = .FALSE.       ! Energy transport (true/false)
  cond_phase_1                             =    0.1339d0   ! Conductivity phase_1 (kg m/K/s3)
  cond_phase_2                             =    0.063d0    ! Conductivity phase_2 (kg m/K/s3)
  capa_phase_1                             = 1778.2d0      ! Specific heat capacity phase_1 (m2/K/s2) 
  capa_phase_2                             = 1047.0d0      ! Specific heat capacity phase_2 (m2/K/s2)
  !----------------------------
  ! PHASE CHANGE                                           ! Needs two-phase flow context.
  phase_change                             = .FALSE.       ! Phase change (true/false).
  latent_heat                              =   2.257d+6    ! Latent Heat (m2/s2).
  phase_coeff                              =   1.0d-3      ! phase coefficient for surface temperature  (kg/K/s/m2)
  micro_htc                                =   1.57d+7     ! Microlayer evaporation heat transfer coefficient (kg/K/s3)
  !----------------------------
  ! DEFAULT BOUNDARY CONDITIONS
  energy_bctype                            = "NNNNDD"      ! Default domain boundary condition types
  energy_iso_bctype                        = "D"           ! Immersed solid boundary condition type
  ! Faces: West          East           
           Ewest=0.0d0   Eeast=0.0d0                       ! Default Dirichlet West/East boundary conditions
  ! Faces: Front         Back
           Efront=0.0d0  Eback=0.0d0                       ! Default Dirichlet Front/Back boundary conditions
  ! Faces: South         North
           Esouth=0.0d0  Enorth=60.0d0                     ! Default Dirichlet South/North boundary conditions
  !
  solid_temperature=0.0d0                                  ! Default solid temperature (K). 
  !----------------------------
  ! SOLVER PARAMETERS
  ! Iterations.      Tolerance.        Relaxation.         Components (used by GMRES only).
   e_max_iter=60     e_tol=1.D-12      e_relax=1.25D0      e_max_comp=10
!--------------------------------------------------------------------------------------------------------------------------------
/
&SPECIES_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  species_transport                        = .FALSE.       ! Species transport (true/false)
  miscible                                 = .FALSE.       ! True if phases are miscible.  
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
  !
  solid_species_concentration=0.0d0                        ! Default solid species concentration.  	   
  !----------------------------
  ! SOLVER PARAMETERS
  ! Iterations.      Tolerance.       Relaxation.          Components (used by GMRES only).
  c_max_iter=60      c_tol=1.D-12     c_relax=1.125D0      c_max_comp=10
!--------------------------------------------------------------------------------------------------------------------------------
/
&INTERFACE_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  ! CONTACT LINE PARAMETERS
  wall_contact_line                        =  .FALSE.       ! Wall contact model (true/false)
  wall_correction                          =  .FALSE.      ! Put contact points back to solid surface (True/False).
  reced_angle                              =  44.0d0       ! Receding  angle (degrees)
  advan_angle                              = 77.0d0       ! Advancing angle (degrees)
  slip_length                              =   1.0d0       ! Slip length at the wall (factor of grid size)
  hide_extended_interface                  =  .FALSE.       ! Display (true/false) virtual interface if wall_contact is true.
  !----------------------------
  ! RUPTURE/COALLESCENCE PARAMETERS
  interface_coalescence                    = .TRUE.        ! True/False: Merging interface  
  dist_merge_1                             = 1.0d0         ! merging distance critiria between interface.
  dist_merge_2                             = 1.0d0         ! merging distance critiria between interface and wall.
  dist_extend                              = 1.0d0         ! length of extended surface.
  !----------------------------
  ! DEFAULT BOUNDARY CONDITIONS
  interface_bctype                         = "DDDDDN"      ! Default domain boundary condition types
  !----------------------------
  ! SOLVER PARAMETERS
  nptfac                                   = 1             ! factor multiplicity of array interface dimension.
  ho_max_iter                              = 15            ! HO max. number of iterations.
  vol_cons                                 = 2             ! Volume conservation (0:as previous, 1:as previous+heaviside, 2:as initial)
  vol_max_iter                             = 50            ! Used only if vol_cons=2 to get volume conserved.
  vol_tol                                  = 1.0d-5        ! Used only if vol_cons=2 to get volume conserved.
  heaviside_option                         = 0             ! 0: smoothing, 1: sweeping ; 2:tight
  int_num_subcycle                         = 1             ! Number of dt subcyles for interface advection  
  hvside_num_iter                          = 70            ! Number of heaviside smoothing sweeps
  int_adv_option                           = 3             ! Interface advection option (0:linear, 1:peskin, 2:fm3, 3:spline).
  int_curv_option                          = 1             ! Curvature option (0:hybrid, 1:compact, 2:original).
  add_element                              = .FALSE.       ! Element addition (true/false).
  add_element_coef                         = 1.0d0         ! Divide element edge when distance is > add_element_coef*min_grid_size.
  dist_construct                           = 0.1d0         ! Interface moving distance for auto reconstruction.
  construct_frequency                      = 0            ! reconstruction frequency of the interface.
!--------------------------------------------------------------------------------------------------------------------------------  
/
&SURFACTANT_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  surfactant_transport                     = .FALSE.        ! Surfactant transport (true/false)
  surf_phase_1                             =   1.0d-5    ! Mass diffusity phase_1 (m2/s)
  surf_phase_2                             =   1.0d-5    ! Mass diffusity phase_2 (m2/s)
  surf_adsorpt                             =   0.00d0     ! Adsorption coefficient
  surf_desorpt                             =   0.00d0    ! Desoprtion coefficient
  surf_Gm_inf                              =   1.0d0       ! Maximum packing concentration (infinite concentration)
  surf_Gm_ini                              =   0.5d0       ! Initial surface concentration
  surf_Gm_diff                             =   1.0d-3    ! Diffusion coefficient along interface
  surf_curv_option                         =   0           ! Surfactant curvature option (0:Langmuir, 1:Linear)
  surf_Ela_Num                             =   0.3d0       ! Elastic number (R*T*Gm_inf)
  surf_epsilon                             =   0.05d0       ! Minimum surfactant surface tension ratio (sigma_critical/sigma_clean)
  surf_frumkin_coeff                       =   0.0d0       ! Coefficient for Frumkin equation of state.  If 0 => Langmuir.
  !----------------------------
  surface_stress                             = .FALSE.        ! surface stress true/false
    surf_gm_ref                              =   9.0d0       ! reference surfactant concentration
    surf_shear_viscosity                     =   0.001d0     ! reference surface shear viscosity
    surf_dilatational_viscosity              =   0.0010      ! reference surface dilatational viscosity
  !----------------------------
    ! DEFAULT BOUNDARY CONDITIONS
  surfactant_bctype                        = "DDNDDD"      ! Default domain boundary condition types
  surfactant_iso_bctype                    = "D"           ! Immersed solid boundary condition type
  ! Faces: West          East
           Swest=0.0d0   Seast=0.0d0                       ! Default Dirichlet West/East boundary conditions
  ! Faces: Front         Back   
           Sfront=0.0d0  Sback=0.0d0                       ! Default Dirichlet Front/Back boundary conditions
  ! Faces: South         North  
           Ssouth=0.0d0  Snorth=0.0d0                      ! Default Dirichlet South/North boundary conditions
  !
  solid_surfactant_concentration=0.0d0                     ! Default solid surfactant concentration.  	   
  !----------------------------
  ! SOLVER PARAMETERS                      
  ! Iterations.      Tolerance.       Relaxation.          Components (used by GMRES only).
  s_max_iter=60      s_tol=1.D-12     s_relax=1.125D0      s_max_comp=10
!--------------------------------------------------------------------------------------------------------------------------------
/
&SUBSTRATE_SURFACTANT_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  substrate_surfactant_transport           = .FALSE.        ! Substrate transport (true/false)
  Cs_diff                                  =   0.01d0      ! Diffusion coefficient along substrate (Ds)
  Cs_inf                                   =   0.01d0      ! Maximum packing substrate Cs (infinite Cs)
  Cs_adsorpt                               =   1.0d0       ! adsorption coefficient of Cs <= C (k3)
  Cs_desorpt                               =   0.1d0       ! desorption coefficient of Cs => C (k4)
  Gm_Cs_adsorpt                            =   0.25d0       ! adsorption coefficient of Cs <= Gamma @contact line (k7)
  Gm_Cs_desorpt                            =   0.25d0       ! desorption coefficient of Cs => Gamma @contact line (k8)
  surf_slip_corr                           =   0.2d0       ! slip correction factor from sbstrate surfactant
!--------------------------------------------------------------------------------------------------------------------------------
/
&MICELLE_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------
  micelle_transport                        = .FALSE.        ! Micelle transport (true/false)
  micelle_phase_1                          =   0.0417d0    ! Mass diffusity phase_1 (m2/s)
  micelle_phase_2                          =   0.0417d0    ! Mass diffusity phase_2 (m2/s)
  micelle_number                           =   10.0d0      ! Number of micelle
  micelle_formation                        =   3.0d0       ! Formation rate of micelle
  micelle_breakup                          =   4.0d0       ! Breakup rate of micelle
  !----------------------------
  ! DEFAULT BOUNDARY CONDITIONS
  micelle_bctype                           = "NNNNNN"      ! Default domain boundary condition types
  micelle_iso_bctype                       = "D"           ! Immersed solid boundary condition type
  ! Faces: West          East
           Mwest=0.0d0   Meast=0.0d0                       ! Default Dirichlet West/East boundary conditions
  ! Faces: Front         Back   
           Mfront=0.0d0  Mback=0.0d0                       ! Default Dirichlet Front/Back boundary conditions
  ! Faces: Mouth         North  
           Msouth=0.0d0  Mnorth=0.0d0                      ! Default Dirichlet South/North boundary conditions
  !
  solid_micelle_concentration=0.0d0                        ! Default solid surfactant concentration.  	   
  !----------------------------
  ! SOLVER PARAMETERS                      
  ! Iterations.      Tolerance.       Relaxation.          Components (used by GMRES only).
  m_max_iter=60      m_tol=1.D-12     m_relax=1.125D0      m_max_comp=10
!--------------------------------------------------------------------------------------------------------------------------------
/
&OUTPUT_PROPERTIES
!--------------------------------------------------------------------------------------------------------------------------------  
! standard output,       Frequency.                Period (s)
  display=.TRUE.         display_frequency=1       display_period=0.0d0
!
! Output compression factors on I, J, K indices (allowed values 1, 2, 4, 8 applied to paraview and tecplot outputs).
  output_compression_factor=1, 1, 1
!
! Output box selection (for paraview and tecplot display. Could avoid heavy data output in massive parallel context).
  ! Box selection (true/false),      Selected box coordinates
  output_box_selection=.FALSE.       output_box_coordinates=0.0d0, 7.0155d0, 0.0d0, 14.031d0, 0.0d0, 7.0155d0
!
! ParaView,                    Format,                                Frequency,                            Period (s)
  paraview_output=.TRUE.      paraview_format="vtk"                  paraview_frequency=0                  paraview_period='delta_t_sn_val'd0
!                              Divergence,                            Static solids,                        Moving solids
                               store_velocity_divergence = .FALSE.    store_every_static_solid = .FALSE.    store_every_moving_solid = .FALSE.
!
! interface,                   Format (stl/raw),        Frequency,                 Period (s)
  interface_output=.FALSE.     interface_format="stl"   interface_frequency=200    interface_period=0.0d0
!
! history,                     Frequency,               Period (s)
  history_output=.TRUE.       history_frequency=1      history_period=0.0d0
                      !                       X,          Y,          Z
                      center_reference_point= 7.0155d0,      14.000d0,      7.0155d0        ! Center reference.
                      axis_reference_point  = 7.0155d0,      7.0155d0                    ! z-axis reference.
                      !                       Z1          Z2
                      axis_segment          = 7.0055d0,      7.0255d0                   ! z-segment reference.
!
! Time signal,                Number of points,         Frequency,             Period (s)
  signal_output=.FALSE.       num_signal_points=1       signal_frequency=1     signal_period=0.0d0
                                   !   X,       Y,       Z
                      signal_points=5.000D0, 5.000D0, 0.000D0,
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
! Particle tracking,           Number of particles,      Frequency,             Period
  particle_tracking=.FALSE.    number_of_particles=1     particle_frequency=1  particle_period=0.0d0
                                  !   X,       Y,       Z
       particle_initial_positions=0.012D0, 0.012D0, 0.012D0,
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
! Restart Output Frequency,      Output time interval (s)
  output_restart_frequency=0     output_restart_period='delta_t_sn_val'd0
!
! Restart (true/false),          Input File Index,           Initial restart file prefix     
  restart=.FALSE.                input_file_index=0          initial_restart_file_prefix="RUN_NAME"
!--------------------------------------------------------------------------------------------------------------------------------
/
EOF
#Create the project working directory
[ -d ~/../ephemeral/$PROJECT ] || mkdir -p ~/../ephemeral/$PROJECT
mv $PROJECT.nml ~/../ephemeral/$PROJECT/Blue.nml
cp $PROJECT.x ~/../ephemeral/$PROJECT
# [ -d ~/../ephemeral/$PROJECT/FILES ] || cp -r FILES ~/../ephemeral/$PROJECT/FILES
cd ~/../ephemeral/$PROJECT
# Run the program.
echo "... Run started @ $(date) ..."
module load  mpi/intel-2019.8.254 intel-suite/2020.2
#pbsexec -grace 55 mpiexec ./$PROGRAM ; OK=$?
#mpirun -np $NBPROC ./$PROGRAM ; OK=$?
mpiexec ./$PROGRAM ; OK=$?
echo "... Run finished @ $(date) with error code $OK ..."
