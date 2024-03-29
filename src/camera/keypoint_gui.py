import cv2
import yaml
import numpy as np
import distance_estimation
import os
import argparse
from grab_image import grab_image
import copy
import sys

class Rect:
    x = None
    y = None
    w = None
    h = None

def get_palm_dist_calib_name(shorthand : str):
    if shorthand == 'Th_TM':
        return 'thumb'
    if shorthand == 'Ind_MCP':
        return 'index'
    if shorthand == 'Mid_MCP':
        return 'middle'
    if shorthand == 'Ring_MCP':
        return 'ring'
    if shorthand == 'Lit_MCP':
        return 'little'
    raise ValueError(f'Unknown shorthand: {shorthand}')


class Circ:
    def __init__(self, x, y, winWidth, winHeight) -> None:
        self.x = x
        self.y = y
        self.radius = 10
        wname = 'circle'
        self.active = False

        self.keepWithin = Rect()
        self.keepWithin.x = 0
        self.keepWithin.y = 0
        self.keepWithin.w = winWidth
        self.keepWithin.h = winHeight

    def clicked_inside(self, x, y):
        return (x - self.x)**2 + (y - self.y)**2 < self.radius**2

class Prog:
    def __init__(self, image, cam_calibration) -> None:
        self.source = image
        self.image  = self.source.copy()
        self.cam_calib = cam_calibration

        self.keypoint_names = [
            "palm_ref0",  "palm_ref1",
            "Th_TM",      "Ind_MCP",    "Mid_MCP", "Ring_MCP", "Lit_MCP", 
            "Th_MCP",     "Th_IP",      "Th_TIP",
            "Ind_PIP",    "Ind_DIP",    "Ind_TIP",
            "Mid_PIP",    "Mid_DIP",    "Mid_TIP",
            "Ring_PIP",   "Ring_DIP",   "Ring_TIP",
            "Lit_PIP", "Lit_DIP", "Lit_TIP",
        ]

        self.keypoints = {}
        self.keypoint_idx = 0
        self.current_circle = None
        self.last_kp_active = False

        with open(os.path.join(os.path.dirname(__file__), '..', 'default_calib.yaml'), 'r') as f:
            self.calib_values = yaml.safe_load(f)

        self.defalt_calib = copy.deepcopy(self.calib_values)

        self.dragging = None

        self.wName = 'Select Hand Keypoints'
        cv2.namedWindow(self.wName, cv2.WINDOW_GUI_NORMAL)
        cv2.setMouseCallback(self.wName, self.cb_func)

        self.palm = None
        self.show_distances = False
        self.saved = False
        self.save_path = ''

        self.done = False
        self.instructions = [
            f"Double-Click LMB to Set the Next Keypoint ({self.keypoint_names[self.keypoint_idx]})",
            "You Can Drag a Keypoint with RMB to Reposition it",
            "Press `d` to toggle distance output",
        ]
        self.clearCanvasNDraw()
        while not self.done:
            if not self.last_kp_active:
                self.instructions = [
                    f"Double-Click LMB to Set the Next Keypoint ({self.keypoint_names[self.keypoint_idx]})",
                    "You Can Drag a Keypoint with RMB to Reposition it",
                    "Press `d` to toggle distance output",
                ]
            else:
                self.instructions = [
                    "You Can Drag a Keypoint with RMB to Reposition it",
                    "Press `d` to toggle distance output"
                ]
            key = cv2.waitKey(1) & 0xFF
            if key == ord("d"):
                print("Pressed d!")
                self.show_distances = not self.show_distances
                self.clearCanvasNDraw()
            if key == ord(" ") and self.keypoint_idx > 19:
                self.save_config()
            if key == ord("q"):
                print("Pressed Q to quit")
                self.done = True

        print("Done!")

    def cb_func(self, event, x, y, flags, bla):
        
        if event == cv2.EVENT_LBUTTONDBLCLK:
            self.current_circle = self.keypoints[self.keypoint_names[self.keypoint_idx]] = Circ(x, y, self.source.shape[1], self.source.shape[0])
            print(f"Created keypoint for {self.keypoint_names[self.keypoint_idx]} at {x},{y}")
            self.keypoint_idx = min(self.keypoint_idx, len(self.keypoint_names)-1)
            if self.keypoint_idx == len(self.keypoint_names) - 1:
                self.last_kp_active = True
            else:
                self.keypoint_idx += 1

        if event == cv2.EVENT_RBUTTONDOWN:
            print("Started dragging...")
            for name,circle in self.keypoints.items(): # Find clicked circle
                if circle.clicked_inside(x, y):
                    self.dragging = circle
                    self.current_circle = circle
                    break
        
        if event == cv2.EVENT_RBUTTONUP:
            print("Finished dragging...")
            self.dragging = None

        if event == cv2.EVENT_MOUSEMOVE:
            if self.dragging is not None:
                self.mouseMove(x, y)
                self.saved = False

        self.clearCanvasNDraw()

    def mouseMove(self, x, y):
        x = max(0, min(self.image.shape[1], x))
        y = max(0, min(self.image.shape[0], y))

        self.dragging.x = x
        self.dragging.y = y

    def clearCanvasNDraw(self):
        self.image  = self.source.copy()

        font = cv2.FONT_HERSHEY_COMPLEX_SMALL
        fontsize_keypoints = 0.8
        fontsize_dists     = 0.5
        fontsize_inst      = 0.7
        font_thickness     = 1

        text_above = 1

        keypoint_list = list(self.keypoints.items())
        MCPs = []
        for idx,(name,circle) in enumerate(self.keypoints.items()):

            if circle == self.current_circle:
                cv2.circle(self.image, (circle.x, circle.y), circle.radius//2, (0, 0, 255), 2)

            if idx == 1:
                cv2.line(self.image, (keypoint_list[0][1].x, keypoint_list[0][1].y), (circle.x, circle.y), (0, 255, 0), 2)

            # Connect PIP to MCP, DIP to PIP, and TIP to DIP
            if len(MCPs) == 5 and ('MCP' not in name or name == 'Th_MCP'):
                if name == 'Th_MCP':
                    ref = MCPs[0]
                elif name == 'Ind_PIP':
                    ref = MCPs[1]
                elif name == 'Mid_PIP':
                    ref = MCPs[2]
                elif name == 'Ring_PIP':
                    ref = MCPs[3]
                elif name == 'Lit_PIP':
                    ref = MCPs[4]
                else:
                    ref = keypoint_list[idx - 1][1]

                cv2.line(self.image, (ref.x, ref.y), (circle.x, circle.y), (255, 255, 255), 2)

                if self.show_distances:
                    text = f"{distance_estimation.estimate_distance((ref.x, ref.y), (circle.x, circle.y), self.cam_calib)*100:2.2f}cm"
                    textsize, _ = cv2.getTextSize(text, font, fontsize_dists, font_thickness)
                    cv2.putText(
                        self.image,
                        text,
                        (circle.x - (circle.x - ref.x)//2 - textsize[0]//2, circle.y - (circle.y - ref.y)//2 - textsize[1]//2),
                        font, 
                        fontsize_dists,
                        (0, 0, 255),
                        font_thickness,
                        cv2.LINE_AA
                    )

            
            # Connect MCPs and Palm refs to polygon
            if name == 'Th_TM':
                cv2.line(self.image, (keypoint_list[1][1].x, keypoint_list[1][1].y), (circle.x, circle.y), (0, 255, 0), 2)
            if name != 'Th_MCP' and ('MCP' in name or name == 'Th_TM'):
                if self.show_distances and self.palm is not None:
                    cv2.line(self.image, (self.palm[0], self.palm[1]), (circle.x, circle.y), (57, 127, 253), 2)
                    text = f"{distance_estimation.estimate_distance(self.palm, (circle.x, circle.y), self.cam_calib)*100:2.2f}cm"
                    textsize, _ = cv2.getTextSize(text, font, fontsize_dists, font_thickness)
                    cv2.putText(
                        self.image,
                        text,
                        (circle.x - (circle.x - self.palm[0])//2 - textsize[0]//2, circle.y - (circle.y - self.palm[1])//2 - textsize[1]//2),
                        font, 
                        fontsize_dists,
                        (0, 0, 255),
                        font_thickness,
                        cv2.LINE_AA
                    )
                
                if self.palm is not None:
                    proj = distance_estimation.project_point_on_line(
                        np.array((keypoint_list[0][1].x, keypoint_list[0][1].y)),
                        np.array((keypoint_list[1][1].x, keypoint_list[1][1].y)),
                        np.array((circle.x, circle.y))
                    ).astype(np.int16)
                    x_off = distance_estimation.estimate_distance(self.palm, proj, self.cam_calib)
                    z_off = distance_estimation.estimate_distance((circle.x, circle.y), proj, self.cam_calib)
                    if proj[1] < self.palm[1]:
                        x_off *= -1

                    c_name = get_palm_dist_calib_name(name)
                    self.calib_values['palm_link_distances'][c_name]['z'] = z_off
                    self.calib_values['palm_link_distances'][c_name]['x'] = x_off


                if len(MCPs) > 0:
                    cv2.line(self.image, (MCPs[-1].x, MCPs[-1].y), (circle.x, circle.y), (0, 255, 0), 2)
                    if name == 'Lit_MCP':
                        cv2.line(self.image, (keypoint_list[0][1].x, keypoint_list[0][1].y), (circle.x, circle.y), (0, 255, 0), 2)
                MCPs.append(circle)

        for idx,(name,circle) in enumerate(self.keypoints.items()):
            # Make circle and name as last, to be on top of lines
            color = (255, 0, 0)
            cv2.circle(self.image, (circle.x, circle.y), circle.radius, (0,  255, 0), 3)
            textsize, _ = cv2.getTextSize(name, font, fontsize_keypoints, font_thickness)
            if 'MCP' in name or 'PIP' in name:
                text_above = 1
            cv2.putText(
                self.image,
                name,
                (circle.x - textsize[0]//2, circle.y - text_above * (textsize[1]//2 + 15)),
                font,
                fontsize_keypoints,
                color,
                font_thickness,
                cv2.LINE_AA
            )
            text_above = text_above * -1

            # Make projection of palm_link
            if name == 'Mid_MCP':
                self.palm = palm = distance_estimation.project_point_on_line(
                    np.array((keypoint_list[0][1].x, keypoint_list[0][1].y)),
                    np.array((keypoint_list[1][1].x, keypoint_list[1][1].y)),
                    np.array((circle.x, circle.y))
                ).astype(np.uint16)

                textsize, _ = cv2.getTextSize('palm_link', font, fontsize_keypoints, font_thickness)
                cv2.putText(
                    self.image,
                    'palm_link',
                    (palm[0] - textsize[0]//2, palm[1] - textsize[1]//2 - 10),
                    font,
                    fontsize_keypoints,
                    (255, 0, 0),
                    font_thickness,
                    cv2.LINE_AA
                )
                cv2.circle(self.image, (palm[0], palm[1]), circle.radius, (255, 0, 0), 10)

        x0 = 25 
        y0 = 25 
        if not self.last_kp_active:
            cv2.rectangle(self.image, (0, 0), (600, 30*len(self.instructions)), (0,0,0), -1)
        else:
            cv2.rectangle(self.image, (0, 0), (800, 30*(1+len(self.instructions))), (0,0,0), -1)

        for inst in self.instructions:
            cv2.putText(self.image, inst, (x0, y0), font, fontsize_inst, (255, 255, 255), font_thickness, cv2.LINE_AA)
            y0 += 22

        if self.last_kp_active:
            cv2.putText(self.image, "Once you are happy with the keypoints, press space to generate a calibration file!", (x0, y0), font, fontsize_inst, (0, 0, 255), font_thickness, cv2.LINE_AA)

        if self.save_path != '':
            if self.saved:
                cv2.putText(self.image, f"Saved Config to: {self.save_path}", (50, self.image.shape[0] - 100), font, fontsize_inst, (0, 0, 255), font_thickness, cv2.LINE_AA)
            else:
                cv2.putText(self.image, f"Unsaved changes!", (50, self.image.shape[0] - 100), font, fontsize_inst, (0, 0, 255), font_thickness, cv2.LINE_AA)

        cv2.imshow(self.wName, self.image)


    def save_config(self):

        thumb  = dict()
        index  = dict()
        middle = dict()
        ring   = dict()
        little = dict()

        scales = {}

        tm  = self.keypoints["Th_TM"]
        mcp = self.keypoints["Th_MCP"]
        ip  = self.keypoints["Th_IP"]
        tip = self.keypoints["Th_TIP"]

        thumb["proximal"] = distance_estimation.estimate_distance((tm.x, tm.y), self.palm, self.cam_calib)
        thumb["middle"]   = distance_estimation.estimate_distance((ip.x, ip.y), (mcp.x, mcp.y), self.cam_calib)
        thumb["distal"]   = distance_estimation.estimate_distance((tip.x, tip.y), (ip.x, ip.y), self.cam_calib)

        scales['thumb']   = {k: thumb[k]/default for k, default in self.defalt_calib['thumb'].items()}

        mcp = self.keypoints["Ind_MCP"]
        pip = self.keypoints["Ind_PIP"]
        dip = self.keypoints["Ind_DIP"]
        tip = self.keypoints["Ind_TIP"]

        index["proximal"] = distance_estimation.estimate_distance((pip.x, pip.y), (mcp.x, mcp.y), self.cam_calib)
        index["middle"]   = distance_estimation.estimate_distance((dip.x, dip.y), (pip.x, pip.y), self.cam_calib)
        index["distal"]   = distance_estimation.estimate_distance((tip.x, tip.y), (dip.x, dip.y), self.cam_calib)

        scales['index']   = {k: index[k]/default for k, default in self.defalt_calib['index'].items()}

        middle_mcp = mcp = self.keypoints["Mid_MCP"]
        pip = self.keypoints["Mid_PIP"]
        dip = self.keypoints["Mid_DIP"]
        tip = self.keypoints["Mid_TIP"]

        middle["proximal"] = distance_estimation.estimate_distance((pip.x, pip.y), (mcp.x, mcp.y), self.cam_calib)
        middle["middle"]   = distance_estimation.estimate_distance((dip.x, dip.y), (pip.x, pip.y), self.cam_calib)
        middle["distal"]   = distance_estimation.estimate_distance((tip.x, tip.y), (dip.x, dip.y), self.cam_calib)

        scales['middle']   = {k: middle[k]/default for k, default in self.defalt_calib['middle'].items()}

        mcp = self.keypoints["Ring_MCP"]
        pip = self.keypoints["Ring_PIP"]
        dip = self.keypoints["Ring_DIP"]
        tip = self.keypoints["Ring_TIP"]

        ring["proximal"] = distance_estimation.estimate_distance((pip.x, pip.y), (mcp.x, mcp.y), self.cam_calib)
        ring["middle"]   = distance_estimation.estimate_distance((dip.x, dip.y), (pip.x, pip.y), self.cam_calib)
        ring["distal"]   = distance_estimation.estimate_distance((tip.x, tip.y), (dip.x, dip.y), self.cam_calib)

        scales['ring']   = {k: ring[k]/default for k, default in self.defalt_calib['ring'].items()}

        mcp = self.keypoints["Lit_MCP"]
        pip = self.keypoints["Lit_PIP"]
        dip = self.keypoints["Lit_DIP"]
        tip = self.keypoints["Lit_TIP"]

        little["proximal"] = distance_estimation.estimate_distance((pip.x, pip.y), (mcp.x, mcp.y), self.cam_calib)
        little["middle"]   = distance_estimation.estimate_distance((dip.x, dip.y), (pip.x, pip.y), self.cam_calib)
        little["distal"]   = distance_estimation.estimate_distance((tip.x, tip.y), (dip.x, dip.y), self.cam_calib)

        scales['little']   = {k: little[k]/default for k, default in self.defalt_calib['little'].items()}

        scales['palm'] = {k: self.calib_values['palm_link_distances']['little'][k]/self.defalt_calib['palm_link_distances']['little'][k] for k in ['z','x']}


        self.calib_values['thumb']     = thumb
        self.calib_values['index']     = index 
        self.calib_values['middle']    = middle 
        self.calib_values['ring']      = ring 
        self.calib_values['little']    = little
        self.calib_values['scales']    = scales

        with open('handcalib.yaml', 'w') as f:
            yaml.dump(self.calib_values, f, default_flow_style=False)
            self.save_path = os.path.abspath(f.name)
            self.saved = True
            print(f"Saved calib under path: {self.save_path}")

if __name__ == '__main__':
    dirname = os.path.dirname(__file__)
    default_calib = os.path.normpath(os.path.join(dirname, os.pardir, 'calibration.npy'))

    parser = argparse.ArgumentParser()

    ex_group = parser.add_mutually_exclusive_group()
    ex_group.add_argument('-d', '--device', type=int, help="Camera device number (defaults to 0)", default=0)
    ex_group.add_argument('-i', '--image', help="Path to image to load")
    parser.add_argument('-c', '--calibration', type=str, help=f"Path to camera calibration (defaults to {default_calib})", default=default_calib)

    args = parser.parse_args()
    print(args)

    if not os.path.isfile(args.calibration):
        print(f'[FATAL ERROR]: calibration file "{args.calibration}" does not exists or is not a file!')
        sys.exit(-1)

    if args.image:
        print('Using image at: ', args.image)
        image = cv2.imread(args.image)
    else:
        image = grab_image(args.device)

    Prog(image, args.calibration)