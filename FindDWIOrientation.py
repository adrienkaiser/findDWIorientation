#!/usr/bin/python

import os # .access .path .rename .remove .mkdir
import sys # .exit
import subprocess # .call
import random

############################################
#             Define variables             #
############################################
DWI='/NIRAL/work/akaiser/Networking/NFG/nfg_1.1.1/generated_collections/130325112527/DWI/dwi.nhdr'
if not os.access(DWI, os.R_OK):
  print '> The given DWI is not readable:',DWI
  print '> ABORT'
  sys.exit(1)

OutputFolder='/NIRAL/work/akaiser/Networking/NFG/nfg_1.1.1/generated_collections/130325112527/DWI'
if not os.access(OutputFolder, os.W_OK):
  print '> The given output folder is not writable:',OutputFolder
  print '> ABORT'
  sys.exit(1)

OutputFolder = OutputFolder + '/findDWIorientation'
if not os.path.isdir(OutputFolder):
  print '> Making output directory:',OutputFolder
  os.mkdir(OutputFolder)

############################################
#       Define and check tools             #
############################################
def CheckTool(Tool):
  ExceptionCaught=0
  try:
    ExitCode = subprocess.call( Tool + ['--help'], stdout=open(os.devnull, 'w') , stderr=open(os.devnull, 'w') ) # call command with no output
  except:
    ExceptionCaught=1
  if ExceptionCaught or ExitCode!=0 :
    print '> Error in:',Tool
    print '> ABORT'
    sys.exit(1)

dtiestimCmd=['/tools/bin_linux64/dtiestim']
CheckTool(dtiestimCmd)
dtiprocessCmd=['/tools/bin_linux64/dtiprocess']
CheckTool(dtiprocessCmd)
OtsuThresholdCmd=['/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/Slicer', '--launch', '/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/lib/Slicer-4.2/cli-modules/OtsuThresholdSegmentation']
CheckTool(OtsuThresholdCmd)
tractoCmd=['/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/Slicer', '--launch', '/tools/Slicer4/Slicer-4.2.2-1-linux-amd64/lib/Slicer-4.2/cli-modules/TractographyLabelMapSeeding']
CheckTool(tractoCmd)
fiberstatsCmd=['/tools/bin_linux64/fiberstats']
CheckTool(fiberstatsCmd)

############################################
# Compute avg fib len for all possible MFs #
############################################

## Function to execute an external command with NO output+ test exit code
def ExecuteCommand (Command):
  print '> Running:',Command
  if subprocess.call( Command, stdout=open(os.devnull, 'w') , stderr=open(os.devnull, 'w') ) !=0 :
    print '> Error executing command'
    print '> ABORT'
    sys.exit(1)

## Write Measurement Frames in a table
MFTable=[]
triples=['(X,0,0)','(0,X,0)','(0,0,X)']
doubles=[1,-1]
for XYZ in [ (X,Y,Z) for X in doubles for Y in doubles for Z in doubles ]: 
  for XYZtriple in [ (Xtriple,Ytriple,Ztriple) for Xtriple in triples for Ytriple in triples for Ztriple in triples ] :
    if XYZtriple[1] != XYZtriple[0] and XYZtriple[2] != XYZtriple[1] and XYZtriple[2] != XYZtriple[0]: # then OK
      MF = XYZtriple[0].replace('X',str(XYZ[0])) + ' ' + XYZtriple[1].replace('X',str(XYZ[1])) + ' ' + XYZtriple[2].replace('X',str(XYZ[2]))
      MFTable.append(MF)

## Compute Avg Fiber Length for all possible MFs
AvgFibLenTupleTable=[] # each element of the table is [MF,AvgFibLen]
print '> Testing',len(MFTable),'measurement frames...'
for MF in MFTable:
  MFindex=len(AvgFibLenTupleTable) + 1 # because values appended: size = index
  # Display Measurement Frame
  print '> Testing MF', MFindex, ':', MF

  # Update DWI header
  MFDWI = OutputFolder + '/MF' + str(MFindex) + '_dwi.nhdr'
  if not os.path.isfile(MFDWI): # NO auto overwrite => if willing to overwrite, rm files
    MFDWIfile = open(MFDWI,'a') # open for Append
    for line in open(DWI): # read all lines and replace line containing 'measurement frame' by the new MF
      if 'measurement frame' in line :
        MFDWIfile.write('measurement frame: ' + MF + '\n')
      elif 'data file' in line : # if not full path (not begin by '/'), need to give the full path to the date file(s)
        DataFile = line.split(' ')[2]
        if DataFile[0] != '/': # not full path
          NewDataFile = os.path.abspath(os.path.dirname(DWI) + '/' + DataFile)
        else: # full path: keep as is
          NewDataFile = DataFile
        MFDWIfile.write( line.replace(DataFile,NewDataFile) )
      else :
        MFDWIfile.write(line)
    MFDWIfile.close()

  # Compute DTI
  DTI = OutputFolder + '/MF' + str(MFindex) + '_dti.nrrd'
  ComputeDTICmdTable = dtiestimCmd + ['--dwi_image', MFDWI, '--tensor_output', DTI, '-m', 'wls']
  if not os.path.isfile(DTI): # NO auto overwrite => if willing to overwrite, rm files
    ExecuteCommand(ComputeDTICmdTable)

  # Compute FA # !! Fa needs to be computed only once because same for all MFs
  FA = OutputFolder + '/fa.nrrd'
  ComputeFACmdTable = dtiprocessCmd + ['--dti_image', DTI, '-f', FA]
  if not os.path.isfile(FA): # NO auto overwrite => if willing to overwrite, rm files
    ExecuteCommand(ComputeFACmdTable)

  # Compute mask by OTSU thresholding FA # !! Mask needs to be computed only once because same for all MFs
  Mask = OutputFolder + '/mask.nrrd'
  ComputeMaskCmdTable = OtsuThresholdCmd + [FA, Mask, '--minimumObjectSize', '10', '--brightObjects'] # brightObjects= bright = fa = 1 # --minimumObjectSize 10 => to avoid 1-voxel artefacts
  if not os.path.isfile(Mask): # NO auto overwrite => if willing to overwrite, rm files
    ExecuteCommand(ComputeMaskCmdTable)

  # Compute Tractography
  tracts = OutputFolder + '/MF' + str(MFindex) + '_tracts.vtk'

  # Compute Average Fiber Length
  AvgFibLen=random.randint(1,100)
  AvgFibLenTupleTable.append( [MF,AvgFibLen] )

############################################
#   Find max MF: max average fiber length  #
############################################

## Sort Average Fiber Length table by AvgFibLen
AvgFibLenTupleTable = sorted(AvgFibLenTupleTable, key=lambda AvgFibLenTuple: AvgFibLenTuple[1], reverse=True) # reverse: higher in 1st position
print '> Results:'
for AvgFibLenTuple in AvgFibLenTupleTable:
  print '> MF', MFTable.index(AvgFibLenTuple[0])+1, '=', AvgFibLenTuple[0] + ' \t: Average Fiber Length = ' + str(AvgFibLenTuple[1])

## Keep max Average Fiber Length in table (= 1st value because sorted)
print '> The measurement frame MF', MFTable.index(AvgFibLenTupleTable[0][0])+1, ':', AvgFibLenTupleTable[0][0], '(AvgFibLen=' + str(AvgFibLenTupleTable[0][1]) + ') will be used.'

## Exit OK
sys.exit(0)

