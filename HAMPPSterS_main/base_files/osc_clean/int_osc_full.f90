!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! -*- Mode: F90 -*- !!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! prolate.f90 --- GFM Test 01t
!! Auteur          : Damir Juric (LIMSI-CNRS) <Damir.Juric@limsi.fr>
!! Cree le         : Tue Sep 22 09:37:35 2009
!! Dern. mod. par  : Jalel Chergui (LIMSI-CNRS) <Jalel.Chergui@limsi.fr>
!! Dern. mod. le   : Sun Apr  1 22:23:36 2012
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
module USER
  use BLUE

  implicit none
!   TANK PROPERTIES
  real(kind=d), parameter :: lq             = 7.0155d0          ! (m/s^2)
  real(kind=d), parameter :: eps            = 'epsilon_val'd0
  real(kind=d), parameter :: WNumber        = 'wave_num_val'd0
  real(kind=d), parameter :: a0             = eps / WNumber   
  public :: USER_sol, USER_int


  contains
!***********************************************************************
  function USER_sol(obj) result(distance)
!***********************************************************************
    implicit none

    ! Dummy
    type(obj_3d), intent(inout) :: obj
    real(kind=d)                :: distance

    ! Locals    
    real(kind=d)   :: x0, y0, z0

    type(cylinder)    :: PL
    real(kind=d)   :: p
   
    x0 = 0.5_d*(BOX(1)+BOX(2))
    y0 = 0.5_d*(BOX(3)+BOX(4))
    z0 = 0.05_d*(BOX(5)+BOX(6))
!
    PL = cylinder(BASEPOINT=[x0, y0, z0], ORIENTATION=[0.0_d, 0.0_d, 1.0_d], RADIUS = lq, INSIDE = FLUID)
    p  = PL%distance(obj%subobj(1)%form) 

    obj%subobj(1)%distance =p
    obj%subobj(1)%movement=movement_property(FORCED=.FALSE., STATIC=.TRUE.)
    distance = obj%subobj(1)%distance

!
  end function USER_sol

!***********************************************************************
  subroutine USER_int(ini)
!***********************************************************************
    implicit none

    type(ini_3d), intent(inout) :: ini
    real(kind=d) :: x0, xi, y0, yj, z0, zk, r
    integer      :: i, j, k
!
     x0 = 0.5_d*(BOX(1)+BOX(2))
     y0 = 0.5_d*(BOX(3)+BOX(4))
     z0 = 4.0d0 !0.5_d*(BOX(5)+BOX(6))

     !Be = BESSEL_JN(0,x0)

    ini%aux1(:,:,:)=ini%phi(:,:,:)
    do k=ini%msh%h%mem_kstart,ini%msh%h%mem_kend
       zk=ini%msh%h%z(k)-z0
    do j=ini%msh%h%mem_jstart,ini%msh%h%mem_jend
       yj=ini%msh%h%y(j)-y0
    do i=ini%msh%h%mem_istart,ini%msh%h%mem_iend
       xi=ini%msh%h%x(i)-x0
       r = sqrt(xi**2 + yj**2)
       ini%phi(i,j,k)= -zk + a0 * BESSEL_JN(0,r*WNumber)
    end do
    end do
    end do
!    call INE_sphere(INI=ini, CENTER=[x0,y0,height], RADIUS= Radius, VELOCITY=[0.0d0, 0.0d0, -0.00d0])
!    call INE_union(INI=ini)
     call INE_finalize(INI=ini)
  end subroutine USER_int
end module USER

program waves
  use USER

  implicit none

  type(com_3d)          :: com
  type(msh_3d)          :: msh
  type(eno_3d)          :: adv
  type(var_3d)          :: var
  type(gmres_mgmres_3d) :: solver
  type(BLUE_CLOCK)      :: clock
  integer               :: rfd
  integer               :: time_step_index, code

  ! Set MSH.
  call MSH_set(COM=com, MSH=msh)

  ! Set VAR.
  call VAR_set(COM=com, MSH=msh, VAR=var, USER_SOLID=USER_sol, USER_INTERFACE=USER_int)

  ! Set. ADV.
  call ADV_set(COM=com, MSH=msh, ADV=adv)

  ! Set solvers & operators
  call SOL_set(COM=com, MSH=msh, VAR=var, SOL=solver)

  ! Read restart file 
  call RST_read(COM=com, MSH=msh, ADV=adv, VAR=var, FD=rfd)

  ! Start time counter
  call CLOCK%start(LABEL="WAVES")

  TIMESTEP: do time_step_index = 1, NUM_TIME_STEP

    ! Solve Navier-Stokes equations.
     call BLUE_solve(COM=com, MSH=msh, ADV=adv, SOL=solver, VAR=var)

    ! Output results
    call IOF_output(COM=com, MSH=msh, VAR=var, SOL=solver)

    ! Write restart file.
    call RST_write(COM=com, MSH=msh, ADV=adv, VAR=var, FD=rfd)

    ! Exit from time loop if run time is reached
    if ( BLUE_MUST_QUIT ) exit TIMESTEP

  end do TIMESTEP

  ! Stop time counter
  call CLOCK%stop(LABEL="WAVES")

  ! Free datatype objects.
  call COM%free()
end program waves
