import numpy as np

from Colors import Colors
from FootballProjector import FootballProjector
from Objects import Footballer, Team, Candidate, Ball
from Config import Config
from utils import color_distance, plain_distance


def color_comparator(color: tuple, candidate: Candidate):
    return candidate.calculate_min_distance(lambda: color_distance(color, candidate.color))


def plain_distance_comparator(center_first: tuple, candidate: Candidate):
    return candidate.calculate_min_distance(lambda: plain_distance(center_first, candidate.center))


def _plain_distance_footballers_sort(footballers_list: list[Footballer], candidate: Candidate):
    candidate.distance = None
    footballers_list.sort(key=lambda f: plain_distance_comparator(f.center, candidate), reverse=False)


def _color_distance_teams_sort(teams_list: list[Team], candidate: Candidate):
    candidate.distance = None
    teams_list.sort(key=lambda team: color_comparator(team.color, candidate), reverse=False)


class FootballManager:
    def __init__(self, projector: FootballProjector, max_teams: int = 2, max_footballers: int = 25):
        self.MAX_TEAMS = max_teams
        self.MAX_FOOTBALLERS = max_footballers

        self.footballers = []
        self.deleted_footballers = []
        self.initial_indexes = list(range(max_footballers))

        self.teams = []
        self.team_colors = Config.TEAM_COLORS.copy()

        self.ball = None

        self.projector = projector

    def _assign_to_existing_team(self, footballer: Footballer, candidate: Candidate):
        _color_distance_teams_sort(self.teams, candidate)
        if self.teams[0] != footballer.team:
            footballer.reassign(self.teams[0])

    def _add_new_team(self, color: tuple):
        if Config.use_display_colors:
            team = Team(len(self.teams), color, self.team_colors[0])
            del self.team_colors[0]
        else:
            team = Team(len(self.teams), color)

        self.teams.append(team)
        print(f"{Colors.OKGREEN}New Team has been added with color: {Colors.OKBLUE}{color}{Colors.ENDC}")
        return team

    def _add_new_footballer(self, candidate: Candidate):
        footballer = Footballer(self.initial_indexes[0], candidate.center, candidate.box, candidate.color)
        self.footballers.append(footballer)
        del self.initial_indexes[0]
        print(f"{Colors.OKGREEN}New Footballer has been added with id: {Colors.OKBLUE}{footballer.id}{Colors.ENDC}")
        return footballer

    def _remove_footballer(self, footballer: Footballer):
        footballer.team.remove_footballer(footballer)
        self.footballers.remove(footballer)
        self.initial_indexes.append(footballer.id)
        print(f"{Colors.WARNING}Footballer with ID {Colors.FAIL}{footballer.id}{Colors.WARNING} has been deleted{Colors.ENDC}")

    def _determine_team(self, candidate: Candidate):
        _color_distance_teams_sort(self.teams, candidate)

        if len(self.teams) >= self.MAX_TEAMS:
            return self.teams[0]

        if len(self.teams) == 0:
            return self._add_new_team(candidate.color)

        if candidate.distance <= 80:
            return self.teams[0]
        else:
            return self._add_new_team(candidate.color)

    def _determine_footballer(self, candidate: Candidate):
        _plain_distance_footballers_sort(self.footballers, candidate)
        if len(self.footballers) >= self.MAX_FOOTBALLERS:
            self.footballers[0].track(candidate.center, candidate.box)
            self._assign_to_existing_team(self.footballers[0], candidate)
            return None

        if len(self.footballers) == 0:
            return self._add_new_footballer(candidate)

        if candidate.distance <= 80:
            self.footballers[0].track(candidate.center, candidate.box)
            self._assign_to_existing_team(self.footballers[0], candidate)
            return None
        else:
            return self._add_new_footballer(candidate)

    def process_candidates(self, candidates: list[Candidate]):
        for candidate in candidates:
            footballer = self._determine_footballer(candidate)
            if footballer is not None:
                team = self._determine_team(candidate)
                team.assign(footballer)

    def process_ball_candidates(self, candidates: list[Candidate]):
        if len(candidates):
            if self.ball is None:
                self.ball = Ball(0, candidates[0].center, candidates[0].box, candidates[0].color)
            else:
                self.ball.track(candidates[0].center, candidates[0].box)

    # TODO Update and draw for merging for loops?
    def update(self):
        for footballer in self.footballers:
            footballer.update()

            if footballer.not_tracked_frames_in_row >= 5:
                self._remove_footballer(footballer)

    def draw(self, frame: np.ndarray):
        for footballer in self.footballers:
            footballer.draw(frame)

        if self.ball is not None:
            self.ball.draw(frame)

    def send_objects_to_projector(self):
        self.projector.footballers = self.footballers
        self.projector.ball = self.ball
