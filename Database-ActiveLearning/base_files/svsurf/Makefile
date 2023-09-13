############################ -*- Mode: Makefile -*- ###########################
## Makefile ---
##
## Copyright MMXVI
## All rights reserved
###############################################################################
include ../../options/Make.inc

SHELL   = /bin/bash
CMD     = emulsion.x
SRCS	= emulsion.f90
OBJS	= emulsion.o
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

clean:;	rm -f $(OBJS) *.mod core* $(CMD)

cleanall:; make clean; rm -f *.vt* *.pvd *.rst *.csv *~
