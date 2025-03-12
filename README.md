=========================================
 OMERO ROI Importer from NDPA/XML
=========================================

Description:
------------
This Python script connects to an OMERO server and imports ROIs (Regions of Interest) 
from an NDPA/XML file. The extracted ROIs are converted into OME-compatible ROIs and 
uploaded to a specified OMERO image. The script also allows users to attach the original 
ROI file to the image for future reference.

Features:
---------
- Connects to an OMERO server using user-provided credentials.
- Reads and extracts ROIs (ellipses) from an NDPA/XML file.
- Converts nanometer-based coordinates into micrometers and pixels.
- Uploads extracted ROIs to a specified OMERO image.
- Attaches the original NDPA/XML file to the OMERO image as an annotation.
- Supports switching between OMERO groups.

Requirements:
-------------
The script requires the following Python libraries:
- ezomero
- omero-gateway
- tkinter (built-in for most Python distributions)

Installation:
-------------
Before running the script, install the required dependencies:

1. Install necessary Python packages:
pip install ezomero pip install omero-py
2. If `tkinter` is not installed, install it manually (Linux users only):
sudo apt-get install python3-tk

Usage:
------
1. Run the script:
python ImportNDPA.py
2. Enter OMERO server credentials when prompted.
3. Select the OMERO group where the image is stored.
4. Enter the OMERO Image ID where ROIs will be uploaded.
5. Select an NDPA/XML file containing the ROIs.
6. The script will extract and upload ROIs to the specified image.
7. If enabled, the script will also attach the original XML file to the image.

Author:
-------
This script was developed by **Daurys De Alba**.

For inquiries, contact:
- Email: daurysdealbaherra@gmail.com
- Email: DeAlbaD@si.edu
