import ezomero
from ezomero.rois import Ellipse
from omero.gateway import BlitzGateway
import re
from omero.model.enums import UnitsLength
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import math


def connect(hostname, username, password):
    '''
    Connect to the OMERO server.
    '''
    conn = BlitzGateway(username, password, host=hostname, port=4064, secure=True)
    if not conn.connect():
        raise ConnectionError("Failed to connect to OMERO server")
    conn.c.enableKeepAlive(60)
    return conn


def read_rois_from_xml(xml_path, pixel_size_x, pixel_size_y,
                       offset_topleft_x, offset_topleft_y, factor_x,
                       factor_y):
    '''
    Read the ROIs from the NDPA file and convert them into OME ROIs.
    Each shape will be independent.
    '''
    tree = ET.parse(xml_path)
    root = tree.getroot()
    shapes = []

    for ndpviewstate in root.findall('ndpviewstate'):
        annotation = ndpviewstate.find('annotation[@type="circle"]')
        if annotation is not None:
            try:
                x_nm = float(annotation.find('x').text)
                y_nm = float(annotation.find('y').text)
                radius_nm = float(annotation.find('radius').text)
                color_hex = annotation.get('color')
                label = ndpviewstate.find('title').text

                # Convert nanometers to micrometers
                x_um = x_nm / factor_x
                y_um = y_nm / factor_y
                radius_um = radius_nm / factor_x

                # Calculate the area in square micrometers
                area_um2 = math.ceil(math.pi * (radius_um ** 2))

                # Convert micrometers to pixels
                x_px = x_um / pixel_size_x + offset_topleft_x
                y_px = y_um / pixel_size_y + offset_topleft_y
                radius_px = radius_um / ((pixel_size_x + pixel_size_y) / 2)

                print(f"ROI: {label}, x_nm: {x_nm}, y_nm: {y_nm}, radius_nm: {radius_nm}, area_um2: {area_um2}")
                print(f"x_um: {x_um}, y_um: {y_um}, radius_um: {radius_um}")
                print(f"x_px: {x_px}, y_px: {y_px}, radius_px: {radius_px}")

                fill_color = (0, 0, 0, 0)
                stroke_color = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5)) + (0,)
                stroke_width = 2.0

                # Assign `z=None` for visibility across all Z levels
                ellipse = Ellipse(x=x_px, y=y_px, x_rad=radius_px, y_rad=radius_px, z=None,
                                  label=label, fill_color=fill_color,
                                  stroke_color=stroke_color, stroke_width=stroke_width)
                shapes.append(ellipse)
            except Exception as e:
                print(f"Error parsing annotation: {e}")

    return shapes


def add_rois_individual(conn, image_id, shapes):
    '''
    Save each ROI individually into OMERO.
    '''
    for shape in shapes:
        # Post each shape as a separate ROI
        ezomero.post_roi(conn, image_id, [shape])


def retrieve_offset(image):
    '''
    Retrieve the offset values from the original metadata so
    we know exactly the location of the shapes.
    '''
    om = image.loadOriginalMetadata()
    KEY = "Slide center"
    center_x = 0
    center_y = 0
    center_z = 0
    unit_x = ""
    unit_y = ""
    unit_z = ""

    if om is not None:
        for keyValue in om[1]:
            if len(keyValue) > 1 and KEY in keyValue[0]:
                key = keyValue[0]
                value = keyValue[1]
                if "X" in key:
                    center_x = value
                    res = re.findall(r'\(.*?\)', key)
                    unit_x = str(res).replace('(', '').replace(')', '')
                elif "Y" in key:
                    center_y = value
                    res = re.findall(r'\(.*?\)', key)
                    unit_y = str(res).replace('(', '').replace(')', '')
                elif "Z" in key:
                    center_z = value
                    res = re.findall(r'\(.*?\)', key)
                    unit_z = str(res).replace('(', '').replace(')', '')

    return (center_x, center_y, center_z, unit_x, unit_y, unit_z)


def upload_original_roi_file(conn, image, xml_path):
    '''
    Attach the original NDPA file to the image as an attachment.
    '''
    attachment = conn.createFileAnnfromLocalFile(xml_path, mimetype="text/xml", desc=None)
    image.linkAnnotation(attachment)


def change_omero_group(conn, new_group_name):
    """
    Changes the current OMERO group for the connected user.
    """
    conn.setGroupForSession(new_group_name)
    print(f"Successfully switched to the '{new_group_name}' group.")


def main():
    root = tk.Tk()
    root.withdraw()

    conn = None

    try:
        upload_file = True
        hostname = simpledialog.askstring("Host", "Host:", initialvalue="xxx") #Put your initial host
        username = simpledialog.askstring("Username", "Username:")
        password = simpledialog.askstring("Password", "Password:", show='*')
        new_group = simpledialog.askstring("Group", "Group:")
        image_id = simpledialog.askinteger("Image ID", "Image ID:")
        xml_path = filedialog.askopenfilename(title="Select XML/NDPA File", filetypes=(("NDPA Files", "*.ndpa"), ("XML Files", "*.xml"), ("All Files", "*.*")))

        if not all([hostname, username, password, image_id, xml_path]):
            messagebox.showwarning("Input Error", "All fields are required.")
            return

        conn = connect(hostname, username, password)

        print("Member of:")
        for g in conn.getGroupsMemberOf():
            print("   ID:", g.getId(), " Name:", g.getName())
        group = conn.getGroupFromContext()
        print("Current group:", group.getName())
        change_omero_group(conn, new_group)

        image = conn.getObject("Image", image_id)
        if image is None:
            raise ValueError("Image with the provided ID not found")

        offset_x, offset_y, offset_z, unit_x, unit_y, unit_z = retrieve_offset(image)

        size_x_obj = image.getPixelSizeX(units=True)
        size_y_obj = image.getPixelSizeX(units=True)

        if size_x_obj is None or size_y_obj is None:
            raise ValueError("Physical size of pixels not available")
        pixel_size_x = float(size_x_obj.getValue())
        pixel_size_y = float(size_y_obj.getValue())

        factor_x = 1
        factor_y = 1
        if size_x_obj.getUnit() == UnitsLength.MICROMETER and "nm" in unit_x:
            factor_x = 1000
        if size_y_obj.getUnit() == UnitsLength.MICROMETER and "nm" in unit_y:
            factor_y = 1000

        offset_x = offset_x / (factor_x * pixel_size_x)
        offset_topleft_x = image.getSizeX() / 2 - offset_x

        offset_y = offset_y / (factor_y * pixel_size_y)
        offset_topleft_y = image.getSizeY() / 2 - offset_y

        shapes = read_rois_from_xml(xml_path, pixel_size_x, pixel_size_y,
                                    offset_topleft_x, offset_topleft_y,
                                    factor_x, factor_y)

        # Add ROIs individually
        add_rois_individual(conn, image_id, shapes)

        if upload_file:
            upload_original_roi_file(conn, image, xml_path)

        messagebox.showinfo("Success", "ROIs successfully added to the image.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
