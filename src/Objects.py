from operator import sub

import cv2
import numpy as np


class Object:
    def __init__(self, identifier: int, center: tuple, box: list[int], color: tuple):
        # Unchangeable
        self.id = identifier
        self.color = color

        # Changeable
        self.box = box
        self.center = center

    def get_id(self):
        return self.id

    def get_color(self):
        return self.color

    def get_box(self):
        return self.box

    def get_center(self):
        return self.center


class Candidate(Object):
    def __init__(self, identifier: int, center: tuple, box: list[int], color: tuple):
        super().__init__(identifier, center, box, color)
        self.distance = None

    def calculate_min_distance(self, function: callable):
        new_distance = function()
        if self.distance is None:
            self.distance = new_distance
        elif self.distance > new_distance:
            self.distance = new_distance
        return self.distance


class MovingObject(Object):
    def __init__(self, identifier: int, center: tuple, box: list[int], color: tuple):
        super().__init__(identifier, center, box, color)
        self.plain_velocity = (0, 0)
        self.not_tracked_frames_in_row = 0
        self.tracked = False

    def __eq__(self, other):
        if not isinstance(other, MovingObject):
            return False
        return self.id == other.id

    def track(self, center, box):
        self.tracked = True
        self.plain_velocity = tuple(map(sub, center, self.center))
        self.center = center
        self.box = box

    def update_position(self):
        self.box = tuple(map(sum, zip(self.box, self.plain_velocity + (0, 0))))
        self.center = tuple(map(sum, zip(self.center, self.plain_velocity)))

    def update(self):
        if self.tracked:
            self.not_tracked_frames_in_row = 0
            self.tracked = False
        else:
            self.update_position()
            self.not_tracked_frames_in_row += 1


class Team:
    def __init__(self, identifier, color):
        self.footballers = []
        self.id = identifier
        self.color = color

        self.sum_of_colors = (0, 0, 0)
        self.n_footballers = 0

    def __eq__(self, other):
        if not isinstance(other, Team):
            return False
        return self.id == other.id

    def add_footballer(self, footballer: MovingObject):
        self.footballers.append(footballer)

        self.sum_of_colors = tuple(map(sum, zip(self.sum_of_colors, footballer.color)))
        self.n_footballers += 1
        self.color = tuple([channel // self.n_footballers for channel in self.sum_of_colors])

    def remove_footballer(self, footballer: MovingObject):
        if footballer in self.footballers:
            self.sum_of_colors = tuple(map(sub, self.sum_of_colors, footballer.color))
            self.n_footballers -= 1
            if self.n_footballers:
                self.color = tuple([channel // self.n_footballers for channel in self.sum_of_colors])
            self.footballers.remove(footballer)

        if self.n_footballers < 0:
            print(self.n_footballers)
            print(len(self.footballers))
            print("XDD------------")

    def assign(self, footballer: MovingObject):
        self.add_footballer(footballer)
        footballer.team = self


class Footballer(MovingObject):
    def __init__(self, identifier: int, center: tuple, box: list[int], color: tuple):
        super().__init__(identifier, center, box, color)
        self.team = None

    def get_team(self):
        return self.team

    def assign(self, team: Team):
        self.team = team
        self.team.add_footballer(self)

    def reassign(self, team: Team):
        self.team.remove_footballer(self)

        self.team = team
        self.team.add_footballer(self)

    def draw(self, frame: np.ndarray):
        cv2.rectangle(frame, (self.box[0], self.box[1]),
                      (self.box[0] + self.box[2], self.box[1] + self.box[3]), self.team.color, 3)
        cv2.putText(frame, str(self.team.id), (self.center[0] + self.box[2] // 2, self.center[1] - self.box[3] // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, self.team.color, 2, cv2.LINE_AA)


class Ball(MovingObject):
    def __init__(self, identifier: int, center: tuple, box: list[int], color: tuple):
        super().__init__(identifier, center, box, color)
