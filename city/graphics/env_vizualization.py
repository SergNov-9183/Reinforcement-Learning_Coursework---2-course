import aggdraw
from Environment.city import City
from Environment.objects.road import Road
from Environment.objects.intersection import Intersection
import tkinter as tk
from tkinter import Canvas
from PIL import ImageTk
from PIL import Image
from threading import Thread
from time import sleep
from Environment.model.state import State


class ThreadUpdater(Thread):
    def __init__(self, map):
        super().__init__()
        self.map = map

    def run(self) -> None:
        i_f = MapVizualization.i_finish
        j_f = MapVizualization.j_finish
        while self.map.running:
            if i_f != MapVizualization.i_finish or \
                    j_f != MapVizualization.j_finish:
                i_f = MapVizualization.i_finish
                j_f = MapVizualization.j_finish
                self.map.draw_content()
            self.map.draw_agent()
            if MapVizualization.has_agent and (isinstance(MapVizualization.city.city_model[MapVizualization.i_agent][MapVizualization.j_agent], Road)):
                MapVizualization.agent_position = MapVizualization.agent_position + 1
            sleep(MapVizualization.delay)


class MapVizualization(tk.Tk):
    delay = None
    city = None
    running = True

    has_finish = False
    i_finish = 0
    j_finish = 0

    has_agent = False
    i_agent = 0
    j_agent = 0
    agent_direction = "Z"
    agent_lane_number = 16
    agent_position = 0

    x0 = 0
    y0 = 0

    x_mouse = 0
    y_mouse = 0

    scale = 1

    move_mode = False

    horizontal_window = 2560 // 3 * 2
    vertical_window = 1440 // 3 * 2

    def __init__(self, env: City, delay: float):
        self.wp = None
        self.vertical = None
        self.horizontal = None
        self.tk_image = None
        self.tk_imageAgent = None
        self.something_clicked = 0
        print("DELAY", delay)

        super().__init__()

        self.title("env_visualization")

        self.canvas = Canvas(self, width=self.horizontal_window, height=self.vertical_window, bg="#247719")
        self.canvas.pack(expand=1, fill=tk.BOTH)

        MapVizualization.city = env
        self.drawAgentCount = 25
        MapVizualization.delay = delay / self.drawAgentCount

        self.set_block_size()
        self.draw_content()
        self.draw_agent()

        self.canvas.bind('<MouseWheel>', self.canvas_mouse_wheel_event)
        self.canvas.bind('<Motion>', self.canvas_motion_event)
        self.canvas.bind('<ButtonPress-1>', self.canvas_button_press_event)
        self.canvas.bind('<ButtonRelease-1>', self.canvas_button_release_event)
        self.canvas.bind("<Configure>", self.canvas_resize_event)

        self.thread = ThreadUpdater(self)
        self.thread.start()

    def clear(self):
        print("del map")
        self.running = False
        self.thread.join()

    def set_block_size(self):
        self.vertical = self.vertical_window / MapVizualization.city.shape[0]
        self.horizontal = self.horizontal_window / MapVizualization.city.shape[1]
        if self.vertical < self.horizontal:
            self.horizontal = self.vertical
        else:
            self.vertical = self.horizontal
        self.wp = self.vertical / 10

    def idx_to_x(self, idx):
        return idx * self.horizontal

    def idx_to_y(self, idx):
        return idx * self.vertical

    def draw_content(self):
        def draw_rectangle(x_left, y_top, x_right, y_bottom, fill_color, line_color):
            draw.rectangle((x_left, y_top, x_right, y_bottom), aggdraw.Pen(line_color, 0.5), aggdraw.Brush(fill_color))

        def draw_grass(x0, y0, x1, y1, x2, y2, x3, y3):
            draw.polygon((x0, y0, x1, y1, x2, y2, x3, y3), aggdraw.Pen("#247719", 0.5), aggdraw.Brush("#247719"))

        def draw_vertical_dash_line(x, y_top, y_bottom):
            i = 0
            while True:
                y1 = y_top + i * self.wp * self.scale
                y2 = y_top + (i + 1) * self.wp * self.scale
                if y2 > y_bottom:
                    break
                if i % 2 == 0:
                    draw.line((x, y1, x, y2), aggdraw.Pen("white", 1 * self.scale))
                i = i + 1

        def draw_horizontal_dash_line(x_left, x_right, y):
            i = 0
            while True:
                x1 = x_left + i * self.wp * self.scale
                x2 = x_left + (i + 1) * self.wp * self.scale
                if x2 > x_right:
                    break
                if i % 2 == 0:
                    draw.line((x1, y, x2, y), aggdraw.Pen("white", 1 * self.scale))
                i = i + 1

        def is_road(i, j):
            return (i > 0) and (i <= MapVizualization.city.shape[0]) and (j > 0) and (j <= MapVizualization.city.shape[1]) and (isinstance(MapVizualization.city.city_model[i][j], Road))

        def get_left_count(i, j):
            return [len(value) for key, value in MapVizualization.city.city_model[i][j].lanes.items()][1]

        def get_right_count(i, j):
            return [len(value) for key, value in MapVizualization.city.city_model[i][j].lanes.items()][0]

        def draw_destonation_point(x, y):
            # print(x, y)
            y_top = y - (4 * self.wp) * self.scale
            y_bottom = y - (1 * self.wp) * self.scale
            x_right = x + (3 * self.wp) * self.scale
            y_right = y - (2.5 * self.wp) * self.scale
            points = [x, y_bottom,
                      x, y_top,
                      x_right, y_right]

            draw.polygon(points, aggdraw.Pen("red", 0.5), aggdraw.Brush("red"))
            draw.line((x, y, x, y_top), aggdraw.Pen("black", 3 * self.scale))

        def draw_ground(horizontal_idx, vertical_idx):
            x_left = self.x0 + self.idx_to_x(horizontal_idx) * self.scale
            x_right = self.x0 + self.idx_to_x(horizontal_idx + 1) * self.scale
            y_top = self.y0 + self.idx_to_y(vertical_idx) * self.scale
            y_bottom = self.y0 + self.idx_to_y(vertical_idx + 1) * self.scale

            draw_rectangle(x_left, y_top, x_right, y_bottom, "#247719", "#247719")

        def draw_intersection(horizontal_idx, vertical_idx):
            x_left = self.x0 + self.idx_to_x(horizontal_idx) * self.scale
            x_right = self.x0 + self.idx_to_x(horizontal_idx + 1) * self.scale
            y_top = self.y0 + self.idx_to_y(vertical_idx) * self.scale
            y_bottom = self.y0 + self.idx_to_y(vertical_idx + 1) * self.scale

            draw_rectangle(x_left, y_top, x_right, y_bottom, "gray", "gray")

            if MapVizualization.has_finish and MapVizualization.i_finish == vertical_idx and MapVizualization.j_finish == horizontal_idx:
                x_center = x_left + (x_right - x_left) // 2
                y_center = y_top + (y_bottom - y_top) // 2
                draw_destonation_point(x_center, y_center)

        def draw_vertical_road(horizontal_idx, vertical_idx):
            x_left = self.x0 + self.idx_to_x(horizontal_idx) * self.scale
            x_right = self.x0 + self.idx_to_x(horizontal_idx + 1) * self.scale
            y_top = self.y0 + self.idx_to_y(vertical_idx) * self.scale
            y_bottom = self.y0 + self.idx_to_y(vertical_idx + 1) * self.scale

            draw_rectangle(x_left, y_top, x_right, y_bottom, "gray", "gray")

            # x_center = x_left + (x_right - x_left) // 2

            # рисуем центральную линию: двойная сполшная и т.д.
            # if self.wp * self.scale > 5:
            #     draw.line((x_center - 1.3 * self.scale, y_top, x_center - 1.3 * self.scale, y_bottom), aggdraw.Pen("white", 1 * self.scale))
            #     draw.line((x_center + 1.3 * self.scale, y_top, x_center + 1.3 * self.scale, y_bottom), aggdraw.Pen("white", 1 * self.scale))

            # количество полос сверху
            left_top_count = get_left_count(vertical_idx, horizontal_idx)
            right_top_count = get_right_count(vertical_idx, horizontal_idx)
            left_bottom_count = get_left_count(vertical_idx + 1, horizontal_idx) if is_road(vertical_idx + 1, horizontal_idx) else get_left_count(vertical_idx, horizontal_idx)
            right_bottom_count = get_right_count(vertical_idx + 1, horizontal_idx) if is_road(vertical_idx + 1, horizontal_idx) else get_right_count(vertical_idx, horizontal_idx)

            # координаты для травы
            x_left_top_grass = x_left + self.wp * left_top_count * self.scale
            x_left_bottom_grass = x_left + self.wp * left_bottom_count * self.scale
            x_right_top_grass = x_right - self.wp * right_top_count * self.scale
            x_right_bottom_grass = x_right - self.wp * right_bottom_count * self.scale

            for i in range(1, 10):
                draw_vertical_dash_line(x_left + i * self.wp * self.scale, y_top, y_bottom)

            draw_grass(x_left_top_grass, y_top, x_right_top_grass, y_top, x_right_bottom_grass, y_bottom, x_left_bottom_grass, y_bottom)
            draw.line((x_left_top_grass, y_top, x_left_bottom_grass, y_bottom), aggdraw.Pen("black", 1.5 * self.scale))
            draw.line((x_right_top_grass, y_top, x_right_bottom_grass, y_bottom), aggdraw.Pen("black", 1.5 * self.scale))

            if MapVizualization.has_finish and MapVizualization.i_finish == vertical_idx and MapVizualization.j_finish == horizontal_idx:
                x_center = x_left + (x_right - x_left) // 2
                y_center = y_top + (y_bottom - y_top) // 2
                draw_destonation_point(x_center, y_center)

        def draw_horizontal_road(horizontal_idx, vertical_idx):
            x_left = self.x0 + self.idx_to_x(horizontal_idx) * self.scale
            x_right = self.x0 + self.idx_to_x(horizontal_idx + 1) * self.scale
            y_top = self.y0 + self.idx_to_y(vertical_idx) * self.scale
            y_bottom = self.y0 + self.idx_to_y(vertical_idx + 1) * self.scale

            draw_rectangle(x_left, y_top, x_right, y_bottom, "gray", "gray")

            # y_center = y_top + (y_bottom - y_top) // 2

            # рисуем центральную линию: двойная сполшная и т.д.
            # if (self.wp * self.scale > 5):
            #     draw.line((x_left, y_center - 1.3 * self.scale, x_right, y_center - 1.3 * self.scale), aggdraw.Pen("white", 1 * self.scale))
            #     draw.line((x_left, y_center + 1.3 * self.scale, x_right, y_center + 1.3 * self.scale), aggdraw.Pen("white", 1 * self.scale))

            # количество полос сверху
            left_top_count = get_right_count(vertical_idx, horizontal_idx)
            left_bottom_count = get_left_count(vertical_idx, horizontal_idx)

            right_top_count = get_right_count(vertical_idx, horizontal_idx + 1) if is_road(vertical_idx, horizontal_idx + 1) else get_right_count(vertical_idx, horizontal_idx)
            right_bottom_count = get_left_count(vertical_idx, horizontal_idx + 1) if is_road(vertical_idx, horizontal_idx + 1) else get_left_count(vertical_idx, horizontal_idx)

            # координаты для травы
            y_left_top_grass = y_top + self.wp * left_top_count * self.scale
            y_right_top_grass = y_top + self.wp * right_top_count * self.scale
            y_left_bottom_grass = y_bottom - self.wp * left_bottom_count * self.scale
            y_right_bottom_grass = y_bottom - self.wp * right_bottom_count * self.scale

            for i in range(1, 10):
                draw_horizontal_dash_line(x_left, x_right, y_top + i * self.wp * self.scale)

            draw_grass(x_left, y_left_top_grass, x_right, y_right_top_grass, x_right, y_right_bottom_grass, x_left, y_left_bottom_grass)
            draw.line((x_left, y_left_top_grass, x_right, y_right_top_grass), aggdraw.Pen("black", 1.5 * self.scale))
            draw.line((x_right, y_right_bottom_grass, x_left, y_left_bottom_grass), aggdraw.Pen("black", 1.5 * self.scale))

            if MapVizualization.has_finish and MapVizualization.i_finish == vertical_idx and MapVizualization.j_finish == horizontal_idx:
                x_center = x_left + (x_right - x_left) // 2
                y_center = y_top + (y_bottom - y_top) // 2
                draw_destonation_point(x_center, y_center)

        image = Image.new("RGBA", (self.horizontal_window, self.vertical_window), (36, 119, 25, 1))
        draw = aggdraw.Draw(image)

        for i in range(MapVizualization.city.shape[0]):
            for j in range(MapVizualization.city.shape[1]):
                if isinstance(MapVizualization.city.city_model[i][j], Road):
                    if MapVizualization.city.city_model[i][j].orientation == "v":
                        draw_vertical_road(j, i)
                    else:
                        draw_horizontal_road(j, i)

                elif isinstance(MapVizualization.city.city_model[i][j], Intersection):
                    draw_intersection(j, i)
                else:
                    draw_ground(j, i)

        draw.flush()
        self.tk_image = ImageTk.PhotoImage(image)
        self.canvas.create_image((0, 0), anchor='nw', image=self.tk_image)

    def draw_agent(self):

        def get_center():
            x_left = self.x0 + self.idx_to_x(MapVizualization.j_agent) * self.scale
            x_right = self.x0 + self.idx_to_x(MapVizualization.j_agent + 1) * self.scale
            y_top = self.y0 + self.idx_to_y(MapVizualization.i_agent) * self.scale
            y_bottom = self.y0 + self.idx_to_y(MapVizualization.i_agent + 1) * self.scale

            x_center = x_left + (x_right - x_left) // 2
            y_center = y_top + (y_bottom - y_top) // 2

            return x_center, y_center

        def get_agent_canvas(x, y):
            if MapVizualization.agent_direction == "N":
                x_left = x + (self.horizontal * 0.5 - (self.agent_lane_number + 1) * self.wp) * self.scale
                y_top = y - (self.vertical // self.drawAgentCount * MapVizualization.agent_position + self.wp) * self.scale
                return x_left, y_top, round(self.wp * self.scale), round(self.wp * 2 * self.scale)

            elif MapVizualization.agent_direction == "S":
                x_left = x - (self.horizontal * 0.5 - self.agent_lane_number * self.wp) * self.scale
                y_top = y + (self.vertical // self.drawAgentCount * MapVizualization.agent_position - self.wp) * self.scale
                return x_left, y_top, round(self.wp * self.scale), round(self.wp * 2 * self.scale)

            elif MapVizualization.agent_direction == "W":
                y_top = y - (self.vertical * 0.5 - self.agent_lane_number * self.wp) * self.scale
                x_left = x - (self.horizontal // self.drawAgentCount * MapVizualization.agent_position + self.wp) * self.scale
                return x_left, y_top, round(self.wp * 2 * self.scale), round(self.wp * self.scale)

            elif MapVizualization.agent_direction == "E":
                y_top = y + (self.vertical * 0.5 - (self.agent_lane_number + 1) * self.wp) * self.scale
                x_left = x + (self.horizontal // self.drawAgentCount * MapVizualization.agent_position - self.wp) * self.scale
                return x_left, y_top, round(self.wp * 2 * self.scale), round(self.wp * self.scale)

        def draw_vehicle(width, height):
            if MapVizualization.agent_direction == "N":
                x_middle = width / 2
                y_middle = x_middle

                points = (0, height,
                          0, y_middle,
                          x_middle, 0,
                          width, y_middle,
                          width, height)
                draw_agent.polygon(points, aggdraw.Pen("black", 0.5), aggdraw.Brush("red"))

            elif MapVizualization.agent_direction == "S":
                x_middle = width / 2
                y_middle = height - x_middle

                points = (width, 0,
                          width, y_middle,
                          x_middle, height,
                          0, y_middle,
                          0, 0)
                draw_agent.polygon(points, aggdraw.Pen("black", 0.5), aggdraw.Brush("red"))

            elif MapVizualization.agent_direction == "W":
                y_middle = height / 2
                x_middle = y_middle

                points = (width, height,
                          x_middle, height,
                          0, y_middle,
                          x_middle, 0,
                          width, 0)
                draw_agent.polygon(points, aggdraw.Pen("black", 0.5), aggdraw.Brush("red"))

            elif MapVizualization.agent_direction == "E":
                y_middle = height / 2
                x_middle = width - y_middle

                points = (0, 0,
                          x_middle, 0,
                          width, y_middle,
                          x_middle, height,
                          0, height)
                draw_agent.polygon(points, aggdraw.Pen("black", 0.5), aggdraw.Brush("red"))

        if MapVizualization.has_agent:
            x_center, y_center = get_center()
            x_left, y_top, canvas_width, canvas_height = get_agent_canvas(x_center, y_center)

            image_agent = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
            draw_agent = aggdraw.Draw(image_agent)
            draw_vehicle(canvas_width, canvas_height)

            draw_agent.flush()
            self.tk_imageAgent = ImageTk.PhotoImage(image_agent)
            self.canvas.create_image((x_left, y_top), anchor='nw', image=self.tk_imageAgent)

    def update_content(self, x, y):
        new_x0 = self.x0 + x - self.x_mouse
        if new_x0 > 0:
            new_x0 = 0
        if self.horizontal_window * self.scale - abs(new_x0) < self.horizontal_window:
            new_x0 = self.horizontal_window - self.horizontal_window * self.scale

        new_y0 = self.y0 + y - self.y_mouse
        if new_y0 > 0:
            new_y0 = 0
        if self.vertical_window * self.scale - abs(new_y0) < self.vertical_window:
            new_y0 = self.vertical_window - self.vertical_window * self.scale

        self.x0 = new_x0
        self.y0 = new_y0
        self.draw_content()
        self.draw_agent()

    def canvas_mouse_wheel_event(self, event):
        # respond to Linux or Windows wheel event
        if event.num == 5 or event.delta == -120:
            if self.scale > 1:
                self.scale -= 0.1
                self.draw_content()
                self.draw_agent()
        if event.num == 4 or event.delta == 120:
            self.scale += 0.1
            self.draw_content()
            self.draw_agent()

    def canvas_motion_event(self, event):
        if self.move_mode:
            self.update_content(event.x, event.y)
        self.x_mouse = event.x
        self.y_mouse = event.y

    def canvas_button_press_event(self, event):
        if self.scale > 1:
            self.move_mode = True
        self.x_mouse = event.x
        self.y_mouse = event.y

    def canvas_button_release_event(self, event):
        self.something_clicked = 0
        self.move_mode = False
        self.update_content(event.x, event.y)

    def canvas_resize_event(self, event):
        [self.horizontal_window, self.vertical_window] = event.width, event.height
        self.set_block_size()
        self.draw_content()
        self.draw_agent()

    @staticmethod
    def callback_agent_draw(state: State):
        MapVizualization.i_finish = state.destination_coordinates.axis0
        MapVizualization.j_finish = state.destination_coordinates.axis1
        MapVizualization.has_finish = True
        MapVizualization.i_agent = state.car_coordinates.axis0
        MapVizualization.j_agent = state.car_coordinates.axis1
        MapVizualization.agent_direction = state.current_direction
        MapVizualization.agent_lane_number = state.current_lane
        MapVizualization.agent_position = 0
        MapVizualization.has_agent = True
