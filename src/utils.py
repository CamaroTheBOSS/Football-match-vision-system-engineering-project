import numpy as np


def color_distance(color_first: tuple, color_second: tuple):
    dR = (color_first[0] - color_second[0])**2
    dG = (color_first[1] - color_second[1])**2
    dB = (color_first[2] - color_second[2])**2
    r = 0.5*(color_first[0] + color_second[0])
    return np.sqrt((2 + r/256)*dR + 4*dG + (2 + (255 - r)/256)*dB)


def plain_distance(center_first: tuple, center_second: tuple):
    return abs(center_first[0] - center_second[0]) + abs(center_first[1] - center_second[1])
