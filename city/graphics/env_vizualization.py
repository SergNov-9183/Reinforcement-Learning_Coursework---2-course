import aggdraw
from Environment.city import City
from Environment.objects.road import Road
from Environment.objects.intersection import Intersection
import tkinter as tk
from tkinter import Canvas
from PIL import Image, ImageTk
from PIL import Image, ImageColor
from PIL import ImageDraw
from threading import Thread
from time import sleep
from Environment.model.state import State


class ThreadUpdater(Thread):
    def __init__(self, map):
        super().__init__()
        self.map = map

    def run(self) -> None:
        while self.map.running:
            self.map.drawAgent()
            print("running")
            sleep(1)

class MapVizualization(tk.Tk):
    running = True

    hasFinish = False
    iFinish = 0
    jFinish = 0

    hasAgent = False
    iAgent = 0
    jAgent = 0

    x0 = 0
    y0 = 0

    xMouse = 0
    yMouse = 0

    scale = 1

    moveMode = False

    horizontalWindow = 2560 // 3 * 2
    verticalWindow = 1440 // 3 * 2

    # def threaded_function(self):
    #     while self.running:
    #         print("running")
    #         sleep(1)
    #
    # def run(self) -> None:
    #     while self.running:
    #         print("running")
    #         sleep(1)

    def __init__(self, env: City):
        super().__init__()

        self.title("env_visualization")

        self.canvas = Canvas(self, width=self.horizontalWindow, height=self.verticalWindow, bg="#247719")
        self.canvas.pack(expand=1,fill=tk.BOTH)


        self.city = env
        #self.city = City(map_sample=2, layout_sample=0, narrowing_and_expansion=True)

        self.setBlockSize()
        self.drawContent()
        self.drawAgent()

        self.canvas.bind('<MouseWheel>', self.canvas_mouseWheel_event)
        self.canvas.bind('<Motion>', self.canvas_motion_event)
        self.canvas.bind('<ButtonPress-1>', self.canvas_buttonPress_event)
        self.canvas.bind('<ButtonRelease-1>', self.canvas_buttonRelease_event)
        self.canvas.bind("<Configure>", self.canvas_resize_event)

        self.thread = ThreadUpdater(self)
        self.thread.start()

    def clear(self):
        print("del map")
        self.running = False
        self.thread.join()

    def setBlockSize(self):
        if self.verticalWindow < self.horizontalWindow:
            self.vertical = self.verticalWindow // self.city.shape[0]
            self.horizontal = self.verticalWindow // self.city.shape[1]
        else:
            self.vertical = self.horizontalWindow // self.city.shape[0]
            self.horizontal = self.horizontalWindow // self.city.shape[1]

        self.wp = self.vertical // 10

    def idxToX(self, idx):
        return idx * self.horizontal

    def idxToY(self, idx):
        return idx * self.vertical

    def drawContent(self):
        def drawRectangle(xLeft, yTop, xRight, yBottom, fillColor, lineColor):
            draw.rectangle((xLeft, yTop, xRight, yBottom), aggdraw.Pen(lineColor, 0.5), aggdraw.Brush(fillColor))

        def drawGrass(x0, y0, x1, y1, x2, y2, x3, y3):
            draw.polygon((x0, y0, x1, y1, x2, y2, x3, y3), aggdraw.Pen("#247719", 0.5),aggdraw.Brush("#247719"))

        def isRoad(i, j):
            return ((i > 0) and (i <= self.city.shape[0]) and (j > 0) and (j <= self.city.shape[1]) and (isinstance(self.city.city_model[i][j], Road)))

        def getLeftCount(i, j):
            return [len(value) for key, value in self.city.city_model[i][j].lanes.items()][1]

        def getRightCount(i, j):
            return [len(value) for key, value in self.city.city_model[i][j].lanes.items()][0]

        def drawGround(horizontalIdx, verticalIdx):
            xLeft = self.x0 + self.idxToX(horizontalIdx) * self.scale
            xRight = self.x0 + self.idxToX(horizontalIdx + 1) * self.scale
            yTop = self.y0 + self.idxToY(verticalIdx) * self.scale
            yBottom = self.y0 + self.idxToY(verticalIdx + 1) * self.scale

            drawRectangle(xLeft, yTop, xRight, yBottom, "#247719", "#247719")

        def drawIntersection(horizontalIdx, verticalIdx):
            xLeft = self.x0 + self.idxToX(horizontalIdx) * self.scale
            xRight = self.x0 + self.idxToX(horizontalIdx + 1) * self.scale
            yTop = self.y0 + self.idxToY(verticalIdx) * self.scale
            yBottom = self.y0 + self.idxToY(verticalIdx + 1) * self.scale

            drawRectangle(xLeft, yTop, xRight, yBottom, "#247719", "#247719")

            xCenter = xLeft + (xRight - xLeft) // 2
            yCenter = yTop + (yBottom - yTop) // 2

            xLeftTop = xCenter
            xRightTop = xCenter
            if (isRoad(verticalIdx - 1, horizontalIdx)):
                xLeftTop = xCenter - self.wp * getLeftCount(verticalIdx - 1, horizontalIdx) * self.scale
                xRightTop = xCenter + self.wp * getRightCount(verticalIdx - 1, horizontalIdx) * self.scale
            elif (isRoad(verticalIdx + 1, horizontalIdx)):
                xLeftTop = xCenter - self.wp * getLeftCount(verticalIdx + 1, horizontalIdx) * self.scale
                xRightTop = xCenter + self.wp * getRightCount(verticalIdx + 1, horizontalIdx) * self.scale

            xLeftBottom = xCenter
            xRightBottom = xCenter
            if (isRoad(verticalIdx + 1, horizontalIdx)):
                xLeftBottom = xCenter - self.wp * getLeftCount(verticalIdx + 1, horizontalIdx) * self.scale
                xRightBottom = xCenter + self.wp * getRightCount(verticalIdx + 1, horizontalIdx) * self.scale
            elif (isRoad(verticalIdx - 1, horizontalIdx)):
                xLeftBottom = xCenter - self.wp * getLeftCount(verticalIdx - 1, horizontalIdx) * self.scale
                xRightBottom = xCenter + self.wp * getRightCount(verticalIdx - 1, horizontalIdx) * self.scale

            yLeftTop = yCenter
            yLeftBottom = yCenter
            if (isRoad(verticalIdx, horizontalIdx - 1)):
                yLeftTop = yCenter - self.wp * getLeftCount(verticalIdx, horizontalIdx - 1) * self.scale
                yLeftBottom = yCenter + self.wp * getRightCount(verticalIdx, horizontalIdx - 1) * self.scale
            elif (isRoad(verticalIdx, horizontalIdx + 1)):
                yLeftTop = yCenter - self.wp * getLeftCount(verticalIdx, horizontalIdx + 1) * self.scale
                yLeftBottom = yCenter + self.wp * getRightCount(verticalIdx, horizontalIdx + 1) * self.scale

            yRightTop = yCenter
            yRightBottom = yCenter
            if (isRoad(verticalIdx, horizontalIdx + 1)):
                yRightTop = yCenter - self.wp * getLeftCount(verticalIdx, horizontalIdx + 1) * self.scale
                yRightBottom = yCenter + self.wp * getRightCount(verticalIdx, horizontalIdx + 1) * self.scale
            elif (isRoad(verticalIdx, horizontalIdx - 1)):
                yRightTop = yCenter - self.wp * getLeftCount(verticalIdx, horizontalIdx - 1) * self.scale
                yRightBottom = yCenter + self.wp * getRightCount(verticalIdx, horizontalIdx - 1) * self.scale

            if (not isRoad(verticalIdx - 1, horizontalIdx)):
                yTop = yRightTop

            if (not isRoad(verticalIdx + 1, horizontalIdx)):
                yBottom = yRightBottom

            if (not isRoad(verticalIdx, horizontalIdx - 1)):
                xLeft = xLeftBottom

            if (not isRoad(verticalIdx, horizontalIdx + 1)):
                xRight = xRightBottom

            points = [xLeft, yLeftTop,
                      xLeftTop, yLeftTop,
                      xLeftTop, yTop,
                      xRightTop, yTop,
                      xRightTop, yRightTop,
                      xRight, yRightTop,
                      xRight, yRightBottom,
                      xRightBottom, yRightBottom,
                      xRightBottom, yBottom,
                      xLeftBottom, yBottom,
                      xLeftBottom, yLeftBottom,
                      xLeft, yLeftBottom]

            draw.polygon((points), aggdraw.Pen("gray", 0.5),aggdraw.Brush("gray"))

        def drawVerticalRoad(horizontalIdx, verticalIdx):
            xLeft = self.x0 + self.idxToX(horizontalIdx) * self.scale
            xRight = self.x0 + self.idxToX(horizontalIdx + 1) * self.scale
            yTop = self.y0 + self.idxToY(verticalIdx) * self.scale
            yBottom = self.y0 + self.idxToY(verticalIdx + 1) * self.scale

            drawRectangle(xLeft, yTop, xRight, yBottom, "gray", "gray")

            xCenter = xLeft + (xRight - xLeft) // 2

            # рисуем центральную линию: двойная сполшная и т.д.
            # пунктирная линия - параметр dash=(15, 15)
            if (self.wp * self.scale > 5):
                draw.line((xCenter - 1.3 * self.scale, yTop, xCenter - 1.3 * self.scale, yBottom), aggdraw.Pen("white", 1 * self.scale))
                draw.line((xCenter + 1.3 * self.scale, yTop, xCenter + 1.3 * self.scale, yBottom), aggdraw.Pen("white", 1 * self.scale))

            # количество полос сверху
            leftTopCount = getLeftCount(verticalIdx, horizontalIdx)
            rightTopCount = getRightCount(verticalIdx, horizontalIdx)
            leftBottomCount = getLeftCount(verticalIdx + 1, horizontalIdx) if isRoad(verticalIdx + 1, horizontalIdx) else getLeftCount(verticalIdx, horizontalIdx)
            rightBottomCount = getRightCount(verticalIdx + 1, horizontalIdx) if isRoad(verticalIdx + 1, horizontalIdx) else getRightCount(verticalIdx, horizontalIdx)
            # print(f"LeftTopCount = {leftTopCount}, rightTopCount = {rightTopCount}, leftBottomCount = {leftBottomCount}, rightBottomCount = {rightBottomCount}")

            # координаты для травы
            xLeftTopGrass = xCenter - self.wp * leftTopCount * self.scale
            xLeftBottomGrass = xCenter - self.wp * leftBottomCount * self.scale
            xRightTopGrass = xCenter + self.wp * rightTopCount * self.scale
            xRightBottomGrass = xCenter + self.wp * rightBottomCount * self.scale

            drawGrass(xLeft, yTop, xLeftTopGrass, yTop, xLeftBottomGrass, yBottom, xLeft, yBottom)
            drawGrass(xRight, yTop, xRightTopGrass, yTop, xRightBottomGrass, yBottom, xRight, yBottom)

        def drawHorizontalRoad(horizontalIdx, verticalIdx):
            xLeft = self.x0 + self.idxToX(horizontalIdx) * self.scale
            xRight = self.x0 + self.idxToX(horizontalIdx + 1) * self.scale
            yTop = self.y0 + self.idxToY(verticalIdx) * self.scale
            yBottom = self.y0 + self.idxToY(verticalIdx + 1) * self.scale

            drawRectangle(xLeft, yTop, xRight, yBottom, "gray", "gray")

            yCenter = yTop + (yBottom - yTop) // 2

            # рисуем центральную линию: двойная сполшная и т.д.
            # пунктирная линия - параметр dash=(15, 15)
            if (self.wp * self.scale > 5):
                draw.line((xLeft, yCenter - 1.3 * self.scale, xRight, yCenter - 1.3 * self.scale), aggdraw.Pen("white", 1 * self.scale))
                draw.line((xLeft, yCenter + 1.3 * self.scale, xRight, yCenter + 1.3 * self.scale), aggdraw.Pen("white", 1 * self.scale))

            # количество полос сверху
            leftTopCount = getLeftCount(verticalIdx, horizontalIdx)
            leftBottomCount = getRightCount(verticalIdx, horizontalIdx)

            rightTopCount = getLeftCount(verticalIdx, horizontalIdx + 1) if isRoad(verticalIdx, horizontalIdx + 1) else getLeftCount(verticalIdx, horizontalIdx)
            rightBottomCount = getRightCount(verticalIdx, horizontalIdx + 1) if isRoad(verticalIdx, horizontalIdx + 1) else getRightCount(verticalIdx, horizontalIdx)
            # print(f"LeftTopCount = {leftTopCount}, rightTopCount = {rightTopCount}, leftBottomCount = {leftBottomCount}, rightBottomCount = {rightBottomCount}")

            # координаты для травы
            yLeftTopGrass = yCenter - self.wp * leftTopCount * self.scale
            yRightTopGrass = yCenter - self.wp * rightTopCount * self.scale
            yLeftBottomGrass = yCenter + self.wp * leftBottomCount * self.scale
            yRightBottomGrass = yCenter + self.wp * rightBottomCount * self.scale

            drawGrass(xLeft, yLeftTopGrass, xLeft, yTop, xRight, yTop, xRight, yRightTopGrass)
            drawGrass(xLeft, yLeftBottomGrass, xLeft, yBottom, xRight, yBottom, xRight, yRightBottomGrass)

        image = Image.new("RGBA", (self.horizontalWindow, self.verticalWindow), (36, 119, 25, 1))
        draw = aggdraw.Draw(image)

        for i in range(self.city.shape[0]):
            for j in range(self.city.shape[1]):
                # print("Object ", i, j, "is a road", self.city.city_model[i][j], ": orientation is ", self.city.city_model[i][j].orientation, ", lanes dict: ", self.city.city_model[i][j].lanes,
                #       ", hard marking line type: ", self.city.city_model[i][j].hard_marking, ", soft marking line type: ",
                #       self.city.city_model[i][j].soft_marking, ".") if isinstance(self.city.city_model[i][j], Road) else print(
                #     "Object ", i, j, "is an intersection ", self.city.city_model[i][j], ": lanes count in directions: ",
                #     self.city.city_model[i][j].n_lanes) if isinstance(self.city.city_model[i][j], Intersection) else print(
                #     "Object ", i, j, " is a ground", self.city.city_model[i][j])
                if (isinstance(self.city.city_model[i][j], Road)):

                    if (self.city.city_model[i][j].orientation == "v"):
                        drawVerticalRoad(j, i)
                    else:
                        drawHorizontalRoad(j, i)

                elif (isinstance(self.city.city_model[i][j], Intersection)):
                    drawIntersection(j, i)
                else:
                    drawGround(j, i)

        draw.flush()
        self.tk_image = ImageTk.PhotoImage(image)
        self.canvas.create_image((0, 0), anchor='nw' ,image=self.tk_image)

    def drawAgent(self):
        def draw_destonation_point(x, y):
            print(x, y)
            yTop = y - (4 * self.wp) * self.scale
            yBottom = y - (1 * self.wp) * self.scale
            xRight = x + (3 *self.wp) * self.scale
            yRight = y - (2.5 * self.wp) * self.scale
            points = [x, yBottom,
                      x, yTop,
                      xRight, yRight]

            drawAgent.polygon((points), aggdraw.Pen("red", 0.5),aggdraw.Brush("red"))
            drawAgent.line((x, y, x, yTop), aggdraw.Pen("black", 1.5 * self.scale))

        def draw_wehicle(x, y):
            xLeft = x - (0.5 *self.wp) *self.scale
            xRight = x + (0.5 *self.wp) *self.scale
            yTop = y - (0.5 * self.wp) * self.scale
            yBottom = y + (0.5 * self.wp) * self.scale
            drawAgent.rectangle((xLeft, yTop, xRight, yBottom), aggdraw.Pen("red", 0.5), aggdraw.Brush("red"))

        def drawBlock(horizontalIdx, verticalIdx):
            xLeft = self.x0 + self.idxToX(horizontalIdx) * self.scale
            xRight = self.x0 + self.idxToX(horizontalIdx + 1) * self.scale
            yTop = self.y0 + self.idxToY(verticalIdx) * self.scale
            yBottom = self.y0 + self.idxToY(verticalIdx + 1) * self.scale

            xCenter = xLeft + (xRight - xLeft) // 2
            yCenter = yTop + (yBottom - yTop) // 2

            if MapVizualization.hasFinish and MapVizualization.iFinish == verticalIdx and MapVizualization.jFinish == horizontalIdx:
                draw_destonation_point(xCenter, yCenter)

            if MapVizualization.hasAgent and MapVizualization.iAgent == verticalIdx and MapVizualization.jAgent == horizontalIdx:
                draw_wehicle(xCenter, yCenter)

        imageAgent = Image.new("RGBA", (self.horizontalWindow, self.verticalWindow), (0, 0, 0, 0))
        drawAgent = aggdraw.Draw(imageAgent)

        for i in range(self.city.shape[0]):
            for j in range(self.city.shape[1]):
                drawBlock(j, i)

        drawAgent.flush()
        self.tk_imageAgent = ImageTk.PhotoImage(imageAgent)
        self.canvas.create_image((0, 0), anchor='nw', image=self.tk_imageAgent)




    def updateContent(self, x, y):

        newX0 = self.x0 + x - self.xMouse
        if(newX0 > 0):
            newX0 = 0
        if(self.horizontalWindow * self.scale - abs(newX0) < self.horizontalWindow):
            newX0 = self.horizontalWindow - self.horizontalWindow * self.scale

        newY0 = self.y0 + y - self.yMouse
        if(newY0 > 0):
            newY0 = 0
        if(self.verticalWindow * self.scale - abs(newY0) < self.verticalWindow):
            newY0 = self.verticalWindow - self.verticalWindow * self.scale

        self.x0 = newX0
        self.y0 = newY0
        self.drawContent()
        self.drawAgent()

    def canvas_mouseWheel_event(self, event):
        # respond to Linux or Windows wheel event
        if event.num == 5 or event.delta == -120:
            if self.scale > 1:
                self.scale -= 0.1
                self.drawContent()
                self.drawAgent()
        if event.num == 4 or event.delta == 120:
            self.scale += 0.1
            self.drawContent()
            self.drawAgent()
        print('Scale: ', self.scale)

    def canvas_motion_event(self, event):
        if self.moveMode:
            self.updateContent(event.x, event.y)
        self.xMouse = event.x
        self.yMouse = event.y
        # print('Motion: ', event.x, event.y)

    def canvas_buttonPress_event(self, event):
        self.something_clicked = 0
        if self.scale > 1:
            self.moveMode = True
        self.xMouse = event.x
        self.yMouse = event.y
        print('ButtonPress: ', event.x, event.y)

    def canvas_buttonRelease_event(self, event):
        self.something_clicked = 0
        self.moveMode = False
        self.updateContent(event.x, event.y)
        print('ButtonRelease: ', event.x, event.y)

    def canvas_resize_event(self, event):
        self.horizontalWindow, self.verticalWindow = event.width, event.height
        self.setBlockSize()
        self.drawContent()
        self.drawAgent()

    @staticmethod
    def callback_agent_draw( state:State):
        print(r"ВЫВОД ДЛЯ ГРАФИКИ!!! -----------------------------------------  \\\\\\")
        print(f'state status : {state} \n\n agent destonation coordinate x is {state.destination_coordinates[0]}, agent destonation coordinates y is {state.destination_coordinates[1]}')
        MapVizualization.iFinish = state.destination_coordinates.axis0
        MapVizualization.jFinish = state.destination_coordinates.axis1
        MapVizualization.hasFinish = True
        MapVizualization.hasAgent = True
        MapVizualization.iAgent = state.car_coordinates.axis0
        MapVizualization.jAgent = state.car_coordinates.axis1
        print(r"ВЫВОД ДЛЯ ГРАФИКИ!!! -----------------------------------------  //////")


