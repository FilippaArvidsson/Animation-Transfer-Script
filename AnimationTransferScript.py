#________________ANIMATION TRANSFER SCRIPT__________________
import sys
from PySide2 import QtCore
from PySide2 import QtWidgets
import pymel.core as pm
import itertools
import maya.cmds as cmds
import pymel.core.datatypes as dt

#LISTS
sourceList = []
targetList = []

#FUNCTIONS
def getJointList(currentJ, list):
    list.append(currentJ)
    for child in currentJ.getChildren():
        getJointList(child, list)
        
def getParentsBPO(jointJ, BPOmtx):
	jParent = jointJ.getParent()
	if(type(jParent) == pm.nodetypes.Joint):
		BPOmtx = getParentsBPO(jParent, BPOmtx)
		BPOmtx = jParent.getRotation().asMatrix() * jParent.getOrientation().asMatrix() * BPOmtx
	return BPOmtx
		
def calcFinalRotation(sourceJ, targetJ, key):
	#Isolate rotation from keyframe
	cmds.currentTime( 0 )
	sBindPose = sourceJ.getRotation().asMatrix()
	invrsBindPose = sBindPose.inverse()
	cmds.currentTime( key )
	
	#Isolated Rotation
	kI = invrsBindPose * sourceJ.getRotation().asMatrix()
	
	#Convert rotation to standard coordinate space
	
	sBO = sourceJ.getOrientation().asMatrix()
	sBO2 = sBO.inverse()
	
	#Get Parents
	sBPOmtx = dt.Matrix()
	
	sParent = sourceJ.getParent()
	if(sParent != None):
		cmds.currentTime( 0 )
		sBPO = getParentsBPO(sourceJ, sBPOmtx)
		cmds.currentTime( key )
		sBPO2 = sBPO.inverse()
	else:
		sBPO = dt.Matrix()
		sBPO2 = sBPO.inverse()
	
	#World Space Rotation
	kII = sBO2 * sBPO2 * kI * sBPO * sBO
	
	#Convert rotation to target joint coordinate space
	
	tBO = targetJ.getOrientation().asMatrix()
	tBO2 = tBO.inverse()
	
	#Get Parents
	tBPOmtx = dt.Matrix()
	
	#TEST
	tParent = targetJ.getParent()
	if(tParent != None):
		cmds.currentTime(0)
		tBPO = getParentsBPO(targetJ, tBPOmtx)
		cmds.currentTime( key )
		tBPO2 = tBPO.inverse()
	else:
		tBPO = dt.Matrix()
		tBPO2 = tBPO.inverse()
		
	#Translated Rotation
	kIII = tBO * tBPO * kII * tBPO2 * tBO2
	
	#Calculate Final Rotation
	cmds.currentTime( 0 )
	tBindPose = targetJ.getRotation().asMatrix()
	finalRot = tBindPose * kIII
	cmds.currentTime( key )
	
	#Convert Matrix to Euler Rotation
	
	eulerRot = dt.EulerRotation(finalRot)
	degRot = dt.degrees(eulerRot)
	
	return degRot

def transferAnimation(sourceJ, targetJ):
	keylist = pm.keyframe(sourceJ, query=True, tc=True, attribute="translateX")
	for key in keylist:
		#calc new
		finalRot = calcFinalRotation(sourceJ, targetJ, key)
		
		#give target new		
		targetJ.setRotation(finalRot, space='object')
		
		#set key
		pm.select(targetJ)
		pm.setKeyframe(t=key)

def main():
	#Handle Root Translation
	mainKeylist = pm.keyframe(sourceList[0], query=True, tc=True, attribute="translateX")
	for mainKey in mainKeylist:
		cmds.currentTime(mainKey)
		#Translation
		newTrans = pm.getAttr(sourceList[0].translate)
		targetList[0].setTranslation(newTrans, space='object')
		
		#Set Key
		pm.select(targetList[0])
		pm.setKeyframe(t=mainKey)
		
	for x in range(len(sourceList)):
		transferAnimation(sourceList[x], targetList[x])



#UI
app = QtCore.QCoreApplication.instance()

#Window
wid = QtWidgets.QWidget()
wid.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
wid.resize(400, 400)
wid.setWindowTitle("Transfer Animation")

#WIDGETS

#Buttons
upButtonSource = QtWidgets.QPushButton("Up")
deleteButtonSource = QtWidgets.QPushButton("Delete")
downButtonSource = QtWidgets.QPushButton("Down")

upButtonTarget = QtWidgets.QPushButton("Up")
deleteButtonTarget = QtWidgets.QPushButton("Delete")
downButtonTarget = QtWidgets.QPushButton("Down")

getSource = QtWidgets.QPushButton("Source")
getTarget = QtWidgets.QPushButton("Target")

transferAnimationButton = QtWidgets.QPushButton("Transfer Animation")

#Labels
sourceJoints = QtWidgets.QLabel()
sourceJoints.setText("Source Joints")

targetJoints = QtWidgets.QLabel()
targetJoints.setText("Target Joints")

rootLabel = QtWidgets.QLabel()
rootLabel.setText("Root:")

rootLabel2 = QtWidgets.QLabel()
rootLabel2.setText("Root:")

#Lists
sourceQList = QtWidgets.QListWidget()
targetQList = QtWidgets.QListWidget()

#Lines
sourceRoot = QtWidgets.QLineEdit("")
targetRoot = QtWidgets.QLineEdit("")

#Layout
orglayout = QtWidgets.QVBoxLayout()
layout = QtWidgets.QHBoxLayout()

layout.addWidget(sourceJoints)
layout.addWidget(targetJoints)

layout2 = QtWidgets.QHBoxLayout()

layout2.addWidget(rootLabel)
layout2.addWidget(sourceRoot)
layout2.addWidget(getSource)
layout2.addWidget(rootLabel2)
layout2.addWidget(targetRoot)
layout2.addWidget(getTarget)


layout2a = QtWidgets.QVBoxLayout()

layout2a.addWidget(upButtonSource)
layout2a.addWidget(deleteButtonSource)
layout2a.addWidget(downButtonSource)

layout2b = QtWidgets.QVBoxLayout()

layout2b.addWidget(upButtonTarget)
layout2b.addWidget(deleteButtonTarget)
layout2b.addWidget(downButtonTarget)

layout3 = QtWidgets.QHBoxLayout()

layout3.addLayout(layout2a)
layout3.addWidget(sourceQList)
layout3.addWidget(targetQList)
layout3.addLayout(layout2b)

layout4 = QtWidgets.QVBoxLayout()

layout4.addWidget(transferAnimationButton)



orglayout.addLayout(layout)
orglayout.addLayout(layout2)
orglayout.addLayout(layout3)
orglayout.addLayout(layout4)

#BUTTON FUNCTIONS
#Source Button:
def getSourceList():
	rootJoint = pm.ls(sl=True)[0]
	getJointList(rootJoint, sourceList)
	sourceRoot.setText(sourceList[0].name())
	for i in sourceList:
		sourceQList.addItem(i.name())
		
def sourceUpB():
	#QList
	currItem = sourceQList.currentItem()
	currIndex = sourceQList.row(currItem)
	prevItem = sourceQList.item(currIndex - 1)
	prevIndex = sourceQList.row(prevItem)
	temp = sourceQList.takeItem(prevIndex)
	sourceQList.insertItem(prevIndex, currItem)
	sourceQList.insertItem(currIndex, temp)
	#SourceList
	prevTop = sourceList[prevIndex]
	newTop = sourceList[currIndex]
	sourceList.remove(prevTop)
	sourceList.remove(newTop)
	sourceList.insert(prevIndex, newTop)
	sourceList.insert(currIndex, prevTop)
	print(sourceList)
	
def deleteSourceB():
	#QList
	currItem = sourceQList.currentItem()
	currIndex = sourceQList.row(currItem)
	sourceQList.takeItem(currIndex)
	#SourceList
	currDelete = sourceList[currIndex]
	sourceList.remove(currDelete)
	print(sourceList)
	
def sourceDownB():
	#QList
	currItem = sourceQList.currentItem()
	currIndex = sourceQList.row(currItem)
	nextItem = sourceQList.item(currIndex + 1)
	nextIndex = sourceQList.row(nextItem)
	temp = sourceQList.takeItem(nextIndex)
	sourceQList.insertItem(currIndex, temp)
	sourceQList.insertItem(nextIndex, currItem)
	#SourceList
	nextDown = sourceList[nextIndex]
	newDown = sourceList[currIndex]
	sourceList.remove(nextDown)
	sourceList.remove(newDown)
	sourceList.insert(currIndex, nextDown)
	sourceList.insert(nextIndex, newDown)
	print(sourceList)

#Target Button:		
def getTargetList():
	rootJoint = pm.ls(sl=True)[0]
	getJointList(rootJoint, targetList)
	targetRoot.setText(targetList[0].name())
	for i in targetList:
		targetQList.addItem(i.name())
		
def targetUpB():
	#QList
	currItem = targetQList.currentItem()
	currIndex = targetQList.row(currItem)
	prevItem = targetQList.item(currIndex - 1)
	prevIndex = targetQList.row(prevItem)
	temp = targetQList.takeItem(prevIndex)
	targetQList.insertItem(prevIndex, currItem)
	targetQList.insertItem(currIndex, temp)
	#SourceList
	prevTop = targetList[prevIndex]
	newTop = targetList[currIndex]
	targetList.remove(prevTop)
	targetList.remove(newTop)
	targetList.insert(prevIndex, newTop)
	targetList.insert(currIndex, prevTop)
	print(targetList)
	
	
def deleteTargetB():
	#QList
	currItem = targetQList.currentItem()
	currIndex = targetQList.row(currItem)
	targetQList.takeItem(currIndex)
	#SourceList
	currDelete = targetList[currIndex]
	targetList.remove(currDelete)
	print(targetList)
	
def targetDownB():
	#QList
	currItem = targetQList.currentItem()
	currIndex = targetQList.row(currItem)
	nextItem = targetQList.item(currIndex + 1)
	nextIndex = targetQList.row(nextItem)
	temp = targetQList.takeItem(nextIndex)
	targetQList.insertItem(currIndex, temp)
	targetQList.insertItem(nextIndex, currItem)
	#SourceList
	nextDown = targetList[nextIndex]
	newDown = targetList[currIndex]
	targetList.remove(nextDown)
	targetList.remove(newDown)
	targetList.insert(currIndex, nextDown)
	targetList.insert(nextIndex, newDown)
	print(targetList)
	
#TRANSFER ANIMATION
def animTrans():
	main()
	
#Connect Buttons
getSource.clicked.connect(getSourceList)
getTarget.clicked.connect(getTargetList)

upButtonSource.clicked.connect(sourceUpB)
deleteButtonSource.clicked.connect(deleteSourceB)
downButtonSource.clicked.connect(sourceDownB)

upButtonTarget.clicked.connect(targetUpB)
deleteButtonTarget.clicked.connect(deleteTargetB)
downButtonTarget.clicked.connect(targetDownB)

transferAnimationButton.clicked.connect(animTrans)

#Exec
wid.setLayout(orglayout)

wid.show()
app.exec_()