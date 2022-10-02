import cv2
import numpy as np
import keyboard

from CameraTracker import CameraTracker
from Drawer import Drawer
from FrameDistributor import FrameDistributor
from ObjectsDetector import ObjectsDetector
from Points import IntersectPoint
from FootballManager import FootballManager
from Config import Config





# NOTES FOR FOOTBALLERS DETECTION
# mask[np.logical_and(mask[:, :, 1] > mask[:, :, 2], mask[:, :, 2] > mask[:, :, 0])] = [255, 255, 255]
# mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
# ret2, mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY)
# mask = cv2.cvtColor(mask, cv2.COLOR_HSV2BGR)
# mask = cv2.erode(mask, (3, 3), iterations=7)
# https://medium.com/betonchart/effective-way-to-collect-soccer-data-70ef69182eba


# def preprocessingIdea1_EXTRUDING_PITCH_LINES(videoFrame):
#     out = cv2.cvtColor(videoFrame, cv2.COLOR_BGR2HLS)
#     out = cv2.inRange(out, PARAMETERS[CONFIG]["PLT"][0], PARAMETERS[CONFIG]["PLT"][1])
#     return out


def houghLinesP(src, dst):
    linesP = cv2.HoughLinesP(src, 1, np.pi / 180, 50, None, 100, 50)
    if linesP is not None:
        for i in range(len(linesP)):
            line = linesP[i][0]
            cv2.line(dst, (line[0], line[1]), (line[2], line[3]), (255, 255, 255), 3, cv2.LINE_AA)
    return dst


def houghLines(src):
    lines = cv2.HoughLines(src, 1, np.pi / 180, 100, None, 0, 0)
    vertical = []
    horizontal = []
    if lines is not None:
        # Separate horizontal and vertical lines from each other
        for i in range(len(lines)):
            r, theta = lines[i][0]
            if theta > np.pi / 2:
                horizontal.append([r, theta])
            else:
                vertical.append([r, theta])
    return vertical, horizontal


def aggregateLines(lines):
    # Aggregation algorithm for horizontal lines
    aggregatedLines = []
    while len(lines):
        r, theta = lines[0]
        toAggregate = [[r, theta]]

        # Collecting similar lines
        for rInterior, thetaInterior in lines:
            if abs(r - rInterior) < 80 and abs(theta - thetaInterior) < 0.15:
                toAggregate.append([rInterior, thetaInterior])

        # Aggregating collected similar lines
        if len(toAggregate) > 1:
            rSum = 0
            thetaSum = 0
            for i in range(len(toAggregate)):
                rSum += toAggregate[i][0]
                thetaSum += toAggregate[i][1]
            aggregatedLines.append([rSum // len(toAggregate), thetaSum / len(toAggregate)])

        # Deleting used horizontal lines
        lines = [item for item in lines if item not in toAggregate]

    return aggregatedLines


def displayLines(lines, dst):
    # Display lines
    for r, theta in lines:
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a * r
        y0 = b * r
        pt1 = (int(x0 + 1000 * (-b)), int(y0 + 1000 * a))
        pt2 = (int(x0 - 1000 * (-b)), int(y0 - 1000 * a))
        cv2.line(dst, pt1, pt2, (255, 255, 255), 3, cv2.LINE_AA)


def convertPOLAR2CARTESIAN(lines):
    cartesian = []
    for r, theta in lines:
        a0 = np.cos(theta)
        b0 = np.sin(theta)

        # "Center" point of the line
        x0 = a0 * r
        y0 = b0 * r

        # Points of the line
        pt1 = (int(x0 - 1000 * b0), int(y0 + 1000 * a0))
        pt2 = (int(x0 + 1000 * b0), int(y0 - 1000 * a0))

        a = (pt2[1] - pt1[1]) / (pt2[0] - pt1[0]) if (pt2[0] - pt1[0]) != 0 else 10000
        b = pt1[1] - a * pt1[0]
        cartesian.append([a, b])
    return cartesian


def findIntersections(vertical, horizontal):
    intersections = []
    for av, bv in vertical:
        for ah, bh in horizontal:
            if av != ah:
                x = (bh - bv) / (av - ah)
                y = av * x + bv
                intersections.append(IntersectPoint((int(x), int(y))))
    return intersections


def displayPoints(points, dst):
    for point in points:
        cv2.circle(dst, point.coord, 10, (255, 0, 0), -1)


def main():
    football_manager = FootballManager()
    drawer = Drawer(football_manager.footballers)

    objects_detector = ObjectsDetector()
    camera_tracker = CameraTracker()
    frame_distributor = FrameDistributor("../video/" + Config.get_video(), objects_detector, camera_tracker)

    while True:
        # 1. Getting frame
        if not frame_distributor.read():
            break

        # 2. Preprocess got frame and send it to detectors
        frame_distributor.cut_background()
        frame_distributor.cut_objects()
        frame_distributor.send_to_detectors()

        # 3. Detect footballers
        objects_detector.look_for_objects()
        candidates = objects_detector.prepare_candidates()
        football_manager.process_candidates(candidates)

        football_manager.update()
        drawer.frame = frame_distributor.frame
        football_manager.draw(drawer.frame)
        drawer.draw_frame("")
        # mask, silhouettes = cut_footballers_silhouette(frame_with_footballers, mask)
        # frame_with_footballers = cv2.bitwise_and(frame, frame, mask=mask)
        # # football_manager.fit_contours_to_objects(frame, silhouettes)
        # # drawer.draw_footballers(frame)
        # cv2.drawContours(frame, silhouettes, -1, (0, 0, 255), 3)

        # cv2.drawContours(frame, silhouettes, -1, (0, 0, 255), 1)

        # # 4. If we don't catch the lines we get lines by this step
        # output = preprocessingIdea1_EXTRUDING_PITCH_LINES(output)
        #
        # # 5. Detecting pitch lines
        # empty = np.zeros_like(output)
        # houghLinesP(output, empty)  # HoughLinesP is detecting lines roughly
        # empty2 = np.zeros_like(output)
        # canny = cv2.Canny(empty, 254, 255)
        # verticalLines, horizontalLines = houghLines(canny)  # Usual HoughLines is detecting lines more precisely
        # aggregatedVerticals = aggregateLines(verticalLines)
        # aggregatedHorizontals = aggregateLines(horizontalLines)
        # displayLines(aggregatedVerticals, empty2)
        # displayLines(aggregatedHorizontals, empty2)
        #
        # # 6. Finding intersections
        # cartesianVerticals = convertPOLAR2CARTESIAN(aggregatedVerticals)
        # cartesianHorizontals = convertPOLAR2CARTESIAN(aggregatedHorizontals)
        # intersectionPoints = findIntersections(cartesianVerticals, cartesianHorizontals)
        # displayPoints(intersectionPoints, frame)

        # X. Show windows
        # cv2.imshow("frame with pitch", frame_with_pitch)
        # cv2.imshow("frame with footballers", frame_with_footballers)
        # cv2.imshow("edges", canny)
        # cv2.imshow("final lines", empty2)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if keyboard.is_pressed("d"):
            frame_distributor.cap_forward()
        if keyboard.is_pressed("a"):
            frame_distributor.cap_rewind()

    frame_distributor.cap.release()
    cv2.destroyAllWindows()


main()
