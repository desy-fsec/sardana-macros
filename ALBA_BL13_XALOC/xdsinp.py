from sardana.macroserver.macro import Macro, Type
import taurus
from datetime import *
import math
import os

class xdsinp(Macro):
    '''
      Creates XDS.INP file from current data collection values  
    '''
    param_def = [ [ 'prefix', Type.String, None, 'Filename prefix'],
                  [ 'run', Type.Integer, None, 'Run number'],
                  [ 'ni', Type.Integer, None, 'Number of images'],
                  [ 'startangle', Type.Float, None, 'Oscillation start'],
                  [ 'angleincrement', Type.Float, None, 'Oscillation range'],
                  [ 'expt', Type.Float, None, 'Exposure time'],
                  [ 'startnum', Type.Integer, 1, 'Start number'],
                  [ 'dir', Type.String, "/beamlines/bl13/commissioning/tmp/", 'Directory to write the XDS.INP file']
                ]
    def run(self, prefix, run, ni, startangle, angleincrement, expt, startnum, dir):
        # PREPARE DEVICES
        xdsdir='/beamlines/bl13/commissioning/templates/'
        var = taurus.Device('bl13/ct/variables')
        t = datetime.now()



        # CREATE DIRECTORIES
        processdir = os.path.join(dir,"process",prefix + "_" + str(run))
#        processdir=dir+"process/"+prefix+"_"+str(run)
        dirprocess = os.path.join(dir,"process")
#        dirprocess = dir+"process/"
        if not os.path.exists(dirprocess):
          try: os.makedirs(dirprocess)
          except: 
             msg = 'XDSINP ERROR: Could not create root directory %s' % dirprocess
             self.error(msg)
             raise Exception(msg)
        elif os.path.isfile(dirprocess): 
          msg = 'XDSINP ERROR: The destination process directory %s exists as a file, cant overwrite as a directory' % dirprocess
          self.error(msg)
          raise Exception(msg)
        if not os.path.exists(processdir):
          try: os.makedirs(processdir)
          except: 
             msg = 'XDSINP ERROR: Could not create process directory %s' % processdir
             self.error(msg)
             raise Exception(msg)

        # PREPARE VARIABLES
        beamx, beamy = var['beamx'].value, var['beamy'].value
        mbeamx, mbeamy = beamy*0.172, beamx*0.172 
        detsamdis = var['detsamdis'].value
        wavelength= round(self.getMoveable("wavelength").getPosition(),6)
        datarangestartnum = startnum 
        datarangefinishnum = startnum+ni-1
        backgroundrangestartnum = startnum 
        spotrangestartnum = startnum
        if angleincrement != 0: 
            minimumrange = int(round(20/angleincrement))
        elif angleincrement == 0:
            minimumrange = 1
        if ni >= minimumrange: backgroundrangefinishnum = startnum+minimumrange-1
        if ni >= minimumrange: spotrangefinishnum = startnum+minimumrange-1
        if ni < minimumrange: backgroundrangefinishnum = startnum+ni-1
        if ni < minimumrange: spotrangefinishnum = startnum+ni-1
        testlowres = 8.
        largestvector=0.172*((max(beamx,2463-beamx))**2+(max(beamy,2527-beamy))**2)**0.5
        testhighres = round(wavelength/(2*math.sin(0.5*math.atan(largestvector/detsamdis))),2)
        lowres = 50.
        highres = testhighres
        datafilename=prefix+'_'+str(run)+'_????'
        mdatafilename=prefix+'_'+str(run)+'_####.cbf'
        seconds = 5*expt
        if angleincrement < 1 and not angleincrement == 0: seconds = 5*expt/angleincrement
        reldir = '../../'


        # DEFINE SG/UNIT CELL
        spacegroupnumber=''
        unitcellconstants=''

        # SPECIAL CASE FOR LYSOZYME
        #if "lyso" in prefix:
        #   spacegroupnumber= ' SPACE_GROUP_NUMBER=96'
        #   unitcellconstants= ' UNIT_CELL_CONSTANTS= 78.7499   78.7499   36.8602   90.0000   90.0000   90.0000'



        # CREATE XDS.INP FILE
        name="XDS_TEMPLATE.INP"
        cfilename = xdsdir+name
        f = open(cfilename,"r")
        lines=f.readlines()
        f.close()
        name="XDS.INP"
        nfilename = processdir+"/"+name
        #self.info(nfilename)
        nf = open(nfilename,"w")
        #self.info('final')
        for line in lines:
            line = line.replace( '###BEAMX###',str(round(beamx,2)))
            line = line.replace( "###BEAMY###", str(round(beamy,2)))
            line = line.replace( "###DETSAMDIS###", str(round(detsamdis,2)))
            line = line.replace( "###ANGLEINCREMENT###", str(angleincrement))
            line = line.replace( "###WAVELENGTH###", str(wavelength) )
            line = line.replace( "###DATARANGESTARTNUM###",str(datarangestartnum))
            line = line.replace( "###DATARANGEFINISHNUM###",str(datarangefinishnum))
            line = line.replace( "###BACKGROUNDRANGESTART###", str(backgroundrangestartnum) )
            line = line.replace( "###BACKGROUNDRANGEFINISHNUM###", str(backgroundrangefinishnum) )
            line = line.replace( "###SPOTRANGESTARTNUM###", str(spotrangestartnum) )
            line = line.replace( "###SPOTRANGEFINISHNUM###", str(spotrangefinishnum))
            line = line.replace( "###TESTLOWRES###", str(testlowres))
            line = line.replace( "###TESTHIGHRES###", str(testhighres))
            line = line.replace( "###LOWRES###", str(lowres))
            line = line.replace( "###HIGHRES###", str(highres))
            line = line.replace( "###DIRECTORY###", str(reldir))
            line = line.replace( "###FILENAME###", str(datafilename))
            line = line.replace( "###SECONDS###", str(seconds))
            line = line.replace( "###LYSOZYME_SPACE_GROUP_NUMBER###", str(spacegroupnumber))
            line = line.replace( "###LYSOZYME_UNIT_CELL_CONSTANTS###", str(unitcellconstants))
            nf.write(line) 
        nf.close()



        # CREATE MOSFLM.DAT FILE
        name="mosflm_template.dat"
        cfilename = xdsdir+name
        f = open(cfilename,"r")
        lines=f.readlines()
        f.close()
        name="mosflm.dat"
        nfilename = processdir+"/"+name
        #self.info(nfilename)
        nf = open(nfilename,"w")
        #self.info('final')
        for line in lines:
            line = line.replace( "###DETSAMDIS###", str(round(detsamdis,2)))
            line = line.replace( '###BEAMX###',str(round(mbeamx,2)))
            line = line.replace( "###BEAMY###", str(round(mbeamy,2)))
            line = line.replace( "###DIRECTORY###", str(reldir))
            line = line.replace( "###FILENAME###", str(mdatafilename))
            line = line.replace( "###WAVELENGTH###", str(wavelength) )
            line = line.replace( "###DATARANGESTARTNUM###",str(datarangestartnum))
            nf.write(line)
        nf.close()
    

            

       

 




