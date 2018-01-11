######################################################################################################
# 
# Macro to autocenter samples using the autofocus_cent macro. First version 20160830 (Roeland Boer)
#
######################################################################################################

import numpy
import math
import time
import PyTango
import itertools

from sardana.macroserver.macro import Macro, Type
import taurus
from bl13constants import OAV_BW_device_name
from bl13constants import OAV_device_name
from bl13constants import OAV_CENTER_X_PX
from bl13constants import omegay_focal_pos

#### These constants are calibrated at zoom 6
OAV_BW_ROWS = 670
IMAGEROWCORRDROP = 0.90
OMEGACORRECTION = 0.0 # degrees
ZOOM = 4
OMEGASPEED = 60
AVG_IMG_INT_FOCUS = [220, 230, 230, 232, 240, 245, 250, 250, 250, 250, 250, 250] # calibration to be done RB 20160915
COLMIN_ZOOM = [220, 230, 0, 150, 0, 245, 250, 250, 250, 250, 250, 250]
ROWMIN_ZOOM = [220, 230, 0, 150, 0, 245, 250, 250, 250, 250, 250, 250]
AUTOFOCUS_COL_STARTADJUST = 20 # columns substracted from sample start column in second autofocus
AUTOFOCUS_COL_WIDTH = 200 # number of images columsn used in 2nd autofocus

class autocentering(Macro):
    """Executes the autocentering macro. Based on an omega scan checking camera image and autofocus using the sampleoavy pseudo motor"""
    param_def = []

    result_def = []

    def run(self):
        starttime = time.time()
        self.oav = PyTango.DeviceProxy(OAV_BW_device_name)
        self.omega = PyTango.DeviceProxy('omega')
        self.omegax = PyTango.DeviceProxy('omegax')
        self.omegay = PyTango.DeviceProxy('omegay')
        self.zoom = PyTango.DeviceProxy('zoom')
        self.vars = taurus.Device('bl13/ct/variables')
        self.pixsize_mm = self.vars.oav_pixelsize_x / 1000.
        # set omegay to focal point
        self.omegay.write_attribute('Position',omegay_focal_pos)
        if not self.zoom.value == ZOOM: 
            self.zoom.write_attribute('value',ZOOM)
            while self.zoom.state() != PyTango.DevState.ON:
                time.sleep(0.5)
                
        self.debug('AVG_IMG_INT_FOCUS[ZOOM-1] %f' % AVG_IMG_INT_FOCUS[ZOOM-1])

        centcol = 0
        tries = 0
        maxtries = 7
        
        sampleInImage = False
        pixmargen = 100
        if numpy.mean(image[:,0])<AVG_IMG_INT_FOCUS[ZOOM-1]: # mean of first column of image at zoom 4 was 214 (pin at top row of image)
            while not sampleInImage and tries<maxtries:
                image = self.oav.Image
                (sampleInImage,hstartcol) = sample_in_oav_image(image)
                if sampleInImage:
                    reldist = -(self.vars.beamwidth/2)/1000 + (round(image.shape[1]/2)-hstartcol) * self.pixsize_mm
                    if reldist < (image.shape[1] * (-pixmargen + (self.pixsize_mm/2))):
                        self.debug('AUTOCENTERING INFO: stage 1, sample startcolumn %d, reldist %f' % (hstartcol,reldist) )
                        self.execMacro('mvr omegax %f' % reldist)
                else: tries = tries + 1

        redoscan = True
        while redoscan:
            redoscan = False
            (image1, image2, image3, curompos,omegadir) = self.omegacamerascan()
            if omegadir == 0: raise 'no sample detected'

            rightompos = curompos + OMEGACORRECTION * omegadir
            self.debug('Low correlation found at omega position %f, current position %f, corrected position %f' % \
                                        (curompos, self.omega.read_attribute('Position').value, rightompos))
            self.execMacro('mv omega %s' % rightompos)
        
            # find direction of focus movement from consecutive images of omegascan
            (dupix,udpix) = self.find_sample_ver_last_row(image2.T)
            sampcenternew = (dupix-udpix)/2
            (dupix,udpix) = self.find_sample_ver_last_row(image1.T)
            sampcenterprev = (dupix-udpix)/2
            sampleoavydir = omegadir * (  sampcenterprev - sampcenternew ) 
            self.info('AUTOCENTERING INFO: stage 2, samplepos ranges %f-%f, sampleoavydir %f' % (sampcenterprev, sampcenternew, sampleoavydir))        
            perpimg = self.oav.Image.T # oav vertical in first dimension, oav horizontal in 2nd dimension
            croppix = 0
            colstrow = croppix
            colendrow = perpimg.shape[1]-1-croppix
            centcol = self.find_sample_hor(perpimg,colstrow,colendrow)
            if math.fabs(sampcenternew - sampcenterprev) > 0.001:
                sampleoavydir = sampleoavydir / math.fabs( sampleoavydir )
                #self.execMacro('autofocus_cent %f %d %d ' % (sampleoavydir, centcol-AUTOFOCUS_COL_STARTADJUST, AUTOFOCUS_COL_WIDTH) )
                self.execMacro('autofocus_cent %f %d %d ' % (sampleoavydir, 0, perpimg.shape[1]) )
            else:
                self.execMacro('autofocus_cent 0 %d %d ' %  (0, perpimg.shape[1]) )

            centcol = 0
            tries = 0
            maxtries = 7
            #While there is sample/low intensity in the first column, move the pin in positive x
            while not centcol and tries<maxtries:
                perpimg = self.oav.Image.T # oav vertical in first dimension, oav horizontal in 2nd dimension
                croppix = 0
                colstrow = croppix
                colendrow = perpimg.shape[1]-1-croppix
                centcol = self.find_sample_hor(perpimg,colstrow,colendrow)
                reldist = -(self.vars.beamwidth/2)/1000 + (round(perpimg.shape[0]/2)-centcol) * self.pixsize_mm
                if reldist < (perpimg.shape[0] * self.pixsize_mm/2):
                    self.debug('AUTOCENTERING INFO: stage 3, sample startcolumn %d, reldist %f' % (centcol,reldist) )
                    self.execMacro('mvr omegax %f' % reldist)
                    time.sleep(0.1) # it seems the camera needs some time to get the new position through
                tries = tries + 1
                if centcol == 0: redoscan = True

        # if deltaomega>0 and sample moves up on the image -> sample is close to the camera then the center of rotation
        # if deltaomega>0 and sample goes down on the image -> sample is farther from the camera then the center of rotation
        # if deltaomega<0 and sample moves up on the image -> sample is farther from the camera then the center of rotation
        # if deltaomega<0 and sample goes down on the image -> sample is close to the camera then the center of rotation
        # for each image, find the row where the sample is by calculating correlation coeff between subsequent rows
        
        image = self.oav.Image.T
        (dupix, udpix) = self.find_sample_ver_last_row(image)
        irow2 = (dupix-udpix)/2
        sampleoavydir = -1.0 * ( irow2 -  ( image.shape[0] /2 ) )
        sampleoavydir = sampleoavydir / math.fabs( sampleoavydir )
        self.info('AUTOCENTERING INFO: stage 4, samplepos ranges %f-%f, sampleoavydir %f' % (dupix, udpix, sampleoavydir))

        #Two alternative approaches: 
        #First option: find the vertical position of tip of sample:
        irow = self.centerSampleVertically(centcol, 20)
        reldist = (self.vars.beamwidth/2)/1000 - (round(perpimg.shape[1]/2)-irow) * self.pixsize_mm
        self.info('mvr sampleoavz %f' % reldist)
        time.sleep(0.1)
        #self.execMacro('mvr sampleoavz %f' % reldist)
        #Second option: rotate omega and do a second autocentering
        #self.autofocus_cent_90deg()
        
        
        # Now check correlation of columns, over a narrow range of rows. 
        perpimg = self.oav.Image.T # oav vertical in first dimension, oav horizontal in 2nd dimension
        croppix = 0
        colstrow = croppix
        colendrow = perpimg.shape[1]-1-croppix
        centcol = self.find_sample_hor(perpimg,colstrow,colendrow)

        reldist = -(self.vars.beamwidth/2)/1000 + (round(perpimg.shape[0]/2)-centcol) * self.pixsize_mm
        self.info('found tip of loop at column %d, relative distance for omegax %f (pixsize_mm %f)' % (centcol,reldist,self.pixsize_mm))
        if reldist < (perpimg.shape[0] * self.pixsize_mm/2):
            self.execMacro('mvr omegax %f' % reldist)
            self.info('AUTOCENTERING INFO: stage 5, sample startcolumn %d, reldist %f' % (centcol,reldist))
        #self.zoom.write_attribute('value',12)
        self.debug('Time needed to run macro %f' % (time.time()-starttime) )

    def centerSampleVertically(self, centcol, ncolw):
        # Given the centcol, ie the first column looking from the left in oav where a intensity drop is 
        #  detected in the image, the sample is centered in the vertical direction based on the intensity
        #  drop in the vertical direction over that column, taking a maximum with of ncolw
        oavimage = self.oav.Image.T
        if centcol+ncolw > oavimage.shape[0]-1: ncolw = oavimage.shape[0]-1 - centcol
        irow = self.find_sample_ver(oavimage,centcol,ncolw, 0, oavimage.shape[1]-1)
        return irow
        
    def sample_in_oav_image(image):
        # Checks if there is a sample in the image. returns a boolean and the first column (starting 
        #   from the left when seen in oav) where the sample appears
        pass

    def omegacamerascan(self):
        # MOVE CONTINOUS to endpos from current position AND ACQUIRE, stop when focus get worse

        omegapos = self.omega.read_attribute('Position').value
        if omegapos > 0: 
            deltaomega = -180
            omegadir = -1
        else: 
            deltaomega = 180
            omegadir = 1
        final_omegapos = omegapos + deltaomega
        self.debug('Moving omega to value %f, omegadir %f' % (final_omegapos,omegadir))
        
        self.initomegaspeed = self.omega.read_attribute('Velocity').value
        
        self.omega.write_attribute('Velocity', OMEGASPEED)
       
        repeat = True
        foundsample = False
        while repeat and self.omegax.read_attribute('Position') > -3:
            self.omega.write_attribute('position', final_omegapos)
            previmage = self.oav.Image
            previmagelst = list(itertools.chain.from_iterable(previmage))
            nrlowrmsdsnaps = 0 # to find direction of sample with omega
            minomega = 0
            meanlst = []
            minmeanint = 1E12
            it = 0
            starttime = time.time()
            curposom = self.omega.read_attribute('Position').value
            while self.omega.read_attribute('State').value != PyTango.DevState.ON and nrlowrmsdsnaps < 2:
                self.checkPoint()
                curposomcalc = curposom + ( time.time()-starttime ) * OMEGASPEED * omegadir
                curposom = self.omega.read_attribute('Position').value
                newimage = self.oav.Image
                newimagelst = list(itertools.chain.from_iterable(newimage))
                rmsd = numpy.sqrt(numpy.mean(numpy.square(numpy.array(newimagelst)-numpy.array(previmagelst))))
                meanint = numpy.mean(newimage)
                self.debug( 'omega %f, rmsd %f, it %d mean %f, curposom %f, curposomcalc %f' % (curposom,rmsd,it, meanint, curposom, curposomcalc) )
                meanlst.append(meanint)
                if meanint<minmeanint: 
                    minmeanint = meanint
                    minomega = curposom
                #if meanint < AVG_IMG_INT_FOCUS[ZOOM-1]:
                #    self.omega.stop()
                #    repeat = False
                #    foundsample = True
                #    break
                if it > 2:
                    A = numpy.vstack([meanlst[it-3:it], numpy.ones(3)]).T
                    lgg, lgc = numpy.linalg.lstsq(A,[0,1,2])[0]
                    self.info('%s lgg %f lgc %f' % (str(meanlst[it-3:it]),lgg,lgc))
                    if lgg*omegadir > 0: # should always improve, slope is positive or negative depending on the direction
                        repeat = False
                        foundsample = True
                        self.omega.stop()
                        break
                #self.info('omega state %s' % self.omega.read_attribute('State').value)
                #if rmsd > 5: # an empirical value..
                #    if nrlowrmsdsnaps == 1:
                #        repeat = False
                #        self.omega.stop()
                #        foundsample = True
                #        break
                #    else: 
                #        nrlowrmsdsnaps = 1
                previmage = newimage
                it=it+1
            if not foundsample:
                self.info('No sample found, moving omegax in positive direction')
                self.execMacro('mvr omegax %f' %  (-0.5 * self.pixsize_mm * previmage.shape[1]) )
                omegadir = omegadir * -1 # revert direction
                final_omegapos = final_omegapos + (deltaomega * omegadir)
        
        if foundsample:
            lastimage = self.oav.Image
            #if it<3: minomega = omegapos
            self.info('Found lowest mean image value %f at omega position %f' % (minmeanint, minomega) )
        else: 
            omegadir = 0

        while self.omega.statusmoving:
            time.sleep(0.1)
            
        self.omega.write_attribute('Velocity', self.initomegaspeed)
            
        return previmage,newimage,lastimage, minomega, omegadir # to calculate the direction of movement of the sample using horizontal lines

    def find_sample_hor(self, image, colstrow, colendrow):
        #Returns the first column where a significant drop in intensity is detected
        firstcol = image[0]
        self.debug('firstcol %s' % str(firstcol))
        self.debug('firstcol mean %f' % numpy.mean(firstcol))
        if numpy.amin(firstcol) < COLMIN_ZOOM[ZOOM-1]: return 0 # there's something in the first column
        prevcolfull = image[1,:].tolist() # somehow, the first column always gave bad rmsd with second column, first column should always be skipped
        prevcol = prevcolfull[colstrow:colendrow]
        #lastcol = image[(imega.shape[0]-1),:].tolist()
        prevcrosscorrcoef = -1
        icol2 = 0
        for col in image.tolist():
            colred = col[colstrow:colendrow]
            colmin = numpy.amin(colred)
            if colmin < COLMIN_ZOOM[ZOOM-1]:
                self.debug('AUTOCENTERING INFO: column minimum %d' % colmin)
                break
            icol2 = icol2 + 1
        return icol2
        
    def find_sample_hor_corr(self, image, colstrow, colendrow):
        #Returns the first column where a significant drop in correlation is detected with the previous column
        firstcol = image[0]
        self.debug('firstcol %s' % str(firstcol))
        self.debug('firstcol mean %f' % numpy.mean(firstcol))
        if numpy.amin(firstcol) < COLMIN_ZOOM[ZOOM-1]: return 0 # there's something in the first column
        prevcolfull = image[1,:].tolist() # somehow, the first column always gave bad rmsd with second column, first column should always be skipped
        prevcol = prevcolfull[colstrow:colendrow]
        #lastcol = image[(imega.shape[0]-1),:].tolist()
        prevcrosscorrcoef = -1
        icol2 = 0
        for col in image.tolist():
            colred = col[colstrow:colendrow]
            self.debug('%f'%numpy.mean(numpy.square(numpy.array(prevcol)-numpy.array(colred))) )
            crossrmsd = numpy.sqrt(numpy.mean(numpy.square(numpy.array(prevcol)-numpy.array(colred))))
            self.debug('AUTOCENTERING INFO: find_sample_hor_corr, column %d column crossrmsd %f mean %f' % 
                        (icol2,crossrmsd,numpy.mean(colred)))
            if not math.isnan(crossrmsd):
                if crossrmsd > 5: # sample comes from low corr end of image..
                    break
            icol2 = icol2 + 1
            prevcol = colred
        return icol2
        
    def find_sample_ver(self, image, colstart, colwidth, rowstart, rowwidth):
        # find the limit rows (first and last) of the sample, within the square defined by colstart, colend etc. 
        # returns the average of the max and min row pixels within the square
        self.debug('AUTOCENTERING INFO: find_sample_ver, colstart %d, colwidth %d, rowstart %d, rowwidth %d' % (colstart,colwidth,rowstart,rowwidth))
        if image.shape[0] < image.shape[1]:
            self.warning('AUTOCENTERING WARNING: The oav image was inverted in find_sample_ver()')
            image = image.T
        # First select columns:
        if colstart+colwidth > image.shape[1]: 
            msg = str('AUTOCENTERING ERROR: image column numbers out of boundary in find_sample_ver (sum = %d)' % (colstart+colwidth))
            self.error(msg)
            raise Exception(msg)
        if rowstart+rowwidth > image.shape[0]: 
            msg = str('AUTOCENTERING ERROR: image row numbers out of boundary in find_sample_ver (sum = %d)' % (rowstart+rowwidth))
            self.error(msg)
            raise Exception(msg)
        imagecols= image[colstart:colstart+colwidth]
        icol = 0
        irow = 0
        irowmin = image.shape[1]
        irowmax = 0
        self.debug('AUTOCENTERING INFO: find_sample_ver, initial irowmin %d, irowmax %d' % (irowmin,irowmax))
        for cindex in range(len(imagecols)):
            rowred = imagecols[cindex][rowstart:rowstart+rowwidth]
            self.debug('AUTOCENTERING INFO: find_sample_ver, cindex %d' % cindex)
            for rindex in range(len(rowred)): # search for first pixel with intensity below cutoff starting from top
                #self.debug('AUTOCENTERING INFO: find_sample_ver, rowred[rindex] %d' % rowred[rindex])
                if rowred[rindex] < ROWMIN_ZOOM[ZOOM-1]:
                    if rindex < irowmin: 
                        irowmin = rindex
                        self.debug('AUTOCENTERING INFO: New upper boundary at %d' % irowmin)
                        rindex = len(rowred) + 1
            rowredinv = list(reversed(rowred))
            for rindex in range(len(rowredinv)): # search for first pixel with intensity below cutoff starting from bottom
                if rowredinv[rindex] < ROWMIN_ZOOM[ZOOM-1]:
                    if len(rowredinv) - 1 - rindex > irowmax: 
                        irowmax = len(rowredinv) - 1 - rindex
                        self.debug('AUTOCENTERING INFO: New lower boundary at %d' % irowmax)
                        rindex = len(rowredinv)+1
        self.debug('AUTOCENTERING INFO: final upper and lower boundaries: irowmax %d, irowmin %d' %(irowmax, irowmin))                
        """
            rowmin = numpy.amin(rowred)
            irowmin = numpy.argmin(rowred)
            if rowmin < ROWMIN_ZOOM[ZOOM-1]:
                if irowmin > numpy.argmin(rowred):
                    irowmin = numpy.argmin(rowred)
            icol2 = icol2 + 1
            #prevrow = rowred
        """
        return rowstart + (irowmin+irowmax)/2
        
    def find_sample_ver_last_row(self, image):
        """ Finds the lower and upper boundary of low intensity within the last row of the input image """
        Timg2_cc = image[image.shape[0]-1,:] #last column when viewwd in oav

        dupix = 0 #down to up limit where loop is found
        ipix = 0
        if Timg2_cc[0] > Timg2_cc[Timg2_cc.shape[0]-1]:
            prevpix = Timg2_cc[0] # needs to be calculated once, just take highest value from first and last pixel of column
        else : prevpix = Timg2_cc[Timg2_cc.shape[0]-1]
        for pix in Timg2_cc[1:].tolist():
            #self.info('%f' % pix)
            if pix<prevpix*0.8: #empirical value: actually depends on zoom and light brightness. TODO calibrate this
                dupix = ipix
                break
            ipix = ipix + 1
            prevpix = pix
        udpix = Timg2_cc.shape[0]-1 #down to up limit where loop is found
        ipix = 0
        for pix in Timg2_cc[1:].T.tolist():
            if pix<prevpix*0.8:
                uppix = ipix
                break
            ipix = ipix + 1
            prevpix = pix
        return dupix,udpix # upper and lower boundaries of the sample

    def autofocus_cent_90deg(self):    
        # now rotate omega to prepare for autofocus in seocond direction
        omegapos = self.omega.read_attribute('Position').value
        newomega = omegapos + 90.0
        while self.omega.read_attribute('State').value != PyTango.DevState.ON:
            time.sleep(0.2)
        self.info('omega state %s' % self.omega.read_attribute('State').value)
        time.sleep(0.2)
        self.execMacro('mv omega %f' % newomega)

        perpimg = self.oav.Image.T # oav vertical in first dimension, oav horizontal in 2nd dimension
        croppix = 0
        colstrow = croppix
        colendrow = perpimg.shape[1]-1-croppix
        centcol_new = self.find_sample_hor(perpimg,colstrow,colendrow)
        if centcol_new < centcol: centcol = centcol_new # in the different view after 90 degree rot of omega, the tip of the sample may be clearer in view, take the smallest value of the two views

        self.debug('AUTOCENTERING INFO: second autofocus_cent')
        self.execMacro('autofocus_cent %f %d %d' % (sampleoavydir, centcol-AUTOFOCUS_COL_STARTADJUST, AUTOFOCUS_COL_WIDTH) )
        
        
    def on_abort(self):
        self.info('AUTOCENTERING WARNING: on_abort running')
        if self.omega.statusmoving: self.omega.stop()
        if self.omegax.statusmoving: self.omegax.stop()
        while self.omega.statusmoving:
            time.sleep(0.1)

        self.omega.write_attribute('Velocity', self.initomegaspeed)
        tryit = 0
        maxtries = 10
