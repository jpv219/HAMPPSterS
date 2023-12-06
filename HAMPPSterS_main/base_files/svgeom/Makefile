############################ -*- Mode: Makefile -*- ###########################
## Makefile ---
## 
## Auteur          : Jalel Chergui (LIMSI-CNRS) <Jalel.Chergui@limsi.fr>
## Cr�� le         : Wed Mar  1 10:21:39 2006
## Dern. mod. par  : Jalel Chergui (LIMSI-CNRS) <Jalel.Chergui@limsi.fr>
## Dern. mod. le   : Wed Jan  4 13:36:20 2012
###############################################################################
include $(BLUE_HOME)/options/Make.inc

SHELL   = /bin/bash
CMD     = file.x
SRCS	= file.f90
OBJS	= file.o
NP	= 12 

FCFLAGS = $(FFLAGS) -I. -I$(BLUEINC)
LIBS	= $(BLUELIB) 

.SUFFIXES: .f90 .o

all: $(CMD)

$(OBJS): $(BLUELIB)

.f90.o : *.f90
	$(FC) $(FCFLAGS) -c $<

$(CMD):	$(OBJS)
	$(FC) $(LDFLAGS) -o $(@) $(OBJS) $(LIBS)

exe : $(CMD)
	mpirun --use-hwthread-cpus -wd $(PWD) -np $(NP) ./$(CMD)
	env DYLD_LIBRARY_PATH=/opt/local/vtk/lib vtk2xml.py -b -n *.vtk && rm -f *.vtk

clean:;	rm -f $(OBJS) *.mod core* $(CMD)

cleanall:; make clean; rm -f *.vt* *.pvd INT_*.stl *.rst *.csv *~
