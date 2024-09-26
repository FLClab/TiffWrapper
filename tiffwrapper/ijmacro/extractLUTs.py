
import os, glob

from ij import IJ, WindowManager
import jarray

# This script allows to convert all LUTs to a text file. This may fail if for
# some reason the user does not have installed some of the LUTs
#
# The script should be launched from the Fiji

SAVEPATH = "../LUTs/"
SAVEPATH = "/Users/Anthony/Desktop/LUTS/"
LUTS = [
	'edges', 'biop-Azure', 'mpl-magma', 'Green Hot', '16_colors', 'ICA2', 'sepia', 'ICA3', 'SQUIRREL-Errors', 'biop-Chartreuse', 'biop-SpringGreen', 'Magenta Hot', 'unionjack', 'Orange Hot', 'Rainbow RGB', 'Red Hot', 'mpl-inferno', 'blue_orange_icb', '6_shades', 'Thermal', 'smart', 'mpl-viridis', 'glow', 'physics', 'SQUIRREL-FRC', 'ICA', 'glasbey_inverted', 'royal', 'thallium', 'biop-Amber', 'Yellow Hot', 'Green Fire Blue', 'HiLo', 'cool', 'biop-ElectricIndigo', 'thal', 'brgbcmyw', '5_ramps', 'biop-BrightPink', 'Cyan Hot', 'gem', 'phase', 'NanoJ-Orange', 'biop-12colors', 'mpl-plasma', 'glasbey_on_dark', 'glasbey'
]

LUTS = glob.glob(os.path.join("/Applications/Fiji.app/luts/*"))
# LUTS = [
# 	lut.split("/")[-1].split(".")[0] for lut in LUTS
# ]

def extractLUTs(lut):
	print(lut)
	# IJ.run(lut);
	IJ.open(lut);

	image = WindowManager.getCurrentImage()
	if image == None:
		IJ.error('Need an image')
		return
	ip = image.getProcessor()
	cm = ip.getCurrentColorModel()
	if not hasattr(cm, 'getMapSize'):
		IJ.error('Need an 8-bit color image')
		return

	size = cm.getMapSize()
	if size > 256:
		IJ.error('Need an 8-bit color image')
		return
	reds = jarray.zeros(size, 'b')
	greens = jarray.zeros(size, 'b')
	blues = jarray.zeros(size, 'b')
	cm.getReds(reds)
	cm.getGreens(greens)
	cm.getBlues(blues)

	def color(array, index):
		value = array[index]
		if value < 0:
			value += 256
		return str(value)

	colors = []
	for i in range(256):
		colors.append([
			color(reds, i), color(greens, i), color(blues, i)
		])

	lut = lut.split("/")[-1].split(".")[0]
	with open(SAVEPATH + lut + ".lut", "w") as file:
		for color in colors:
			color = " ".join(color) + "\n"
			file.write(color)

for lut in LUTS:
	extractLUTs(lut)
