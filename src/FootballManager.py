import numpy as np

from Colors import Colors
from Objects import Footballer, Team, Candidate
from Config import Config


def color_distance(color_first: tuple, color_second: tuple):
    dR = (color_first[0] - color_second[0])**2
    dG = (color_first[1] - color_second[1])**2
    dB = (color_first[2] - color_second[2])**2
    r = 0.5*(color_first[0] + color_second[0])
    return np.sqrt((2 + r/256)*dR + 4*dG + (2 + (255 - r)/256)*dB)


def color_comparator(color: tuple, candidate: Candidate):
    return candidate.calculate_min_distance(lambda: color_distance(color, candidate.color))


def plain_distance(center_first: tuple, center_second: tuple):
    return abs(center_first[0] - center_second[0]) + abs(center_first[1] - center_second[1])


def plain_distance_comparator(center_first: tuple, candidate: Candidate):
    return candidate.calculate_min_distance(lambda: plain_distance(center_first, candidate.center))


class FootballManager:
    def __init__(self, max_teams: int = 2, max_footballers: int = 25):
        self.MAX_TEAMS = max_teams
        self.MAX_FOOTBALLERS = max_footballers

        self.footballers = []
        self.deleted_footballers = []
        self.initial_indexes = list(range(max_footballers))

        self.teams = []
        self.team_colors = Config.TEAM_COLORS.copy()

        self.ball = None

    def _plain_distance_footballers_sort(self, candidate: Candidate):
        candidate.distance = None
        self.footballers.sort(key=lambda f: plain_distance_comparator(f.center, candidate), reverse=False)

    def _plain_distance_deleted_footballers_sort(self, candidate: Candidate):
        candidate.distance = None
        self.deleted_footballers.sort(key=lambda f: plain_distance_comparator(f.center, candidate), reverse=False)

    def _color_distance_teams_sort(self, candidate: Candidate):
        candidate.distance = None
        self.teams.sort(key=lambda team: color_comparator(team.color, candidate), reverse=False)

    def _assign_to_existing_team(self, footballer: Footballer, candidate: Candidate):
        self._color_distance_teams_sort(candidate)
        if self.teams[0] != footballer.team:
            footballer.reassign(self.teams[0])

    def _add_new_team(self, color: tuple):
        # if Config.use_display_colors:
        #     team = Team(len(self.teams), color, self.team_colors[0])
        #     del self.team_colors[0]
        # else:
        team = Team(len(self.teams), color)

        self.teams.append(team)
        print(f"{Colors.OKGREEN}New Team has been added with color: {Colors.OKBLUE}{color}{Colors.ENDC}")
        return team

    # def _add_footballer_from_deleted_list(self, candidate: Candidate):
    #     footballer = Footballer(self.deleted_footballers[0].id, candidate.center, candidate.box, candidate.color)
    #     self.deleted_footballers[0].team.assign(footballer)
    #     self.footballers.append(footballer)
    #     print(
    #         f"{Colors.OKGREEN}Footballer from deleted_list has been added with id: "
    #         f"{Colors.OKBLUE}{self.deleted_footballers[0].id}{Colors.ENDC}")
    #     del self.deleted_footballers[0]

    def _add_new_footballer(self, candidate: Candidate):
        # if self.deleted_footballers:
        #     self._plain_distance_deleted_footballers_sort(candidate)
        #     self._add_footballer_from_deleted_list(candidate)
        #     return None

        footballer = Footballer(self.initial_indexes[0], candidate.center, candidate.box, candidate.color)
        self.footballers.append(footballer)
        del self.initial_indexes[0]
        print(f"{Colors.OKGREEN}New Footballer has been added with id: {Colors.OKBLUE}{footballer.id}{Colors.ENDC}")
        return footballer

    def _remove_footballer(self, footballer: Footballer):
        footballer.team.remove_footballer(footballer)
        self.footballers.remove(footballer)
        # self.deleted_footballers.append(footballer)
        self.initial_indexes.append(footballer.id)
        print(f"{Colors.WARNING}Footballer with ID {Colors.FAIL}{footballer.id}{Colors.WARNING} has been deleted{Colors.ENDC}")

    def _determine_team(self, candidate: Candidate):
        self._color_distance_teams_sort(candidate)

        if len(self.teams) >= self.MAX_TEAMS:
            return self.teams[0]

        if len(self.teams) == 0:
            return self._add_new_team(candidate.color)

        if candidate.distance <= 80:
            return self.teams[0]
        else:
            return self._add_new_team(candidate.color)

    def _determine_footballer(self, candidate: Candidate):
        self._plain_distance_footballers_sort(candidate)
        if len(self.footballers) >= self.MAX_FOOTBALLERS:
            self.footballers[0].track(candidate.center, candidate.box)
            # self._assign_to_existing_team(self.footballers[0], candidate)
            return None

        if len(self.footballers) == 0:
            return self._add_new_footballer(candidate)

        if candidate.distance <= 80:
            self.footballers[0].track(candidate.center, candidate.box)
            # self._assign_to_existing_team(self.footballers[0], candidate)
            return None
        else:
            return self._add_new_footballer(candidate)

    def process_candidates(self, candidates: list[Candidate]):
        for candidate in candidates:
            footballer = self._determine_footballer(candidate)
            if footballer is not None:
                team = self._determine_team(candidate)
                team.assign(footballer)

    def update(self):
        for footballer in self.footballers:
            footballer.update()

            if footballer.not_tracked_frames_in_row >= 5:
                self._remove_footballer(footballer)

    def draw(self, frame: np.ndarray):
        for footballer in self.footballers:
            footballer.draw(frame)
