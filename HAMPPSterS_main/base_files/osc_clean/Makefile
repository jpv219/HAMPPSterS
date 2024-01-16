############################ -*- Mode: Makefile -*- ###########################
## Makefile ---
## 
## Copyright MMXIX
## All rights reserved
###############################################################################
include $(BLUE_HOME)/options/Make.inc

SHELL   = /bin/bash
CMD     = file.x
SRCS	= file.f90
OBJS	= file.o
NP	= 8

FCFLAGS = $(FFLAGS) -I. -I$(BLUEINC)
LIBS	= $(BLUELIB) 

.SUFFIXES: .f90 .o

all: $(CMD)

$(OBJS): $(BLUELIB)

.f90.o :
	$(FC) $(FCFLAGS) -c $<

$(CMD):	$(OBJS)
	$(FC) $(LDFLAGS) -o $(@) $(OBJS) $(LIBS)

exe : $(CMD)
	mpirun --use-hwthread-cpus -np $(NP) ./$(CMD)
	env DYLD_LIBRARY_PATH=/opt/local/vtk/lib vtk2xml.py -b -n *.vtk && rm -f *.vtk

clean:;	rm -f $(OBJS) *.mod core* $(CMD)

cleanall:; make clean; rm -f *.vtr *.vtk *.pvd *.rst *.stl *.csv *~
