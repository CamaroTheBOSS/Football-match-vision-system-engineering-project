from operator import sub


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


class MovingObject(Object):
    def __init__(self, identifier: int, center: tuple, box: list[int], color: tuple):
        super().__init__(identifier, center, box, color)
        self.plain_velocity = (0, 0)


class Team:
    def __init__(self, identifier, color):
        self.footballers = []
        self.id = identifier
        self.color = color

    def add_footballer(self, footballer: MovingObject):
        self.footballers.append(footballer)


class Footballer(MovingObject):
    def __init__(self, identifier: int, center: tuple, box: list[int], color: tuple):
        super().__init__(identifier, center, box, color)
        self.team = None

    def get_team(self):
        return self.team

    def assign(self, team: Team):
        self.team = team
        self.team.add_footballer(self)


class Ball(MovingObject):
    def __init__(self, identifier: int, center: tuple, box: list[int], color: tuple):
        super().__init__(identifier, center, box, color)
