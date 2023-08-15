!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! -*- Mode: F90 -*- !!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! waves.f90 --- Moving object test
!! Auteur          : Damir Juric (LIMSI-CNRS) <Damir.Juric@limsi.fr>
!! Cree le         : Tue Sep 22 09:37:35 2009
!! Dern. mod. par  : Jalel Chergui (LIMSI-CNRS) <Jalel.Chergui@limsi.fr>
!! Dern. mod. le   : Sun Apr  1 22:23:36 2012
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
module USER
  use BLUE

  implicit none

  real(kind=d),       parameter :: Pipe_Radius        =   0.5d0*0.01575d0                ! (m)
!
  real(kind=d),	      parameter :: SMX_Position       =   0.004d0
  real(kind=d),	      parameter :: SMX_Bar_Width      =   0.00193d0              ! (m)
  real(kind=d),       parameter :: SMX_Bar_Thickness  =   0.00102d0              ! (m)
  real(kind=d),       parameter :: SMX_Space_Size     =   0.00193d0                ! (m)
  integer,	      parameter :: Number_of_Bars     =   8
  integer,            parameter :: Number_of_Elements =   1
!
  integer,            parameter :: Nb_Drops_per_Level =   6          !
  integer,            parameter :: Nb_Levels          =   2          ! 
!
  real(kind=d),dimension(Nb_Levels), parameter :: Drop_Radius =i [5.0d-4,3.0e-4]
  real(kind=d),	      parameter :: Flow_Rate =   9.07897d-6     ! (m^3/s)
  public ::  USER_solid, USER_init, USER_bcd, USER_int

  contains
!***********************************************************************
  function USER_solid(obj) result(distance)
!***********************************************************************
    implicit none

    ! Dummy
    type(obj_3d), intent(inout)  :: obj
    real(kind=d)                 :: distance
    ! Locals
    type(cylinder)   :: CYL1, CYL2, CYL3
    type(block)      :: BL0, BL1, BL2, BL3
    type(plane)      :: PL1, PL2, PL3
    real(kind=d)     :: c1, c2, c3, p1, p2, p3, p4, b0, b0_bis, b1, b2, b3, bsave1, bsave2, bsave3, SMX_OBJ1, SMX_OBJ2, SMX_OBJ, PIPE_OBJ
    real(kind=d)     :: x0, y0, z0
    integer          :: i, j
    x0 = 0.5d0*(BOX(1)+BOX(2))
    y0 = 0.5d0*(BOX(3)+BOX(4))
    z0 = 0.5d0*(BOX(5)+BOX(6))

     CYL1       = cylinder(BASEPOINT=[x0,y0,z0], ORIENTATION=[1.0_d, 0.0_d, 0.0_d], RADIUS=Pipe_Radius, INSIDE=FLUID)
     c1         = CYL1%distance(obj%subobj(1)%form)
     PIPE_OBJ  = c1
    x0 = BOX(1)  + SMX_Position
    y0 = 0.5d0*(BOX(3)+BOX(4)) - Pipe_Radius +  0.5d0*SMX_Bar_Width
    BL0 = block(EXTENT=[x0 - 0.5d0*SMX_Bar_Thickness, x0 + 0.5d0*SMX_Bar_Width, &
                         y0 - 0.5d0*SMX_Bar_Thickness, y0 + 0.5d0*SMX_Bar_Width, &
                         z0 - 3.0d0*Pipe_Radius, z0 + 3.0d0*Pipe_Radius],&
                 ORIENTATION=[0.0_d, BLUE_PI_VALUE/4.0d0, 0.0_d], INSIDE=SOLID)
    b0 = BL0%distance(obj%subobj(1)%form)

          PL2       = plane(BASEPOINT=[x0 , y0, z0], ORIENTATION=[-1.0_d, 0.0_d, 0.0_d])
          p2        = PL2%distance(obj%subobj(1)%form)
    b0     = intersection(p2,b0)
    b0_bis = b0
      do j = 0 , Number_of_Elements - 1


          PL2       = plane(BASEPOINT=[x0 + real(2*j, kind=d)* 2.0d0*Pipe_Radius , y0, z0], ORIENTATION=[-1.0_d, 0.0_d, 0.0_d])
          p2        = PL2%distance(obj%subobj(1)%form)

          PL3       = plane(BASEPOINT=[x0 + real(2*j, kind=d)* 2.0d0*Pipe_Radius + 2.0d0*Pipe_Radius, y0, z0], ORIENTATION=[1.0_d, 0.0_d, 0.0_d])
          p3        = PL3%distance(obj%subobj(1)%form)
      do i = 0 , Number_of_Bars - 1
            BL1 = block(EXTENT=[x0 +(- 0.5d0*SMX_Bar_Thickness + real(2*j, kind=d) * 2.0d0*Pipe_Radius) , &
                                x0 +( 0.5d0*SMX_Bar_Thickness + real(2*j, kind=d) * 2.0d0*Pipe_Radius ) , &
                                y0 + (real(i, kind=d)*SMX_Space_Size - 0.5d0*SMX_Bar_Width) ,&
                                y0 + (real(i, kind=d)*SMX_Space_Size + 0.5d0*SMX_Bar_Width) ,&
                                z0 - 3.0d0*Pipe_Radius, z0 + 3.0d0*Pipe_Radius],&
                 ORIENTATION=[((-1.0d0)**i)*BLUE_PI_VALUE/4.0d0*((-1.0d0**j) + 1)*0.5, ((-1.0d0)**i)*BLUE_PI_VALUE/4.0d0*(-(-1.0d0**j) + 1)*0.5, 0.0_d], INSIDE=SOLID)
            b1 = BL1%distance(obj%subobj(1)%form)
            bsave1 =intersection(union(b0,b1),p2)
            b0     = intersection(bsave1,p3)

            BL2 = block(EXTENT=[x0 + Pipe_Radius + real(2*j, kind=d) * 2.0d0*Pipe_Radius  - 0.5d0*SMX_Bar_Thickness, &
                                x0 + Pipe_Radius + real(2*j, kind=d) * 2.0d0*Pipe_Radius + 0.5d0*SMX_Bar_Thickness, &
                                y0 + real(i, kind=d)*SMX_Space_Size - 0.5d0*SMX_Bar_Width, &
                                y0 + real(i, kind=d)*SMX_Space_Size + 0.5d0*SMX_Bar_Width, &
                                z0 - 3.0d0*Pipe_Radius, z0 + 3.0d0*Pipe_Radius],&
                 ORIENTATION=[0.0d0, ((-1.0d0)**i)*BLUE_PI_VALUE/4.0d0, 0.0_d], INSIDE=SOLID)
            b2 = BL2%distance(obj%subobj(1)%form)
            bsave2 = intersection(union(b0,b2),p2)
            b0     = intersection(bsave2,p3)
            BL3 = block(EXTENT=[x0 - 0.5d0*SMX_Bar_Thickness + real(2*j+1, kind=d) * 2.0d0*Pipe_Radius, &
                                x0 + 0.5d0*SMX_Bar_Thickness + real(2*j+1, kind=d) * 2.0d0*Pipe_Radius, &
                                y0 + real(i, kind=d)*SMX_Space_Size - 0.5d0*SMX_Bar_Width, &
                                y0 + real(i, kind=d)*SMX_Space_Size + 0.5d0*SMX_Bar_Width, &
                                z0 - 3.0d0*Pipe_Radius, z0 + 3.0d0*Pipe_Radius],&
                 ORIENTATION=[0.0d0, ((-1.0d0)**i)*BLUE_PI_VALUE/4.0d0, 0.0_d], INSIDE=SOLID)
            b3 = BL3%distance(obj%subobj(1)%form)
            bsave3 = intersection(union(b0,b3),p2)
            b0     = intersection(bsave3,p3)
      end do
            SMX_OBJ1   = intersection(union(b0_bis,union(union(bsave1,bsave2),bsave3)),p3)
            b0_bis    = SMX_OBJ1
!
     end do
!
!
!
!
!
!
!
!
!
!
      z0 = 0.5d0*(BOX(5)+BOX(6)) - Pipe_Radius
      y0 = 0.5d0*(BOX(3)+BOX(4)) + 0.25d0* Pipe_Radius - SMX_Bar_Thickness
      do j = 0 , Number_of_Elements -2


          PL2       = plane(BASEPOINT=[x0 + real(2*j+1, kind=d)* 2.0d0*Pipe_Radius , y0, z0], ORIENTATION=[-1.0_d, 0.0_d, 0.0_d])
          p2        = PL2%distance(obj%subobj(1)%form)

          PL3       = plane(BASEPOINT=[x0 + real(2*j+1, kind=d)* 2.0d0*Pipe_Radius + 2.0d0*Pipe_Radius, y0, z0], ORIENTATION=[1.0_d, 0.0_d, 0.0_d])
          p3        = PL3%distance(obj%subobj(1)%form)
      do i = 0 , Number_of_Bars + 10
            BL1 = block(EXTENT=[x0 +(- 0.5d0*SMX_Bar_Thickness + real(2*j+1, kind=d) * 2.0d0*Pipe_Radius) , &
                                x0 +( 0.5d0*SMX_Bar_Thickness + real(2*j+1, kind=d) * 2.0d0*Pipe_Radius ) , &
                                y0 - 3.0d0*Pipe_Radius, y0 + 3.0d0*Pipe_Radius, &
                                z0 + (real(i, kind=d)*SMX_Space_Size - 0.5d0*SMX_Bar_Width) ,&
                                z0 + (real(i, kind=d)*SMX_Space_Size + 0.5d0*SMX_Bar_Width)], &
                 ORIENTATION=[((-1.0d0)**i)*BLUE_PI_VALUE/4.0d0*((-1.0d0**j) + 1)*0.5, 0.0d0, ((-1.0d0)**i)*BLUE_PI_VALUE/4.0d0*(-(-1.0d0**j) + 1)*0.5], INSIDE=SOLID)
            b1 = BL1%distance(obj%subobj(1)%form)
            bsave1 =intersection(union(b0,b1),p2)
            b0     = intersection(bsave1,p3)

            BL2 = block(EXTENT=[x0 + Pipe_Radius + real(2*j+1, kind=d) * 2.0d0*Pipe_Radius  - 0.5d0*SMX_Bar_Thickness, &
                                x0 + Pipe_Radius + real(2*j+1, kind=d) * 2.0d0*Pipe_Radius + 0.5d0*SMX_Bar_Thickness, &
                                y0 - 3.0d0*Pipe_Radius, y0 + 3.0d0*Pipe_Radius, &
                                z0 + real(i, kind=d)*SMX_Space_Size - 0.5d0*SMX_Bar_Width, &
                                z0 + real(i, kind=d)*SMX_Space_Size + 0.5d0*SMX_Bar_Width],&
                 ORIENTATION=[0.0d0, 0.0d0, ((-1.0d0)**i)*BLUE_PI_VALUE/4.0d0], INSIDE=SOLID)
            b2 = BL2%distance(obj%subobj(1)%form)
            bsave2 = intersection(union(b0,b2),p2)
            b0     = intersection(bsave2,p3)
            BL3 = block(EXTENT=[x0 - 0.5d0*SMX_Bar_Thickness + real(2*j+2, kind=d) * 2.0d0*Pipe_Radius, &
                                x0 + 0.5d0*SMX_Bar_Thickness + real(2*j+2, kind=d) * 2.0d0*Pipe_Radius, &
                                y0 - 3.0d0*Pipe_Radius, y0 + 3.0d0*Pipe_Radius, &
                                z0 + real(i, kind=d)*SMX_Space_Size - 0.5d0*SMX_Bar_Width, &
                                z0 + real(i, kind=d)*SMX_Space_Size + 0.5d0*SMX_Bar_Width],&
                 ORIENTATION=[0.0d0, 0.0d0, ((-1.0d0)**i)*BLUE_PI_VALUE/4.0d0], INSIDE=SOLID)
            b3 = BL3%distance(obj%subobj(1)%form)
            bsave3 = intersection(union(b0,b3),p2)
            b0     = intersection(bsave3,p3)
      end do
            SMX_OBJ2   = intersection(union(b0_bis,union(union(bsave1,bsave2),bsave3)),p3)
            b0_bis    = SMX_OBJ2
!
     end do

          PL3       = plane(BASEPOINT=[BOX(1) + SMX_Position + real(Number_of_Elements, kind=d)* 2.0d0*Pipe_Radius, y0, z0], ORIENTATION=[1.0_d, 0.0_d, 0.0_d])
          p3        = PL3%distance(obj%subobj(1)%form)



     SMX_OBJ= intersection(union(SMX_OBJ1,SMX_OBJ2),p3)

    distance  = union(PIPE_OBJ,SMX_OBJ)
!   distance  = intersection(-PIPE_OBJ,SMX_OBJ)
  end function USER_solid

!***********************************************************************
!***********************************************************************
  subroutine USER_int(ini)
!***********************************************************************
    implicit none

    type(ini_3d),  intent(inout) :: ini
!
    real(kind=d)     ::x0, y0, z0, Theta, Layer_space
    integer          :: i, j, k


    x0 = BOX(1) + SMX_Position - 2.5d0*Drop_Radius(1)
    y0 = 0.5_d*(BOX(3)+BOX(4))
    z0 = 0.5_d*(BOX(5)+BOX(6))
    Layer_space = x0 / Nb_Levels
!ini%msh%h%dz
      Theta     = 0.0_d
      call INE_sphere(INI=ini, CENTER = [x0 , &
                                         y0 + (0.75d0*Pipe_Radius )*sin(Theta)  , &
                                         z0 + (0.75d0*Pipe_Radius )*cos(Theta) ], &
                               RADIUS=Drop_Radius(1) )
      do i = 1 , Nb_Drops_per_Level
      Theta     = real(i, kind=d) * 2.0_d * BLUE_PI_VALUE / real(Nb_Drops_per_Level , kind=d)
      call INE_sphere(INI=ini, CENTER = [x0 ,	&
                                         y0 + (0.75d0*Pipe_Radius)*sin(Theta) , &
					 z0 + (0.75d0*Pipe_Radius)*cos(Theta)], &
		               RADIUS=Drop_Radius(1))
      call INE_union(INI=ini)
      end do
     
      do i = 1 , (Nb_Drops_per_Level)/2 
      Theta     =   BLUE_PI_VALUE /real(Nb_Drops_per_Level, kind=d) + real(i, kind=d) * 2.0_d * BLUE_PI_VALUE / real(Nb_Drops_per_Level/2 , kind=d)
      call INE_sphere(INI=ini, CENTER = [x0 ,   &
                                         y0 + (0.5d0*Pipe_Radius)*sin(Theta) , &
                                         z0 + (0.5d0*Pipe_Radius)*cos(Theta)], &
                               RADIUS=Drop_Radius(1) )
      call INE_union(INI=ini)
      end do

      do i = 1 , (Nb_Drops_per_Level)/4
      Theta     =  real(i, kind=d) * 2.0_d * BLUE_PI_VALUE / real(Nb_Drops_per_Level/4 , kind=d)
      call INE_sphere(INI=ini, CENTER = [x0 ,   &
                                         y0 + (0.25d0*Pipe_Radius)*sin(Theta) , &
                                         z0 + (0.25d0*Pipe_Radius)*cos(Theta)], &
                               RADIUS=Drop_Radius(1) )
      call INE_union(INI=ini)
      end do


     do k = 1 , Nb_Levels -1       
      do i = 1 , Nb_Drops_per_Level
      Theta     = real(i, kind=d) * 2.0_d * BLUE_PI_VALUE / real(Nb_Drops_per_Level , kind=d)
      call INE_sphere(INI=ini, CENTER = [x0 - real(k, kind=d) * Layer_space,   &
                                         y0 + (0.75d0*Pipe_Radius)*sin(Theta) , &
                                         z0 + (0.75d0*Pipe_Radius)*cos(Theta)], &
                               RADIUS=Drop_Radius(k+1) )
      call INE_union(INI=ini)
      end do

      do i = 1 , (Nb_Drops_per_Level)/2
      Theta     =   BLUE_PI_VALUE /real(Nb_Drops_per_Level, kind=d) + real(i, kind=d) * 2.0_d * BLUE_PI_VALUE / real(Nb_Drops_per_Level/2 , kind=d)
      call INE_sphere(INI=ini, CENTER = [x0 - real(k, kind=d) * Layer_space,   &
                                         y0 + (0.5d0*Pipe_Radius)*sin(Theta) , &
                                         z0 + (0.5d0*Pipe_Radius)*cos(Theta)], &
                               RADIUS=Drop_Radius(k+1) )
      call INE_union(INI=ini)
      end do

      do i = 1 , (Nb_Drops_per_Level)/4
      Theta     =  real(i, kind=d) * 2.0_d * BLUE_PI_VALUE / real(Nb_Drops_per_Level/4 , kind=d)
      call INE_sphere(INI=ini, CENTER = [x0 - real(k, kind=d) * Layer_space,   &
                                         y0 + (0.25d0*Pipe_Radius)*sin(Theta) , &
                                         z0 + (0.25d0*Pipe_Radius)*cos(Theta)], &
                               RADIUS=Drop_Radius(k+1) )
      call INE_union(INI=ini)
      end do

     end do

    call INE_finalize(INI=ini)
  end subroutine USER_int

!***********************************************************************

!***********************************************************************
  subroutine USER_init(com, msh, var)
!***********************************************************************
    implicit none

    class(com_3d), intent(in)   :: com
    type(msh_3d), intent(in)    :: msh
    type(var_3d), intent(inout) :: var

    ! Locals
    integer      :: i, j, k
    real(kind=d) :: Distance
        var%h%fn(:,:,:)= (surf_desorpt * surf_Gm_ini / (surf_adsorpt*( surf_Gm_inf -surf_Gm_ini )))*var%h%ohv(:,:,:) 
end subroutine USER_init
!***********************************************************************


!***********************************************************************
  subroutine USER_bcd(com, msh, var)
!***********************************************************************
    implicit none

    class(com_3d), intent(in)    :: com
    type(msh_3d),  intent(in)    :: msh
    type(var_3d),  intent(inout) :: var

    ! Locals
    integer      :: j, k
    real(kind=d) :: y0, z0, r, uav

    ! BC on WEST face
    if ( BLUE_WEST_SIDE ) then

      Uav = Flow_Rate/(BLUE_PI_VALUE*Pipe_Radius*Pipe_Radius) 

      y0=0.5d0*(BOX(3)+BOX(4))
      z0=0.5d0*(BOX(5)+BOX(6))

      do k=msh%u%mem_kstart+1,msh%u%mem_kend-1
        do j=msh%u%mem_jstart+1,msh%u%mem_jend-1

           if (var%p%obj%phi(msh%p%istart+1,j,k) >= 0.0_d) then

              r=sqrt((msh%p%y(j)-y0)**2+(msh%p%z(k)-z0)**2)
              if ( r <= Pipe_Radius ) then
                  var%u%bctype(msh%u%istart+1,j,k)="D"
                  var%v%bctype(msh%v%istart  ,j,k)="D"
                  var%w%bctype(msh%w%istart,  j,k)="D"
                  var%p%bctype(msh%p%istart,  j,k)="N"
                  var%u%west(j,k) = 2.0_d*Uav*(1.0_d-(r/Pipe_Radius)**2)
                  var%v%west(j,k) = 0.0_d
                  var%w%west(j,k) = 0.0_d
              end if

           end if

        enddo
      enddo

    end if

  end subroutine USER_bcd
!***********************************************************************
end module USER
program fibers_program
  use USER

  implicit none

  type(com_3d)        :: com
  type(msh_3d)        :: msh
  type(var_3d)        :: var
  type(eno_3d)        :: adv
  type(gmres_mgmres_3d) :: solver
  type(BLUE_CLOCK)    :: clock
  integer             :: fd
  integer             :: time_step_index, code

  ! Set MSH.
  call MSH_set(COM=com, MSH=msh)

  ! Set VAR.
  call VAR_set(COM=com, MSH=msh, VAR=var, USER_SOLID=USER_solid, USER_BC=USER_bcd, USER_INTERFACE=USER_int)
  call USER_init(COM=com, MSH=msh, VAR=var)
  ! Set. ADV.
  call ADV_set(COM=com, MSH=msh, ADV=adv)

  ! Set solvers & operators
  call SOL_set(COM=com, MSH=msh, VAR=var, SOL=solver)

  ! Read restart file
  call RST_read(COM=com, MSH=msh, ADV=adv, VAR=var, FD=fd)

  ! Start time counter
  call clock%start(LABEL="FIBERS")

  TIMESTEP: do time_step_index = 1, NUM_TIME_STEP

    ! Solve interface/momentum/energy/species/surfactant equations.
    call BLUE_solve(COM=com, MSH=msh, ADV=adv, SOL=solver, VAR=var)

    ! Output some infos on the screen.
    call IOF_output(COM=com, MSH=msh, VAR=var, SOL=solver)

    ! Write restart file.
    call RST_write(COM=com, MSH=msh, ADV=adv, VAR=var, FD=fd)

    ! Exit from time loop if run time is reached
    if ( BLUE_MUST_QUIT ) exit TIMESTEP

  end do TIMESTEP

  ! Stop time counter
  call clock%stop(LABEL="FIBERS")

  ! Finalize
  call COM%free()
end program fibers_program

