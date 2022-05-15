import math
from pathlib import Path
from typing import Union
from collections import namedtuple

import numpy as np
from gym.spaces.discrete import Discrete

from Environment.objects.ground import Ground
from Environment.objects.intersection import Intersection
from Environment.objects.model_object import Object
from Environment.objects.road import Road
from Environment.objects.car import Car

raw_data_path = Path("Environment", "raw_data")


class City:
    __actions = ('FORWARD',
                 'RIGHT_BACK',
                 'LEFT',
                 'LEFT_LANE',
                 'RIGHT_LANE',
                 'PASS',
                 'TURN_AROUND')
    _actions = namedtuple('Actions', __actions)(*np.arange(len(__actions)))

    __cardinal_directions = ('SE', 'S', 'SW', 'W', 'NW', 'N', 'NE', 'E')

    def __init__(self, map_sample: int = 0, layout_sample: int = 0, narrowing_and_expansion: bool = False):

        from Environment.raw_data.roads import roads

        np.random.seed(123)

        city_map = []
        with open(Path(raw_data_path, 'map.txt'), 'r') as map_file:
            line = map_file.readline()
            while line:
                city_map.append(line.split())
                line = map_file.readline()
        self.city_map = np.array(city_map)
        self.shape = self.city_map.shape

        self.intersections = np.array(list(zip(*np.where(self.city_map == 'X'))))
        self.roads = roads.get(layout_sample)
        self.road_cells = []

        self.city_model = [[Object() for __ in range(self.shape[1])] for _ in range(self.shape[0])]
        print("Empty city was built.")

        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                self.city_model[i][j] = Ground()
        print("Ground was built.")

        self.make_intersections()
        self.make_roads(narrowing_and_expansion)
        print("Intersections and roads were built.")

        self.print_model_to_file('model_with_intersections_and_lanes(with dynamic lanes).txt')

        # self.reward_range = np.arange()

        # n_states =
        n_actions = len(City._actions)
        self.action_space = Discrete(n_actions)

        # self.P = {s: {a: [] for a in range(n_actions)} for s in range(nS)}
        #
        # for d in self.__cardinal_directions[1:-1:2]:
        #     for c_d in self.__cardinal_directions:





    def test_state(self):
        start_axis0, start_axis1, _, current_direction, lane = self.choose_random_road_state()
        finish_axis0, finish_axis1 = self.choose_random_road()
        print(f"Start: {(start_axis0, start_axis1)},{current_direction = },{lane = }")
        print(f"Finish: {(finish_axis0, finish_axis1)}")
        Vector = namedtuple('Vector', ('axis0', 'axis1'))
        vec = Vector(finish_axis0 - start_axis0, finish_axis1 - start_axis1)
        print(vec)

        # Approximate direction preprocessing
        if math.isclose(vec.axis1, 0.0):
            alpha = 90 if vec.axis0 >= 0 else 270
        elif math.isclose(vec.axis0, 0.0):
            alpha = 0 if vec.axis1 >= 0 else 180
        else:
            tg_alpha = vec.axis0 / vec.axis1
            print(f"{tg_alpha = }")

            alpha = math.degrees(math.atan(tg_alpha))

            if alpha < 0:
                alpha += 360
            if vec.axis0 < 0 and vec.axis1 < 0:
                alpha += 180
            if vec.axis0 > 0 and vec.axis1 < 0:
                alpha -= 180

        print(f"{alpha = }")
        for angle in np.arange(22.5, 292.6, 45):
            print(angle)
            if angle <= alpha < angle + 45:
                approx_dir = self.__cardinal_directions[int(angle // 45)]
                break
        else:
            approx_dir = 'N'

        # Lanes preprocessing
        n_lanes: int = len(self.city_model[start_axis0][start_axis1].lanes.get(current_direction))
        lanes = namedtuple('LaneInfo', ('is_left', 'is_right'))
        if n_lanes == 1:
            lane_pos = lanes(True, True)
        elif n_lanes == 0:
            lane_pos = None
        elif lane == 0:
            lane_pos = lanes(True, False)
        elif lane == n_lanes - 1:
            lane_pos = lanes(False, True)
        else:
            lane_pos = lanes(False, False)

        state = current_direction, approx_dir, (lane, n_lanes, lane_pos),\
            tuple(self.get_observation(current_direction, start_axis0, start_axis1).reshape(1, -1).ravel())
        print(f"State: {state}")

    def choose_random_road(self):
        return self.road_cells[np.random.randint(0, len(self.road_cells))]

    # May appear a problem if there are no lanes in the particular direction.
    def choose_random_road_state(self):
        axis0, axis1 = self.choose_random_road()
        if self.city_model[axis0][axis1].orientation == 'v':
            direction = np.random.choice(['N', 'S'])
        else:
            direction = np.random.choice(['W', 'E'])
        lane = np.random.randint(0, len(self.city_model[axis0][axis1].lanes.get(direction)))
        return axis0, axis1, self.city_model[axis0][axis1], direction, lane

    def get_observation(self, direction: str, *coord) -> np.ndarray:
        o = []
        axis0, axis1 = coord
        if direction == 'N':
            for a0 in range(axis0-1, axis0+1):
                for a1 in range(axis1-1, axis1+2):
                    o.append(self.city_model[a0][a1])
            return np.array(o).reshape(2, 3)
        elif direction == 'S':
            for a0 in range(axis0, axis0+2):
                for a1 in range(axis1-1, axis1+2):
                    o.append(self.city_model[a0][a1])
            return np.array(o).reshape(2, 3)
        elif direction == 'W':
            for a0 in range(axis0-1, axis0+2):
                for a1 in range(axis1-1, axis1+1):
                    o.append(self.city_model[a0][a1])
            return np.array(o).reshape(3, 2)
        else:
            for a0 in range(axis0-1, axis0+2):
                for a1 in range(axis1, axis1+2):
                    o.append(self.city_model[a0][a1])
            return np.array(o).reshape(3, 2)

    def make_intersections(self):
        for axis0, axis1 in self.intersections:
            self.city_model[axis0][axis1] = Intersection()

    def make_roads(self, narrowing_and_expansion: bool = False) -> None:
        _LANES_AVAILABLE = [1, 2, 3]
        _LANE_TRANSFORMATIONS = [-1, 0, 1]

        def narrow_expand(n_lanes: int) -> int:
            if narrowing_and_expansion and n_lanes >= 2:
                shift = np.random.choice(_LANE_TRANSFORMATIONS)
                return n_lanes + shift
            return n_lanes

        for way in self.roads:

            intersection_start_coord = self.intersections[way[0]]
            intersection_finish_coord = self.intersections[way[1]]

            start_axis0 = intersection_start_coord[0]
            start_axis1 = intersection_start_coord[1]
            finish_axis0 = intersection_finish_coord[0]
            finish_axis1 = intersection_finish_coord[1]

            intersection_start: Union[Intersection, list[Object]] = self.city_model[start_axis0][start_axis1]
            intersection_finish: Union[Intersection, list[Object]] = self.city_model[finish_axis0][finish_axis1]

            if start_axis0 == finish_axis0:
                intersection_start.lanes['E'] = 2
                intersection_finish.lanes['W'] = 2

                current_e_lanes = narrow_expand(intersection_start.lanes['E'])
                current_w_lanes = narrow_expand(intersection_finish.lanes['W'])

                for axis1_index in range(start_axis1 + 1, (finish_axis1 + start_axis1 + 1) // 2):
                    self.road_cells.append((start_axis0, axis1_index))
                    self.city_model[start_axis0][axis1_index] = Road('h',
                                                                     {'W': intersection_finish.lanes['W'],
                                                                      'E': intersection_start.lanes['E']},
                                                                     'ds',
                                                                     'b')
                for axis1_index in range((finish_axis1 + start_axis1 + 1) // 2, finish_axis1):
                    self.road_cells.append((start_axis0, axis1_index))
                    self.city_model[start_axis0][axis1_index] = \
                        Road('h',
                             {'W': current_w_lanes,
                              'E': current_e_lanes},
                             'ds',
                             'b')

                intersection_finish.lanes['W'] = current_w_lanes

            elif start_axis1 == finish_axis1:
                intersection_start.lanes['S'] = 3
                intersection_finish.lanes['N'] = 3

                current_n_lanes = narrow_expand(intersection_finish.lanes['N'])
                current_s_lanes = narrow_expand(intersection_start.lanes['S'])

                for axis0_index in range(start_axis0 + 1, (finish_axis0 + start_axis0 + 1) // 2):
                    self.road_cells.append((axis0_index, start_axis1))
                    self.city_model[axis0_index][start_axis1] = Road('v',
                                                                     {'N': intersection_finish.lanes['N'],
                                                                      'S': intersection_start.lanes['S']},
                                                                     'ds',
                                                                     'b')

                for axis0_index in range((finish_axis0 + start_axis0 + 1) // 2, finish_axis0):
                    self.road_cells.append((axis0_index, start_axis1))
                    self.city_model[axis0_index][start_axis1] = \
                        Road('v',
                             {'N': current_n_lanes,
                              'S': current_s_lanes},
                             'ds',
                             'b')

                intersection_finish.lanes['N'] = current_n_lanes

    def print_model_to_file(self, filename: str):
        with open(Path('Environment', filename), 'w', encoding='UTF-8') as new_map_file:
            for line in self.city_model:
                print(*line, sep='', file=new_map_file)

    def step(self):
        pass

    def reset(self):
        pass
