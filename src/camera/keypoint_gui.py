import cv2
import numpy as np
import distance_estimation

class Rect:
    x = None
    y = None
    w = None
    h = None

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
    def __init__(self) -> None:
        self.source = cv2.imread('src/image_grab.png')
        self.image  = self.source.copy()

        self.keypoint_names = ["DEXMO_REF", "Th_MCP", "Ind_MCP", "Mid_MCP", "Ring_MCP", "Little_MCP", 
                               "Th_IP", "Th_TIP",
                               "Ind_PIP", "Ind_DIP", "Ind_TIP",
                               "Mid_PIP", "Mid_DIP", "Mid_TIP",
                               "Ring_PIP", "Ring_DIP", "Ring_TIP",
                               "Little_PIP", "Little_DIP", "Little_TIP"]
        self.keypoints = {}
        self.keypoint_idx = 0
        self.current_circle = None

        self.dragging = None

        self.wName = 'Select Hand Keypoints'
        cv2.namedWindow(self.wName, cv2.WINDOW_GUI_NORMAL)
        cv2.setMouseCallback(self.wName, self.cb_func)

        self.show_distances = False

        self.done = False
        while not self.done:
            if self.keypoint_idx <= 19:
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
            self.clearCanvasNDraw()
            key = cv2.waitKey(1) & 0xFF
            if key == ord("d"):
                print("Pressed d!")
                self.show_distances = not self.show_distances
                self.clearCanvasNDraw()
            if key == ord(" ") and self.keypoint_idx > 19:
                print("Saving config NYI!")

        print("Done!")
        cv2.waitKey(0)

    def cb_func(self, event, x, y, flags, bla):
        
        if event == cv2.EVENT_LBUTTONDBLCLK:
            self.current_circle = self.keypoints[self.keypoint_names[self.keypoint_idx]] = Circ(x, y, self.source.shape[1], self.source.shape[0])
            print(f"Created keypoint for {self.keypoint_names[self.keypoint_idx]} at {x},{y}")
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

        self.clearCanvasNDraw()

    def mouseMove(self, x, y):
        x = max(0, min(self.image.shape[1], x))
        y = max(0, min(self.image.shape[0], y))

        self.dragging.x = x
        self.dragging.y = y

    def clearCanvasNDraw(self):
        self.image  = self.source.copy()

        font = cv2.FONT_HERSHEY_SIMPLEX

        for idx,(name,circle) in enumerate(self.keypoints.items()):
            cv2.circle(self.image, (circle.x, circle.y), circle.radius, (0, 255, 0), 3)
            textsize, _ = cv2.getTextSize(name, font, 0.7, 2)
            cv2.putText(
                self.image,
                name,
                (circle.x - textsize[0]//2, circle.y - textsize[1]//2 - 10),
                font,
                0.7,
                (0, 255, 0),
                2
            )

            if circle == self.current_circle:
                cv2.circle(self.image, (circle.x, circle.y), circle.radius//2, (0, 0, 255), 2)

            MCPs = [6, 8, 11, 14, 17]
            ref = None
            if self.show_distances:
                if idx == 0:
                    continue
                if idx <= 5:
                    ref = self.keypoints[self.keypoint_names[0]]
                elif idx in MCPs:
                    ref = self.keypoints[self.keypoint_names[1+MCPs.index(idx)]]
                else:
                    ref = self.keypoints[self.keypoint_names[idx-1]]

                
            if ref is not None:
                cv2.line(self.image, (ref.x, ref.y), (circle.x, circle.y), (80, 0, 0), 2)
                text = f"{distance_estimation.estimate_distance((ref.x, ref.y), (circle.x, circle.y))*100:2.2f}cm"
                textsize, _ = cv2.getTextSize(text, font, 0.7, 2)
                cv2.putText(
                    self.image,
                    text,
                    (circle.x - (circle.x - ref.x)//2 - textsize[0]//2, circle.y - (circle.y - ref.y)//2 - textsize[1]//2),
                    font, 
                    0.7, 
                    (0, 0, 255),
                    2
                )

        x0 = 50 
        y0 = 50 
        if self.keypoint_idx > 19:
            cv2.rectangle(self.image, (0, 0), (1000, 50+30*(len(self.instructions))+1), (0,0,0), -1)
        else:
            cv2.rectangle(self.image, (0, 0), (700, 50+30*len(self.instructions)), (0,0,0), -1)

        for inst in self.instructions:
            cv2.putText(self.image, inst, (x0, y0), font, 0.7, (255, 255, 255), 2)
            y0 += 27

        if self.keypoint_idx > 19:
            cv2.putText(self.image, "Once you are happy with the keypoints, press space to generate a calibration file!", (x0, y0), font, 0.7, (0, 0, 255), 2)

        cv2.imshow(self.wName, self.image)


def run():
    pass

if __name__ == '__main__':
#    run()
    Prog()