############################ -*- Mode: Makefile -*- ###########################
## Makefile ---
##
## Copyright MMXVI
## All rights reserved
###############################################################################
include ../../options/Make.inc

SHELL   = /bin/bash
CMD     = emu_test_layer.x
SRCS	= emu_test_layer.f90
OBJS	= emu_test_layer.o
NP	= 4

FCFLAGS = $(FFLAGS) -I. -I$(BLUEDIR)/$(BLUEINC)
LIBS	= $(BLUEDIR)/$(BLUELIB) 

.SUFFIXES: .f90 .o

all: $(CMD)

$(OBJS): $(BLUEDIR)/$(BLUELIB)

.f90.o : *.f90
	$(FC) $(FCFLAGS) -c $<

$(CMD):	$(OBJS)
	$(FC) $(LDFLAGS) -o $(@) $(OBJS) $(LIBS)

exe : $(CMD)
	mpirun -wd $(PWD) -np $(NP) ./$(CMD)
	DYLD_LIBRARY_PATH=/opt/local/vtk/lib vtk2xml.py -b -n *.vtk && rm -f *.vtk

#clean:;	rm -f $(OBJS) *.mod core* $(CMD)

#cleanall:; make clean; rm -f *.vt* *.pvd *.rst *.csv *~
