# -*- coding: utf-8 -*-
# benderconversions.py


"""Conversion between half steps and Newtons in XALOC benders

Conversion routines between half steps and Newtons in VFM and HFM XALOC mirrors
31.1.2011: ** ONLY LINEAL APPROXIMATION ** More accurate relations in a later stage

Created on Tue Jan 31 2012

@author: juanhuix
"""

import numpy as np
import math as m
from string import lower
from numpy import interp


def vfmbenb_conversion(request, force):
    """vfmbenb_conversion(request, force)
    Gives Conversion between force and half steps for vfm bender BACK
    mode = 'N' Converts hs->N
    mode = 'hs' Converts N->hs
    CURRENTLY 31.1.2012: vfmbenb(hs): 6305 - vfmstrnb.value: 153.5
    """
    slope = 121.765		 	# hsteps/N - JNicolas
    offset = 6305-slope*153.5 		#hs

    if request == 'hs':
	force_max = 300		        # lim max in N
	force_min = 0		        # lim min in N
	force_hs = slope*force + offset
	if force<force_min or force>force_max:
	    return(-1)
	return(force_hs)

    elif request == 'N':
	force_max = 1E6		        # lim max in hs
	force_min = -1E6	        # lim min in hs
	force_N = (force-offset)/slope
	if force<force_min or force>force_max:
	    return(-1)
	return(force_N)


def vfmbenf_conversion(request, force):
    """vfmbenf_conversion(request, force)
    Gives Conversion between force and half steps for vfm bender FRONT
    mode = 'N' Converts hs->N
    mode = 'hs' Converts N->hs
    CURRENTLY 31.1.2012: vfmbenf(hs): -2518 - vfmstrnf.value: 154.7
    """
    slope = 158.203		 	# hsteps/N - JNicolas
    offset = -2518-slope*154.7 		#hs

    if request == 'hs':
	force_max = 300		        # lim max in N
	force_min = 0		        # lim min in N
	force_hs = slope*force + offset
	if force<force_min or force>force_max:
	    return(-1)
	return(force_hs)

    elif request == 'N':
	force_max = 1E6		        # lim max in hs
	force_min = -1E6	        # lim min in hs
	force_N = (force-offset)/slope
	if force<force_min or force>force_max:
	    return(-1)
	return(force_N)

def hfmbenb_conversion(request, force):
    """hfmbenb_conversion(request, force)
    Gives Conversion between force and half steps for vfm bender BACK
    mode = 'N' Converts hs->N
    mode = 'hs' Converts N->hs
    CURRENTLY 13.2.2012: hfmbenb(hs): 40426 - hfmstrnb.value: 201.95
    """
    slope = 405.500		 	# hsteps/N - JNicolas
    offset = 40426-slope*201.95 		#hs

    if request == 'hs':
	force_max = 300	               	# lim max in N
	force_min = 0		        # lim min in N
	force_hs = slope*force + offset
	if force<force_min or force>force_max:
	    return(-1)
	return(force_hs)

    elif request == 'N':
	force_max = 1E6		        # lim max in hs
	force_min = -1E6	        # lim min in hs
	force_N = (force-offset)/slope
	if force<force_min or force>force_max:
	    return(-1)
	return(force_N)

def hfmbenf_conversion(request, force):
    """vfmbenf_conversion(request, force)
    Gives Conversion between force and half steps for vfm bender FRONT
    mode = 'N' Converts hs->N
    mode = 'hs' Converts N->hs
    CURRENTLY 13.2.2012: vfmbenf(hs): 42999 - vfmstrnf.value: 201.52
    """
    slope = 801.498		 	# hsteps/N - JNicolas
    offset = 42999-slope*201.52 		#hs

    if request == 'hs':
	force_max = 300		        # lim max in N
	force_min = 0		        # lim min in N
	force_hs = slope*force + offset
	if force<force_min or force>force_max:
	    return(-1)
	return(force_hs)

    elif request == 'N':
	force_max = 1E6		        # lim max in hs
	force_min = -1E6	        # lim min in hs
	force_N = (force-offset)/slope
	if force<force_min or force>force_max:
	    return(-1)
	return(force_N)


def vfmelipse_conversion(request, parb, parf):
    """vfmelipse_conversion(request, parb, parf)
    Gives Conversion between forces in N and elipse paramters for vfm
    request = 'Force' Converts Elipse parameters E2, E3 -> Forces [N]
    request = 'Elipse' Converts Forces [N] -> Elipse parameters E2, E3
    parb = FU OR E2
    parf = FD OR E3
    Elipse is described by h(x) = E2 x**2 + E3 x**3
    """
# U = Upstream   = Back (parb)
# D = Downstream = Front (parf)
    E20 = 1.9817931531E-5
    E2U = 5.3352884441E-7
    E2D = 6.8795635423E-7
    E30 = -1.0720120935E-5
    E3U = -9.5879551897E-7
    E3D = 1.2533444067E-6
    FU_NOM = 170.558
    FD_NOM = 130.277

    if request == 'Elipse':
	FU = parb
	FD = parf
	E2 = E20 + E2U*FU + E2D*FD
	E3 = E30 + E3U*FU + E3D*FD
	return(E2, E3)

    elif request == 'Force':
	E2 = parb
	E3 = parf
	FU = (E3-E30-E3D*E2/E2D+E3D*E20/E2D)/(E3U-E2U*E3D/E2D)
	FD = (E2-E20-E2U*FU)/E2D
	return(FU, FD)



def vfmoptic_conversion(request, par1, par2, incidenceangle, p):
    """vfmoptic_conversion(request, parb, parf)
    Gives Conversion between elipse parameters and optical paramters for vfm
    request = 'Optics' Converts Elipse parameters E2, E3 -> Optical parameters q, DE3
    request = 'Elipse' Converts Optical parameters q, DE3 -> Elipse parameters E2, E3
    par1 = q OR E2
    par2 = DE3 OR E3
    incidenceangle = incidence angle angle to vfm in mrad with respect to surface
    p = distance source to mirror in m
    Elipse is described by h(x) = E2 x**2 + E3 x**3
    """
# U = Upstream   = Back (parb)
# D = Downstream = Front (parf)
    import math as m
    alpha = m.pi/2. - incidenceangle/1000 

    if request == 'Elipse':
	q   = par1
	DE3 = par2
	E2 = (1./p + 1./q)*m.cos(alpha)/4.
	E3 = (1.+DE3)*(1./p/p - 1./q/q)*m.sin(2.*alpha)/16.
	return(E2, E3)

    elif request == 'Optics':
	E2 = par1
	E3 = par2 
	q = 1./(4.*E2/m.cos(alpha) - 1./p)
	DE3 = 16.*E3/m.sin(2*alpha)/(1./p/p-1./q/q) - 1.
	return(q, DE3)



def hfmelipse_conversion(request, parb, parf):
    """hfmelipse_conversion(request, parb, parf)
    Gives Conversion between forces in N and elipse paramters for hfm
    request = 'Force' Converts Elipse parameters E2, E3 -> Forces [N]
    request = 'Elipse' Converts Forces [N] -> Elipse parameters E2, E3
    parb = FU OR E2
    parf = FD OR E3
    Elipse is described by h(x) = E2 x**2 + E3 x**3
    """
    # U = Upstream   = Back (parb)
    # D = Downstream = Front (parf)
    E20 = -2.383657E-5
    E2U = 5.378920E-7
    E2D = 5.984089E-7
    E30 = -1.120740E-6
    E3U = -5.877415E-7
    E3D = 6.094811E-7
    FU_NOM = 278.4522
    FD_NOM = 231.8139

    if request == 'Elipse':
	FU = parb
	FD = parf
	E2 = E20 + E2U*FU + E2D*FD
	E3 = E30 + E3U*FU + E3D*FD
	return(E2, E3)

    elif request == 'Force':
	E2 = parb
	E3 = parf
	FU = (E3-E30-E3D*E2/E2D+E3D*E20/E2D)/(E3U-E2U*E3D/E2D)
	FD = (E2-E20-E2U*FU)/E2D
	return(FU, FD)



def hfmoptic_conversion(request, par1, par2, incidenceangle, p):
    """hfmoptic_conversion(request, parb, parf)
    Gives Conversion between elipse parameters and optical paramters for hfm
    request = 'Optics' Converts Elipse parameters E2, E3 -> Optical parameters q, DE3
    request = 'Elipse' Converts Optical parameters q, DE3 -> Elipse parameters E2, E3
    par1 = q OR E2
    par2 = DE3 OR E3
    incidenceangle = incidence angle angle to hfm in mrad with respect to surface
    p = distance source to mirror in m
    Elipse is described by h(x) = E2 x**2 + E3 x**3
    """
    # U = Upstream   = Back (parb)
    # D = Downstream = Front (parf)
    import math as m
    alpha = m.pi/2. - incidenceangle/1000 

    if request == 'Elipse':
	q   = par1
	DE3 = par2
	E2 = (1./p + 1./q)*m.cos(alpha)/4.
	E3 = (1.+DE3)*(1./p/p - 1./q/q)*m.sin(2.*alpha)/16.
	return(E2, E3)

    elif request == 'Optics':
	E2 = par1
	E3 = par2 
	q = 1./(4.*E2/m.cos(alpha) - 1./p)
	DE3 = 16.*E3/m.sin(2*alpha)/(1./p/p-1./q/q) - 1.
	return(q, DE3)


