import cv2
import numpy as np
from Points import IntersectPoint
from Football import FootballManager


CONFIG = "lewy.mp4"
PARAMETERS = {"fifa.mkv": {"CBT": [(30, 0, 40), (50, 255, 255)],  # Cutting background threshold (getting whole pitch)
                           "PLT": [(0, 110, 0), (255, 255, 255)]},  # Extruding pitch lines threshold (getting pitch lines)
              "lewy.mp4": {"CBT": [(30, 0, 30), (50, 255, 255)],
                           "PLT": [(0, 110, 0), (255, 255, 255)]},
              "v.mp4": {"CBT": [(30, 0, 30), (70, 255, 200)],
                        "PLT": [(0, 120, 0), (255, 255, 255)]},
              }


# NOTES FOR FOOTBALLERS DETECTION
# mask[np.logical_and(mask[:, :, 1] > mask[:, :, 2], mask[:, :, 2] > mask[:, :, 0])] = [255, 255, 255]
# mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
# ret2, mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY)
# mask = cv2.cvtColor(mask, cv2.COLOR_HSV2BGR)
# mask = cv2.erode(mask, (3, 3), iterations=7)
# https://medium.com/betonchart/effective-way-to-collect-soccer-data-70ef69182eba


def cut_background(frame: np.ndarray):
    kernel = np.ones((3, 3))
    out = cv2.cvtColor(frame, cv2.COLOR_BGR2HLS)
    out = cv2.inRange(out, PARAMETERS[CONFIG]["CBT"][0], PARAMETERS[CONFIG]["CBT"][1])
    out = cv2.morphologyEx(out, cv2.MORPH_OPEN, kernel=kernel, iterations=5)
    out = cv2.morphologyEx(out, cv2.MORPH_CLOSE, kernel=kernel, iterations=7)
    return out


def cut_footballers_boxes(frame: np.ndarray):
    # 1. Finding all the contours in specific frame
    _, thresh = cv2.threshold(frame, 1, 255, cv2.RETR_TREE)
    thresh = cv2.erode(thresh, np.ones((3, 3)), iterations=12)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    contours_on_img = sorted(contours, key=lambda cnt: cv2.contourArea(cnt), reverse=False)

    # 2. Looking for the best candidates (size criterion)
    candidate_contours = []
    for contour in contours_on_img:
        if cv2.contourArea(contour) < 10000:
            candidate_contours.append(contour)
        else:
            break

    mask = np.full_like(thresh, 255)
    cv2.drawContours(mask, candidate_contours, -1, (0, 0, 0), cv2.FILLED)
    return mask


def cut_footballers_silhouette(frame: np.ndarray, mask):
    # 1. Cutting silhouettes
    mask[np.logical_and(frame[:, :, 1] > frame[:, :, 2], frame[:, :, 2] > frame[:, :, 0])] = 255
    mask = cv2.erode(mask, (3, 3), iterations=20)

    # 2. Finding contours of silhouettes
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    # 3. Artifacts cleaning (area criterion)
    silhouettes = []
    for contour in contours:
        if 150 < len(contour) < 2500:
            silhouettes.append(contour)

    return mask, silhouettes


def preprocessingIdea1_EXTRUDING_PITCH_LINES(videoFrame):
    out = cv2.cvtColor(videoFrame, cv2.COLOR_BGR2HLS)
    out = cv2.inRange(out, PARAMETERS[CONFIG]["PLT"][0], PARAMETERS[CONFIG]["PLT"][1])
    return out


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
        b = pt1[1] - a*pt1[0]
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
    cap = cv2.VideoCapture("video/" + CONFIG)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 3600)
    football_manager = FootballManager()

    while True:
        # 1. Getting frame
        ret, frame = cap.read()
        if not ret:
            break

        # 2. Cutting background and footballer boxes
        mask = cut_background(frame)
        mask = cut_footballers_boxes(mask)
        frame_with_pitch = cv2.bitwise_and(frame, frame, mask=mask)

        # 3. Finding footballers
        frame_with_footballers = cv2.bitwise_and(frame, frame, mask=np.invert(mask))
        mask, silhouettes = cut_footballers_silhouette(frame_with_footballers, mask)
        frame_with_footballers = cv2.bitwise_and(frame, frame, mask=mask)
        football_manager.fit_contours_to_objects(frame, silhouettes)

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
        cv2.imshow("frame", frame)
        cv2.imshow("frame with pitch", frame_with_pitch)
        cv2.imshow("frame with footballers", frame_with_footballers)
        # cv2.imshow("edges", canny)
        # cv2.imshow("final lines", empty2)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


main()
