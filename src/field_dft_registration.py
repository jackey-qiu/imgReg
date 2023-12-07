# -*- coding: utf-8 -*-
import os


# // module to manage the aligment tool in the field view
from PySide6 import QtGui, QtCore, QtWidgets
# QtCore.qInstallMsgHandler(lambda *args: None)
import pyqtgraph as pg
import numpy as np
import copy
from ui.field_registration import Ui_field_registration
from spatial_registration_module import registration_dft_slice
from spatial_registration_module import rotatePoint


def qt_image_to_array(img, share_memory=False):
    """ Creates a numpy array from a QImage.

        If share_memory is True, the numpy array and the QImage is shared.
        Be careful: make sure the numpy array is destroyed before the image,
        otherwise the array will point to unreserved memory!!
    """
    assert (img.format() == QtGui.QImage.Format.Format_RGB32 or \
            img.format() == QtGui.QImage.Format.Format_ARGB32_Premultiplied),\
        "img format must be QImage.Format.Format_RGB32, got: {}".format(
        img.format())

    img_size = img.size()
    buffer = img.constBits()

    # Sanity check
    n_bits_buffer = len(buffer) * 8
    n_bits_image = img_size.width() * img_size.height() * img.depth()
    assert n_bits_buffer == n_bits_image, \
        "size mismatch: {} != {}".format(n_bits_buffer, n_bits_image)

    assert img.depth() == 32, "unexpected image depth: {}".format(img.depth())

    # Note the different width height parameter order!
    arr = np.ndarray(shape=(img_size.height(), img_size.width(), img.depth() // 8),
                     buffer=buffer,
                     dtype=np.uint8)

    if share_memory:
        return arr
    else:
        return copy.deepcopy(arr)

def qt_pixmap_to_array(pixmap, share_memory=False):
    """ Creates a numpy array from a QPixMap.
        If share_memory is True, the numpy array and the QImage is shared.
        Be careful: make sure the numpy array is destroyed before the image,
        otherwise the array will point to unreserved memory!!
    """
    assert isinstance(pixmap, QtGui.QPixmap), "pixmap must be a QtGui.QImage object"
    img_size = pixmap.size()
    img = pixmap.toImage()
    buffer = img.constBits()

    # Sanity check
    n_bits_buffer = len(buffer) * 8
    n_bits_image = img_size.width() * img_size.height() * img.depth()
    assert n_bits_buffer == n_bits_image, \
        "size mismatch: {} != {}".format(n_bits_buffer, n_bits_image)

    assert img.depth() == 32, "unexpected image depth: {}".format(img.depth())

    # Note the different width height parameter order!
    arr = np.ndarray(shape=(img_size.height(), img_size.width(), img.depth() // 8),
                     buffer=buffer,
                     dtype=np.uint8)

    if share_memory:
        return arr
    else:
        return copy.deepcopy(arr)



def mdi_field_imreg_show(self):
    """
    Launching the field registration tool
    :param self:
    :return:
    """
    self.mdi_field_registration_widget = MdiFieldImreg(self)
    self.mdi_field_registration_widget.logMessage_sig.connect(self.dock_log.add_event)
    self.mdi_field_registration_widget.statusMessage_sig.connect(self.statusUpdate)
    self.mdi_field_registration_widget.progressUpdate_sig.connect(self.progressUpdate)
    self.dock_properties.grid_settings.addWidget(self.mdi_field_registration_widget)
    self.mdi_field_widget.field.rectangleSelected_sig.connect(self.mdi_field_registration_widget.set_reference_zone)
    self.mdi_field_widget.setEnabled(True)

    self.dock_properties.stackedWidget.setCurrentIndex(1)

    # // enable pipeline selection
    self.dock_pipe.setEnabled(True)
    self.dock_properties.show()
    self.mdi_field_registration_widget.show()

class MdiFieldImreg(QtWidgets.QDialog, Ui_field_registration):
    """
    class around the GUI for image registration based on DFT-based input
    """
    statusMessage_sig = QtCore.Signal(str)
    progressUpdate_sig = QtCore.Signal(float)
    logMessage_sig = QtCore.Signal(dict)

    def __init__(self, parent):
        """
        Initialize function
        :param parent:
        :param current_group:
        """
        super(MdiFieldImreg, self).__init__(parent)
        self.setupUi(self)
        self._parent = parent
        self.roi_active = False
        self.target_frame = np.zeros((0,0))
        self.target_outline = [0,0,0,0,0,0]
        self.reference_frame = np.zeros((0, 0))
        self.reference_outline = [0,0,0,0,0,0]
        self.setMinimumWidth(self._parent.dock_properties.size().width() - 40)
        self.connect_slots()

    def connect_slots(self):
        """
        Connect all slots within the software
        :return:
        """
        self.bt_registration.clicked.connect(self.dft_imreg2)
        self.bt_add_ref.clicked.connect(self.add_reference)
        self.bt_add_target.clicked.connect(self.add_target)
        self.buttonBox.accepted.connect(self.accept_dialog)
        self.buttonBox.rejected.connect(self.reject_dialog)

    def add_target(self):
        """
        Adds the target slice. This can be from an image in the workspace, or from a dataset
        :return:
        """
        self.target_image = self._parent.mdi_field_widget.update_field_current
        current_loc = self._parent.mdi_field_widget.update_field_current.loc
        if isinstance(current_loc, dict):
            self.target_attrs = current_loc
            self.target_frame = qt_image_to_array(self.target_image.pixmap.toImage())
            # // grayscale conversion
            self.target_frame = np.dot(self.target_frame[..., :3], [0.299, 0.587, 0.114])
            self.ent_target.setText(current_loc["Path"])
        elif isinstance(current_loc, Group):
            dset = current_loc.get_dataset()
            self.target_attrs = dset.attrs
            # // grab the array and the positions of the outline
            self.target_frame = np.atleast_2d(
                self._parent.position_tracker.retrieve_slice(dset, ["spatialx", "spatialy"],
                                                            channel_spec=1)).astype(
                float)
            self.ent_target.setText(dset.name)
        else:
            raise ValueError("Unexpected type: {}".format(type(current_loc)))

    def add_reference(self):
        """
        Adds the reference slice. This can be from an image in the workspace, or from a dataset
        :return:
        """
        self.reference_image = self._parent.mdi_field_widget.update_field_current
        current_loc = self._parent.mdi_field_widget.update_field_current.loc
        if isinstance(current_loc, dict):
            self.reference_attrs = current_loc
            self.reference_frame = qt_image_to_array(self.reference_image.pixmap.toImage())
            # // grayscale conversion
            self.reference_frame = np.dot(self.reference_frame[..., :3], [0.299, 0.587, 0.114])
            self.ent_ref.setText(current_loc["Path"])
        else:
            raise ValueError("Unexpected type: {}".format(type(current_loc)))

    @QtCore.Slot()
    def set_reference_zone(self, x0, y0, x1, y1):
        """
        Sets the coordinates of the rectangle selection within the reference zone

        :param x0: left-top corner x coordinate
        :param y0: left-top corner y coordinate
        :param x1: right-bottom corner x coordinate
        :param y1: right-bottom corner y coordinate
        :return:
        """
        print(x0, y0, x1, y1)
        if self.roi_active:
            self._parent.mdi_field_widget.field.removeItem(self.roi)

        self.roi = pg.ROI([x0, y0], [x1-x0, y1-y0], pen=(0, 9), movable=False)
        self._parent.mdi_field_widget.field.addItem(self.roi)
        self.reference_sub_outline = (x0, x1, y0, y1)
        self.roi_active = True

    def set_auto_reference_zone(self, image, scale=1.1):
        """
        This method is meant to increase a zone around the current image, in order to constrain the region of the
        reference image in which a match will be found
        :param pos1:
        :param pos2:
        :param scale:
        :return:
        """
        pass

    def accept_dialog(self):
        try:
            if self.move_box in self._parent.mdi_field_widget.field.allChildren():
                self._parent.mdi_field_widget.field.removeItem(self.move_box)
            self.update_field_current.setBorder(None)
        except:
            pass
        self.accept()

    def reject_dialog(self):
        clear_preview(self._parent, "signaltrace")
        self.reject()

    def closeEvent(self, event):
        try:
            if self.move_box in self._parent.mdi_field_widget.field.allChildren():
                self._parent.mdi_field_widget.field.removeItem(self.move_box)
            self.update_field_current.setBorder(None)
        except:
            pass

    def restore(self):
        if 'Outline_r' in self.dset.attrs.keys():
            outl = self.dset.attrs['Outline_r']
            self.dset.attrs['Outline'] = outl
            if 'Rotation_r' in self.dset.attrs.keys():
                self.dset.attrs['Rotation'] = self.dset.attrs[
                    'Rotation_r']
            else:
                self.dset.attrs['Rotation'] = 0

        # // reset the field box
        if outl[0] != outl[1]:
            if self._parent.axis[0] > -1:
                x_aspect = self.dset.shape[self._parent.axis[0]] / abs(outl[0] - outl[1])
            else:
                x_aspect = 1
        else:
            x_aspect = 1
        if outl[2] != outl[3]:
            if self._parent.axis[1] > -1:
                y_aspect = self.dset.shape[self._parent.axis[1]] / abs(outl[2] - outl[3])
            else:
                y_aspect = 1
        else:
            y_aspect = 1

        s = list(self.update_field_current._scale)
        self.update_field_current.scale(1 / s[0], 1 / s[1])

        # // rotate the dataset if a rotation transformation is required]
        if 'Rotation_r' in self.dset.attrs.keys():
            rot = self.dset.attrs['Rotation_r']
            self.update_field_current.rotate(-rot)
            self.update_field_current._rot = self.update_field_current._rot - rot
            self.dset.attrs['Rotation'] = self.move_box.angle()
        else:
            self.update_field_current._rot = 0.0
            self.dset.attrs['Rotation'] = 0.0

        self.update_field_current.scale(1 / x_aspect, 1 / y_aspect)
        self.update_field_current._scale = (1 / x_aspect, 1 / y_aspect)

        # // translates the dataset in the field view based on the left corner coordinate in the outline
        self.update_field_current.setPos(pg.Point(outl[0], outl[2]))
        # self._parent.mdi_field_widget.update_field()

    def dft_imreg2(self, downscale_target=True):
        """

        :return:
        """
        # // determine the image registration transform
        angle = (0,20)
        scale = (1,0.3)
        tx = (0,50)
        ty = (0,50)

        target_outline = self.target_attrs["Outline"].copy()
        # // extract the rectangular zone from the reference image, based on the existing coordinates
        # of the target image by adding a ROI
        if self.roi_active == False:
            # // current outline of the target frame
            target_x_size = target_outline[1]-target_outline[0]
            target_y_size = target_outline[3] - target_outline[2]
            target_outline[0] = target_outline[0] - 0.1 * target_x_size
            target_outline[1] = target_outline[1] + 0.1 * target_x_size
            target_outline[2] = target_outline[2] - 0.1 * target_y_size
            target_outline[3] = target_outline[3] + 0.1 * target_y_size

            self.roi = pg.ROI([target_outline[0], target_outline[2]], [target_outline[1] - target_outline[0], target_outline[3] - target_outline[2]], pen=(0, 9), movable=False)
            self._parent.mdi_field_widget.field.addItem(self.roi)
            self.reference_sub_outline = (target_outline[0], target_outline[1], target_outline[2], target_outline[3])
            self.roi_active = True
        else:
            # // rotate the ROI so it matches the rotation of the image
            print(434243234)

        # // calculate new target size
        target_x_size = target_outline[1] - target_outline[0]
        target_y_size = target_outline[3] - target_outline[2]

        self.reference_sub_frame = self.roi.getArrayRegion(self.reference_frame, self.reference_image)
        self.target_sub_frame = self.roi.getArrayRegion(self.target_frame, self.target_image)
        import cv2
        cv2.imwrite(r"C:\Users\admi_n\Downloads\projection_test\target_sub_frame.jpg", self.target_sub_frame)
        # // downscale the target frame to the resolution of the reference frame (in order to have comparable
        # resolution across the images ( resolution in pixel per micron). Having a greater resolution than the
        # reference target won't really help in getting a more accurate registration.
        pixel_scale_ref = self.reference_sub_frame.shape[0] / (
                    self.reference_sub_outline[1] - self.reference_sub_outline[0])
        pixel_scale_target = self.target_sub_frame.shape[0] / (target_outline[1] - target_outline[0])

        import scipy.ndimage.interpolation as ndii
        if downscale_target:
            self.target_zoom_frame=ndii.zoom(self.target_sub_frame, (pixel_scale_ref/pixel_scale_target))
        else:
            # Alternatively, upscale the reference sub frame to the resolution of the target. Warning; this may
            # increase compute time.
            self.reference_sub_frame = ndii.zoom(self.reference_sub_frame, (pixel_scale_target/pixel_scale_ref))
            self.target_zoom_frame = self.target_sub_frame
        import cv2
        cv2.imwrite(r"C:\Users\admi_n\Downloads\projection_test\target_sub_frame_downscaled.jpg", self.target_zoom_frame)

        print("shapes:", self.target_zoom_frame.shape, self.reference_sub_frame.shape)
        # // match the shape of reference (template) frame and current frame (image to be transformed
        if self.target_zoom_frame.shape != self.reference_sub_frame.shape:
            # // pad on the right side
            x_diff = self.reference_sub_frame.shape[0]-self.target_zoom_frame.shape[0]
            y_diff = self.reference_sub_frame.shape[1] - self.target_zoom_frame.shape[1]
            left_pad = x_diff//2
            right_pad = x_diff - left_pad
            top_pad = y_diff//2
            bottom_pad = y_diff - top_pad
            if x_diff>=0 and y_diff>=0:
                self.target_zoom_frame = np.pad(self.target_zoom_frame, ((left_pad,right_pad), (top_pad, bottom_pad)), "edge")
            else:
                self.target_zoom_frame = self.target_zoom_frame[:self.reference_sub_frame.shape[0], :self.reference_sub_frame.shape[1]]
        else:
            print("no padding required")
        print("shapes:", self.target_zoom_frame.shape, self.reference_sub_frame.shape)
        # self.target_image.setImage(self.target_frame)
        import cv2
        cv2.imwrite(r"C:\Users\admi_n\Downloads\projection_test\reference_sub_frame.jpg", self.reference_sub_frame)

        import cv2
        cv2.imwrite(r"C:\Users\admi_n\Downloads\projection_test\target_zoom_frame_padded.jpg", self.target_zoom_frame)

        # // get different frames (taking into account the scaling)
        
        vector_dict = registration_dft_slice(self.reference_sub_frame, self.target_zoom_frame, scale=scale, angle=angle,
                                                tx=tx, ty=ty, iterations=10, \
                                                display=False,  progressbar=None,
                                                display_window=None)

        if vector_dict["success"]:
            net_rotation_degrees = -vector_dict["angle"]
            full_rotation_degrees = self.target_attrs["Rotation"] + net_rotation_degrees
            # // note that the scale factor is calculated under the assumption that the images have the same pixel
            # // size, which is not the case
            self.scale_factor = vector_dict["scale"]
            # // correct for pixel size to calculate the correct scale factor
            if downscale_target:
                pass
            else:
                self.scale_factor *= (pixel_scale_ref/pixel_scale_target)

        image_projection = False
        if image_projection:
            s = list(self.target_image._scale)
            self.target_image.scale(1 / s[0], 1 / s[1])
            self.target_image.rotate(-self.target_attrs["Rotation"])
            # self.target_attrs["Rotation"] = 0

            # // translation
            # arr = ird.imreg.transform_img_dict(self.target_zoom_frame, tdict=vector_dict, bgval=None, order=1, invert=False)
            # import cv2
            # cv2.imwrite(r"C:\Users\admi_n\Downloads\projection_test\crop_img.jpg", arr)
            # # QI = QtGui.QImage(arr.data, target_x_size, target_y_size, QtGui.QImage.Format_Mono)

            import imreg_dft as ird
            vector_dict["tvec"] *= (pixel_scale_target / pixel_scale_ref)
            arr = ird.imreg.transform_img_dict(self.target_sub_frame, tdict=vector_dict, bgval=None, order=1,
                                               invert=False)
            import cv2
            cv2.imwrite(r"C:\Users\admi_n\Downloads\projection_test\target_sub_frame_transformed.jpg", arr)
            self.target_image.setPixmap(QtGui.QPixmap(r"C:\Users\admi_n\Downloads\projection_test\target_sub_frame_transformed.jpg"))
            self.target_image.setPos(self.roi.pos())
            self.target_image.scale(target_x_size / arr.shape[0], target_y_size / arr.shape[1])
        else:
            import imreg_dft as ird
            arr = ird.imreg.transform_img_dict(self.target_sub_frame, tdict=vector_dict, bgval=None, order=1,
                                               invert=False)
            import cv2
            cv2.imwrite(r"C:\Users\admi_n\Downloads\projection_test\target_sub_frame_transformed.jpg", arr)

            # self.target_attrs["Rotation"] = full_rotation_degrees

            # // translation
            # self.scale_factor *= self.reference_image._scale[0] / self.target_image._scale[0]
            # self.scale_factor *= (pixel_scale_ref / pixel_scale_target)

            print("tvec: ", vector_dict["tvec"])
            print("angle: ", vector_dict["angle"], self.target_attrs["Rotation"])
            print("scale: ", vector_dict["scale"])
            print("pixel_scale_target", pixel_scale_target)
            print("pixel_scale_ref", pixel_scale_ref)
            print(self.reference_image._scale, self.target_image._scale)

            # // correct for the rescaling of the target
            self.scale_factor *= (pixel_scale_ref / pixel_scale_target)
            # // correct for the difference in scale between the reference and the target
            # self.scale_factor *= self.reference_image._scale[0]/self.target_image._scale[0]
            print("scalefactor: ", self.scale_factor)

            s = list(self.target_image._scale)
            self.target_image.scale(1 / s[0], 1 / s[1])
            self.target_image.rotate(net_rotation_degrees)
            self.target_image.scale(self.scale_factor , self.scale_factor )
            self.target_image._scale = (self.scale_factor , self.scale_factor )

            # // the correction of the position for the rotation is needed.
            target_outline = self.target_attrs["Outline"].copy()
            pos1 = QtCore.QPointF((target_outline[1] - target_outline[0]) / 2, (target_outline[3] - target_outline[2]) / 2)
            pos2 = rotatePoint(centerPoint=(0.0, 0.0),
                                         point=((target_outline[1] - target_outline[0]) / 2, (target_outline[3] - target_outline[2]) / 2),
                                         angle=self.target_attrs["Rotation"])
            pos3 = rotatePoint(centerPoint=(0.0, 0.0),
                               point=pos2,
                               angle=-vector_dict["angle"])
            rotation_correction = (QtCore.QPointF(pos3[0], pos3[1]) - QtCore.QPointF(pos2[0], pos2[1]))
            self.target_image.setPos(self.target_image.pos() - rotation_correction)

            # // the correction is basically the distance between the image pos (left-top-corner) and the center, with a fraction of the scaling
            scale_position_correction = (1-vector_dict["scale"])*(QtCore.QPointF(pos3[0], pos3[1]))
            print("scale_position_correction:", scale_position_correction)
            self.target_image.setPos(self.target_image.pos() + scale_position_correction)

            # // convert tvec in pixel in the target image
            if downscale_target:
                vector_dict["tvec"] *= pixel_scale_target*(pixel_scale_ref / pixel_scale_target)
            # print(vector_dict["tvec"])
            # // convert shift in pixel into micron

            translation_component = QtCore.QPointF(vector_dict["tvec"][1], vector_dict["tvec"][0])
            print("translation_component",translation_component)
            self.target_image.setPos(self.target_image.pos() + translation_component)
        return vector_dict

def main():
    app.setQuitOnLastWindowClosed(True)
    w = MdiFieldImreg(main)
    w.logMessage_sig.connect(main.dock_log.add_event)
    w.statusMessage_sig.connect(main.statusUpdate)
    w.progressUpdate_sig.connect(main.progressUpdate)
    main.dock_properties.grid_settings.addWidget(w)
    init_preview(main)
    main.mdi_field_widget.setEnabled(True)
    main.dock_properties.stackedWidget.setCurrentIndex(1)
    # // enable pipeline selection
    main.dock_pipe.setEnabled(True)
    main.dock_properties.show()
    main.mdi_field_widget.tblItemClicked(1, 0)
    w.add_target()
    main.mdi_field_widget.tblItemClicked(0, 0)
    main.mdi_field_widget.field.rectangleSelected_sig.connect(w.set_reference_zone)
    w.add_reference()
    # w.set_reference_zone(48489.8606844214, 49002.94295666035, 49298.44732932892, 49698.63259831663)
    w.dft_imreg2()
    w.exec_()
    app.closeAllWindows()
    app.quit()

if __name__=='__main__':
    main()