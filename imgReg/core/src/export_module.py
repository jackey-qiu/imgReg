# -*- coding: utf-8 -*-
import os
import numpy as np
import os
import string

def lock_aspect_rescale(attrs, export_arr):
    if 'AspectRatio' in attrs.keys():
        asp = attrs['AspectRatio']
    else:
        raise ValueError("AspectRatio required")
    if len(asp) > 0:
        # asp is the dimension of one pixel
        out_shape = list(export_arr.shape)
        zoom_factors = [1] * 2
        if asp[0] < asp[1]:
            out_shape[1] = int(asp[1] / asp[0] * out_shape[1])
            zoom_factors[1] = out_shape[1] / export_arr.shape[1]
        elif asp[0] > asp[1]:
            out_shape[0] = int(asp[0] / asp[1] * out_shape[0])
            zoom_factors[0] = out_shape[0] / export_arr.shape[0]
        else:
            pass
        import scipy.ndimage.interpolation
        return scipy.ndimage.interpolation.zoom(export_arr, zoom_factors)


def make_safe_filename(inputFilename):
    # Set here the valid chars
    safechars = string.ascii_letters + string.digits + "~ -_.[]+"
    try:
        return ''.join([x if x in safechars else '_' for x in inputFilename])
    except Exception as e:
        print(e)
        return "invalid_file_name"
    pass


def generate_xml_attr(dset_list):
    pass


def write_im_xml(xml_path, attrList, distributed=False):
    '''
    Parameters
    ----------

    Returns
    -------

    Notes
    -----
    none

    Examples
    --------
    >>>
    '''
    from lxml import etree as ET
    # import xml.etree.ElementTree as ET
    import os
    # create the file structure
    data = ET.Element('ImageMap')
    for i, d in enumerate(attrList):
        imageitem = ET.SubElement(data, 'Image{}'.format(i))
        filename = ET.SubElement(imageitem, "Filename")
        Opacity = ET.SubElement(imageitem, "Opacity")
        Visible = ET.SubElement(imageitem, "Visible")
        Rotation = ET.SubElement(imageitem, "Rotation")

        # // recalculate_all the center and size based on the given outline
        d["Center"] = [0] * 3
        d["Size"] = [0] * 2
        d["Size"][0] = abs(d["Outline"][1] - d["Outline"][0])
        d["Size"][1] = abs(d["Outline"][3] - d["Outline"][2])
        d["Center"][0] = d["Size"][0] / 2 + d["Outline"][0]
        d["Center"][1] = d["Size"][1] / 2 + d["Outline"][2]
        d['Focus'] = d["Outline"][4]
        Center = ET.SubElement(imageitem, "Center")
        Size = ET.SubElement(imageitem, "Size")
        Focus = ET.SubElement(imageitem, "Focus")
        filename.text = d['Name']
        Opacity.text = str(d['Opacity'])
        if d['Visible']:
            Visible.text = "TRUE"
        else:
            Visible.text = "FALSE"
        Rotation.text = str(d['Rotation'])
        if distributed:
            BaseFolder = ET.SubElement(imageitem, "BaseFolder")
            BaseFolder.text = os.path.dirname(d['Path'])
        Center.text = str(d['Center'][0]) + ',' + str(d['Center'][1])
        Size.text = str(d['Size'][0]) + ',' + str(d['Size'][1])
        Focus.text = str(d['Focus'])

    dataitem = ET.SubElement(data, "Data")
    imagecount = ET.SubElement(dataitem, "ImageCount")
    imagecount.text = str(len(attrList))
    if not distributed:
        basefolder = ET.SubElement(dataitem, "BaseFolder")
        # basefolder.text = attrList[0]['BaseFolder']
        basefolder.text = xml_path

    tree = ET.ElementTree(data)
    tree.write(xml_path, pretty_print=True, xml_declaration=True, encoding="Windows-1252")


