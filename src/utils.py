import numpy as np


def color_distance(color_first: tuple, color_second: tuple):
    dR = (color_first[0] - color_second[0])**2
    dG = (color_first[1] - color_second[1])**2
    dB = (color_first[2] - color_second[2])**2
    r = 0.5*(color_first[0] + color_second[0])
    return np.sqrt((2 + r/256)*dR + 4*dG + (2 + (255 - r)/256)*dB)


def plain_distance(center_first: tuple, center_second: tuple):
    return abs(center_first[0] - center_second[0]) + abs(center_first[1] - center_second[1])


# here are the functions which are used for testing whether intersection between two edges exists
# source https://www.geeksforgeeks.org/check-if-two-given-line-segments-intersect/
def on_segment(p, q, r):
    if ((q[0] <= max(p[0], r[0])) and (q[0] >= min(p[0], r[0])) and
            (q[1] <= max(p[1], r[1])) and (q[1] >= min(p[1], r[1]))):
        return True
    return False


def orientation(p, q, r):
    val = (float(q[1] - p[1]) * (r[0] - q[0])) - (float(q[0] - p[0]) * (r[1] - q[1]))
    if val > 0:  # Clockwise orientation
        return 1

    elif val < 0:  # Counterclockwise orientation
        return 2

    else:  # Collinear orientation
        return 0


def do_intersect(p1, q1, p2, q2):
    # Find the 4 orientations required for
    # the general and special cases
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    # General case
    if (o1 != o2) and (o3 != o4):
        return True

    # Special Cases
    # p1 , q1 and p2 are collinear and p2 lies on segment p1q1
    if (o1 == 0) and on_segment(p1, p2, q1):
        return True

    # p1 , q1 and q2 are collinear and q2 lies on segment p1q1
    if (o2 == 0) and on_segment(p1, q2, q1):
        return True

    # p2 , q2 and p1 are collinear and p1 lies on segment p2q2
    if (o3 == 0) and on_segment(p2, p1, q2):
        return True

    # p2 , q2 and q1 are collinear and q1 lies on segment p2q2
    if (o4 == 0) and on_segment(p2, q1, q2):
        return True

    # If none of the cases
    return False
