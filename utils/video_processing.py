# video_processing.py
# Utility module to process videos and count people entering, leaving, and inside a space.

import cv2
import numpy as np
from collections import OrderedDict
from scipy.spatial import distance as dist

# ------------------ SIMPLE CENTROID TRACKER ------------------
class CentroidTracker:
    def __init__(self, maxDisappeared=40):
        self.nextObjectID = 0
        self.objects = OrderedDict()
        self.disappeared = OrderedDict()
        self.maxDisappeared = maxDisappeared

    def register(self, centroid):
        self.objects[self.nextObjectID] = centroid
        self.disappeared[self.nextObjectID] = 0
        self.nextObjectID += 1

    def deregister(self, objectID):
        if objectID in self.objects:
            del self.objects[objectID]
        if objectID in self.disappeared:
            del self.disappeared[objectID]

    def update(self, rects):
        if len(rects) == 0:
            for objectID in list(self.disappeared.keys()):
                self.disappeared[objectID] += 1
                if self.disappeared[objectID] > self.maxDisappeared:
                    self.deregister(objectID)
            return self.objects

        inputCentroids = []
        for (x1, y1, x2, y2) in rects:
            cX = int((x1 + x2) / 2.0)
            cY = int((y1 + y2) / 2.0)
            inputCentroids.append((cX, cY))

        if len(self.objects) == 0:
            for c in inputCentroids:
                self.register(c)
        else:
            objectIDs = list(self.objects.keys())
            objectCentroids = list(self.objects.values())

            D = dist.cdist(np.array(objectCentroids), np.array(inputCentroids))
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            usedRows, usedCols = set(), set()

            for (r, c) in zip(rows, cols):
                if r in usedRows or c in usedCols:
                    continue
                objectID = objectIDs[r]
                self.objects[objectID] = inputCentroids[c]
                self.disappeared[objectID] = 0
                usedRows.add(r)
                usedCols.add(c)

            unusedRows = set(range(0, D.shape[0])) - usedRows
            unusedCols = set(range(0, D.shape[1])) - usedCols

            for r in unusedRows:
                objectID = objectIDs[r]
                self.disappeared[objectID] += 1
                if self.disappeared[objectID] > self.maxDisappeared:
                    self.deregister(objectID)

            for c in unusedCols:
                self.register(inputCentroids[c])

        return self.objects

# ------------------ MAIN VIDEO PROCESSING FUNCTION ------------------
def analyze_video(video_path):
    """
    Analyze a video and return counts of people:
    {'in': int, 'out': int, 'inside': int}
    """
    in_count, out_count = 0, 0
    inside_ids = set()

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Cannot open video: " + video_path)

    tracker = CentroidTracker(maxDisappeared=40)
    prev_positions = {}

    # counting line: middle of frame
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
    LINE_Y = frame_height // 2

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30,30))
        rects = [(x, y, x+w, y+h) for (x, y, w, h) in faces]

        objects = tracker.update(rects)

        for objectID, centroid in objects.items():
            cX, cY = centroid
            current_side = 'above' if cY < LINE_Y else 'below'
            prev_side = prev_positions.get(objectID, current_side)

            if prev_side == 'below' and current_side == 'above':
                in_count += 1
                inside_ids.add(objectID)
            elif prev_side == 'above' and current_side == 'below':
                out_count += 1
                inside_ids.discard(objectID)

            prev_positions[objectID] = current_side

        # cleanup removed objects
        for old_id in list(prev_positions.keys()):
            if old_id not in objects:
                prev_positions.pop(old_id, None)
                inside_ids.discard(old_id)

    cap.release()
    return {'in': in_count, 'out': out_count, 'inside': max(0, len(inside_ids))}
