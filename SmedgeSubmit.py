# ##### BEGIN MIT LICENSE BLOCK #####
#
#  Copyright <2018> <Johannes Wuensch>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), 
#  to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, 
#  and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
#  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# ##### END MIT LICENSE BLOCK #####


#  This script requires a an installed Version of the Smedge render manager


###############################################################

# Please adjust these paths to your Smedge installation path. 
# Normally you only have to adjust the path of your current used operating system
# If you sync this script with all the machines in your network and you are using machines with different operating systems, it makes sense to adjust all of them. Each computer will automatically use the correct one.

smedgeInstallationPath_Windows = "C:\\Program Files\\Smedge\\"
smedgeInstallationPath_Linux = "/home/YourUserName/Smedge/"
smedgeInstallationPath_MacOS = "/Applications/Smedge.app/Contents/MacOS/"

###############################################################


bl_info = {
    "name": "Smedge Submitter",
    "description": "Render your Blender scenes distributed with the Smedge render manger",
    "author": "Johannes Wuensch",
    "version": (1, 0, 0),
    "blender": (2, 79, 0),
    "location": "Properties > Render> SmedgeSubmitter",
    "warning": "",
    "wiki_url": "",
    "category": "Render" }



import os, platform, subprocess, shlex, sys
import bpy

from bpy.props import *


smedgeSubmitterPath = ""
smedgePoolManagerPath = ""

if platform.system() == "Windows":
	smedgeInstallationPath = smedgeInstallationPath_Windows.replace("/","\\")  # convert forward-slashes to back-slashes
	smedgeSubmitterPath =  '\"' + smedgeInstallationPath + "Submit.exe\"" 
	smedgePoolManagerPath =  '\"' + smedgeInstallationPath + "PoolManager.exe\""
	
if platform.system() == "Linux":
	smedgeInstallationPath = smedgeInstallationPath_Linux.replace("\\","/")  # convert back-slashes to forward-slashes
	smedgeSubmitterPath =  '\"' + smedgeInstallationPath + "Submit\"" 
	smedgePoolManagerPath = '\"' + smedgeInstallationPath + "PoolManager\"" 

if platform.system() == "Darwin":
	smedgeInstallationPath = smedgeInstallationPath_MacOS.replace("\\","/")  # convert back-slashes to forward-slashes
	smedgeSubmitterPath =  '\"' + smedgeInstallationPath + "Submit\"" 
	smedgePoolManagerPath = '\"' + smedgeInstallationPath + "PoolManager\"" 




# -- Helper functions/classes

class SmedgeInfosOperator(bpy.types.Operator):
	bl_idname	= "smedge.infos"
	bl_label	= "SMEDGE INFO"

	Message		= StringProperty()

	
	

	def invoke(self, context, event):
		calculatedWidth = len(self.Message)*10
		if "Error" in self.Message:
			calculatedWidth = max(calculatedWidth, 1000)
		return context.window_manager.invoke_props_dialog(self, width = calculatedWidth, height = 450)

	def draw(self, context):
		row = self.layout.split(1.0)
		row.label(self.Message)

		# Add an additional hint if an error occurs
		if "Error" in self.Message:
			row = self.layout.split(1.0)
			row.label("Please make sure that the path at the top of the \"SmedgeSubmitter.py\" file points to your Smedge installation!")
			row = self.layout.split(1.0)
			row.operator("smedge.openfolder", text="edit SmedgeSubmitter.py")
	
	def execute(self, context):
		return {"FINISHED"}


def SmedgeInfo(msg):
	print (msg)
	bpy.ops.smedge.infos("INVOKE_DEFAULT", Message = msg)
	return False





class SmedgeOpenScriptContainingFolderOperator(bpy.types.Operator):
	"""Open the Folder in which this script File is located"""
	bl_idname = "smedge.openfolder"
	bl_label = "Open Script Folder"

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):

		# get the path of this script file
		path = os.path.dirname( os.path.realpath(__file__) )
		
		# build the command line
		commandLineString = ""

		if platform.system() == "Windows":
			commandLineString = "explorer " + "\"" + path + "\""
		
		if platform.system() == "Linux":
			commandLineString = "xdg-open " + "\"" + path + "\""
        
		if platform.system() == "Darwin":
			commandLineString = "open " + "\"" + path + "\""
		


		print("Smedge Submitter executed: " + commandLineString)


		shellArgs = shlex.split(commandLineString)
		

		try:
			OpenFolderSubprocess = subprocess.Popen(shellArgs)
			returncode = OpenFolderSubprocess.wait()
	
		except:
			err = str (sys.exc_info()[1]) 
			SmedgeInfo("Open script containing folder failed! Error code: %s" % (err))
			
		
		return {"FINISHED"}





class SmedgeSubmitOperator(bpy.types.Operator):
	"""Submits a new job to Smedge"""
	bl_idname	= "smedge.submit"
	bl_label	= "Submit job"

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):
		
		scn = bpy.context.scene

		if str( os.path.normpath(bpy.data.filepath)) == "." :
			SmedgeInfo("Please save your file first!")
		else:

			#  Build the command line
			commandLineString  = smedgeSubmitterPath
			commandLineString += " Script"
			commandLineString += " -Type Blender"
			commandLineString += " -Scene " +  "\"" + str( os.path.normpath(bpy.data.filepath) ) + "\""
			commandLineString += " -Range " + str( scn.frame_start ) + "-" + str( scn.frame_end )
			commandLineString += " -Name " + str( os.path.basename(bpy.data.filepath) ).split(".blend")[0]
			commandLineString += " -priority " + str(scn.SmedgePriority)
			commandLineString += " -PacketSize " + str(scn.SmedgePacketSize)
			if scn.SmedgeJobStartPaused:
				commandLineString += " -paused"
			if scn.SmedgePools != "all":
				commandLineString += " -pool " + scn.SmedgePools
		

			print("Smedge Submitter executed: " + commandLineString)

			shellArgs = shlex.split(commandLineString) #important to also work on linux

			try:
				SubmitSubprocess = subprocess.Popen(shellArgs)
				returncode = SubmitSubprocess.wait(timeout = 3)
	
				if returncode>0:
					SmedgeInfo("Job submission to Smedge failed! Error code: %s" % (returncode))
					return None
				else:
					SmedgeInfo("Job successfully submitted to Smedge!")

			except subprocess.TimeoutExpired:
				SmedgeInfo("Time out! Are you sure a Smedge farm is running somewhere on the network?")

			except:
				err = str (sys.exc_info()[1]) 
				SmedgeInfo("Job submission to Smedge failed! Error code: %s" % (err))
			
		
		return {"FINISHED"}





class SmedgeLoadPoolsOperator(bpy.types.Operator):
	"""Load all available pools from the render farm"""
	bl_idname	= "smedge.load_pools"
	bl_label	= "load pools"

	@classmethod
	def poll(cls, context):
		return True

	def execute(self, context):

		scn = bpy.context.scene

		commandLineString  = smedgePoolManagerPath + " List Name"

		print("Smedge Submitter executed: " + commandLineString)

		shellArgs = shlex.split(commandLineString) 


		try:
			resultAsBytes = subprocess.check_output( shellArgs , timeout = 3 )  # for some reason the result under Linux is always r"" while it's correct on Windows

		except:
			err = str( sys.exc_info()[1] )
			if "timed out" in err:
				SmedgeInfo("Time out! Are you sure a Smedge farm is running somewhere on the network?")
			else:
				SmedgeInfo("Updating pools failed! Error code: %s" % (err))
			
		else:
			
			#convert bytes result to string and remove all '\r' 
			resultAsString = resultAsBytes.decode("utf-8").replace("\r","") 

			# split string into array and remove empty lines
			resultingPoolsStringArray = [line for line in resultAsString.split('\n') if line.strip() != '']   

			if resultingPoolsStringArray[0] != "No Pools Available.":

				# generate the items for the enum
				poolItems = [('all','all engines','All engines connected to the Smedge farm will process this job',1)]
				itemNumber = 2
				for pool in resultingPoolsStringArray:
					poolItems.append((str(pool), str(pool),"", itemNumber))
					itemNumber += 1

			
				# update SmedgePools property
				bpy.types.Scene.SmedgePools = bpy.props.EnumProperty( items = poolItems, name = "pool" )

				SmedgeInfo("Pools successfully updated!")

			else:
				SmedgeInfo("Sorry. Looks like there are no pools available on the current render farm!")

		
		return {"FINISHED"}



class SmedgeSubmitPanel(bpy.types.Panel):
	bl_idname		= "smedge_panel"
	bl_label		= "Smedge Submitter"
	bl_space_type   = 'PROPERTIES'
	bl_region_type  = 'WINDOW'
	bl_context      = "render"


	def draw (self, context):

		#define variables
		scn = bpy.context.scene
		fileFormat = scn.render.image_settings.file_format
		width = scn.render.resolution_x
		height = scn.render.resolution_y
		ResolutionPercentage = scn.render.resolution_percentage
		color_mode = scn.render.image_settings.color_mode
		color_depth = scn.render.image_settings.color_depth
		engineInfo = ""
		renderOut = scn.render.filepath
		renderOut = renderOut.replace("//", "\\")

		
		
		## draw panel ##
		
		layout	= self.layout

		# job summary
		layout.label("Render Settings Summary:")
		
		box = layout.box()

		box.label("Start:  " + str(scn.frame_start))
		box.label("End:  " + str(scn.frame_end))
		box.label("Resolution:  " + str(width) + " x " + str(height) + "     " + str(ResolutionPercentage) + "%")

		if scn.render.engine == "CYCLES":
			if scn.cycles.progressive == "PATH":
				engineInfo = scn.render.engine + "     " + str(scn.cycles.samples) + " samples"
			if scn.cycles.progressive == "BRANCHED_PATH":
				engineInfo = scn.render.engine + "     Branched Path Tracing"
		if scn.render.engine == "BLENDER_RENDER":
			engineInfo = scn.render.engine 
		box.label(engineInfo)

		box.label("---- Active Render Layers ----")

		for rl in scn.render.layers:
			renderLayerInfo = ""
			if rl.use:
				if scn.render.engine == "CYCLES":
					if rl.samples == 0:
						if rl.cycles.use_denoising:
							renderLayerInfo = rl.name + ":   denoised"
						else:
							renderLayerInfo = rl.name + ":   no denoising"
					else:
						if rl.cycles.use_denoising:
							renderLayerInfo = rl.name + ":   " + str(rl.samples) + " sp | denoised"
						else:
							renderLayerInfo = rl.name + ":   " + str(rl.samples) + " sp | no denoising"
				else:
					renderLayerInfo = rl.name
			if renderLayerInfo != "":
				box.label(renderLayerInfo)

		box.label("-------------------------------")

		box.label("Image Type:  " + fileFormat + "     " + color_mode + "     " + color_depth +" bit")
		box.label("Render Output:  " +  os.path.dirname(renderOut) + "\\" + os.path.basename(renderOut)) 

		# Smedge Settings
		layout.label("")
		layout.label("Smedge Job Settings:")

		box = layout.box()

		col = box.column()
		col.scale_y = 0.5
		layout.label("")

		col = box.column()
		row = col.row()
		row.prop(scn, "SmedgePriority")
		row.prop(scn, "SmedgePacketSize")

		if platform.system() != "Linux": # only show pool options for Windows and MacOS as Linux doesn't work
			col = box.column()
			row = col.row()
			row.prop(scn, "SmedgePools")
			row.operator("smedge.load_pools", text="load pools")

		col = box.column()
		row = col.row()
		row.prop (scn, "SmedgeJobStartPaused")


		# submit button
		col	= layout.column()
		col.scale_y = 2
		col.operator("smedge.submit", text="Submit job to Smedge")

		col	= layout.column()
	
		
		

def register():
	bpy.utils.register_class(SmedgeSubmitOperator)
	bpy.utils.register_class(SmedgeLoadPoolsOperator)
	bpy.utils.register_class(SmedgeSubmitPanel)
	bpy.utils.register_class(SmedgeInfosOperator)
	bpy.utils.register_class(SmedgeOpenScriptContainingFolderOperator)
	

	# define Scene Properties for Smedge
	bpy.types.Scene.SmedgePriority = bpy.props.IntProperty( name = "Job Priority", description = "Priority of the job on the Smedge render farm. Higher priority jobs will be rendered first.", default = 10, min = 0, max = 100)
	bpy.types.Scene.SmedgePacketSize = bpy.props.IntProperty( name = "Packet Size", description = "Number of frames each client will render in a row without reloading the scene.", default = 5, min = 1)
	bpy.types.Scene.SmedgePools = bpy.props.EnumProperty( items = [('all','all engines','All engines connected to the Smedge farm will process this job',1)], name = "pool" )
	bpy.types.Scene.SmedgeJobStartPaused = bpy.props.BoolProperty(name = "Start job paused", description = "job will be sent to farm in paused mode. You have to manually activate it on the farm later to render it.", default = False)

def unregister():
	bpy.utils.unregister_class(SmedgeSubmitOperator)
	bpy.utils.unregister_class(SmedgeLoadPoolsOperator)
	bpy.utils.unregister_class(SmedgeSubmitPanel)
	bpy.utils.unregister_class(SmedgeInfosOperator)
	bpy.utils.unregister_class(SmedgeOpenScriptContainingFolderOperator)

if __name__ == "__main__":
	register()








