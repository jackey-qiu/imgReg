# -*- coding: utf-8 -*-
import numpy as np
import cv2
from matplotlib import pyplot as plt
from spatial_registration_module import registration_dft_slice

def imreg_dft():
    angle = [0.0, 5.0]
    scale = [1.0, 1.1]
    tx = [0, 10]
    ty = [float(self.ent_avg_ty.text()), float(self.ent_sigma_ty.text())]

    if self.rb_register_within_slice.isChecked() or self.rb_register_dsets_slice.isChecked():
        axis_x = self.ref_x[0]
        axis_y = self.ref_y[0]
        axis_z = self.ref_z[0]

        # axis_x,axis_y,axis_z=axis_x[0],axis_y[0],axis_z[0]
        if axis_z < axis_x:
            axis_x -= 1
        if axis_z < axis_y:
            axis_y -= 1

            # slice_ref = retrieve_slice_rev(self, [b'spatial'], [b'z'])
        slice_ref = [slice(None, None)] * len(self.ref_indices)
        slice_ref[self.ref_z[0]] = self.ref_indices[self.ref_z[0]]
        reference_frame = self.ref_node[tuple(slice_ref)]
        slice_target = [slice(None, None)] * len(self.target_indices)
        slice_target[self.target_z[0]] = self.target_indices[self.target_z[0]]
        current_frame = self.target_node[tuple(slice_target)]
        
        if self.ref_n[0] != None:
            channel_im0 = self.ref_indices[self.ref_n[0]]
            channel_axis_im0 = self.ref_n[0]
        else:
            channel_im0 = None
            channel_axis_im0 = None
        if self.ref_n[0] != None:
            channel_im1 = self.target_indices[self.target_n[0]]
            channel_axis_im1 = self.target_n[0]
        else:
            channel_im1 = None
            channel_axis_im1 = None

        a, vector_dict = registration_dft_slice(reference_frame, current_frame, channel_im0=channel_im0, \
                                                channel_im1=channel_im1, channel_axis_im0=channel_axis_im0, \
                                                channel_axis_im1=channel_axis_im1, scale=scale, angle=angle, tx=tx,
                                                ty=ty, iterations=int(self.ent_iter_imreg.text()), \
                                                display=False, quiet=False, simulation=False, progressbar=None,
                                                display_window=self.img0_imreg, vector_dict_out=True)
        return a, vector_dict

def run():
    img1 = cv2.imread(r'C:\Users\admi_n\Downloads\projection_test\test2.bmp',0)          # queryImage
    img2 = cv2.imread(r'C:\Users\admi_n\Downloads\projection_test\test1.bmp',0) # trainImage


    # Initiate ORB detector
    orb = cv2.ORB_create()

    # find the keypoints and descriptors with ORB
    kp1, des1 = orb.detectAndCompute(img1,None)
    kp2, des2 = orb.detectAndCompute(img2,None)

    # img1 = cv2.drawKeypoints(img1,kp1, None)
    # draw only keypoints location,not size and orientation
    # img3 = cv2.drawKeypoints(img1,kp1,img1,color=(0,255,0), flags=0)
    # cv2.imwrite('sift_keypoints.jpg',img1)

    # create BFMatcher object
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    # Match descriptors.
    matches = bf.match(des1,des2)

    # Sort them in the order of their distance.
    matches = sorted(matches, key = lambda x:x.distance)

    # Draw first 10 matches.
    img3 = cv2.drawMatches(img1,kp1,img2,kp2,matches[:15],None, flags=2)

    plt.imshow(img3),plt.show()


    sys.exit()

    # FLANN parameters
    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
    search_params = dict(checks=50)   # or pass empty dictionary

    flann = cv2.FlannBasedMatcher(index_params,search_params)

    matches = flann.knnMatch(des1,des2,k=2)

    # Need to draw only good matches, so create a mask
    matchesMask = [[0,0] for i in range(len(matches))]

    # ratio test as per Lowe's paper
    for i,(m,n) in enumerate(matches):
        if m.distance < 0.7*n.distance:
            matchesMask[i]=[1,0]

    draw_params = dict(matchColor = (0,255,0),
                       singlePointColor = (255,0,0),
                       matchesMask = matchesMask,
                       flags = 0)

    img3 = cv2.drawMatchesKnn(img1,kp1,img2,kp2,matches,None,**draw_params)

    plt.imshow(img3,),plt.show()