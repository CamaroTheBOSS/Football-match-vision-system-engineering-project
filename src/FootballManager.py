import cv2
import numpy as np

from Colors import Colors
from Objects import Footballer, Team


def get_box_and_center(contour):
    m = cv2.moments(contour)
    box = cv2.boundingRect(contour)
    center = (int(m['m10'] / m['m00']), int(m['m01'] / m['m00'])) if m['m00'] != 0.0 else \
        tuple(coord // 2 for coord in box[0:2])

    return center, box


def find_average_color(frame: np.ndarray, box: list[int]):
    x, y, w, h = box[0] + box[2] // 3, box[1] + box[3] // 10, box[2] // 3, 3 * box[3] // 10
    x_vec = np.linspace(x, x + w - 1, 10, dtype=int)
    y_vec = np.linspace(y, y + h - 1, 10, dtype=int)
    colors_list = [frame[y, x] for x in x_vec for y in y_vec]
    average_color = (0, 0, 0)
    divider = 0
    for color in colors_list:
        if not np.logical_and(color[0] > color[1], color[1] > color[2]):
            average_color = tuple(map(sum, zip(average_color, color)))
            divider += 1
    if not divider:
        divider = 1
    average_color = tuple(int(color) // divider for color in average_color)

    return average_color


class FootballManager:
    def __init__(self):
        self.footballers = []
        self.teams = []
        self.ball = None
        self.footballer_idx = 0

    def _add_footballer_to_existing_team(self, center: tuple, box: list[int], color: tuple, team: Team):
        print(f"{Colors.OKCYAN} Footballer added to team with id: {team.id}{Colors.ENDC}")
        self.footballers.append(Footballer(self.footballer_idx, center, box, color, team))
        self.footballer_idx += 1

    def _add_footballer_and_team(self, center: tuple, box: list[int], color: tuple):
        print(f"{Colors.OKGREEN} Footballer and team added {Colors.ENDC}")
        self.teams.append(Team(color, len(self.teams)))
        self.footballers.append(Footballer(self.footballer_idx, center, box, color, self.teams[-1]))
        self.footballer_idx += 1

    def track_footballers(self, center, box, average_color):
        # 3.1 Looking for the nearest footballer
        if len(self.footballers):
            self.footballers.sort(key=lambda f: f.calc_distance(center), reverse=False)
            for footballer in self.footballers:
                # 3.1.1 Necessary condition
                if footballer.distance > 1 ** 2:
                    self.teams.sort(key=lambda t: t.calc_distance(average_color), reverse=False)
                    if self.teams[0].distance < 1:
                        self._add_footballer_to_existing_team(center, box, average_color, self.teams[0])
                    else:
                        self._add_footballer_and_team(center, box, average_color)
                    return

                # 3.1.2 Team condition
                self.teams.sort(key=lambda t: t.calc_distance(average_color), reverse=False)
                for team in self.teams:
                    if team.id != footballer.team.id or team.distance > 1:
                        self._add_footballer_and_team(center, box, average_color)
                        return

                    # 3.1.3 TODO Size condition

                    # 3.1.4 This is that footballer
                    footballer.track(center, box)
                    print(f"{Colors.OKBLUE} Footballer tracked (id: {footballer.id}) {Colors.ENDC}")
                    return
        else:
            self._add_footballer_and_team(center, box, average_color)

    def fit_contours_to_objects(self, frame: np.ndarray, contours: list[np.ndarray]):
        for contour in contours:
            # 1. Finding center of mass and bounding box of the contour
            center, box = get_box_and_center(contour)

            # 2. Finding average color
            average_color = find_average_color(frame, box)

            # 3. Fit object with specific center of mass and specific
            # color to previously detected objects (or add it to detected objects)
            self.track_footballers(center, box, average_color)