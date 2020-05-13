import pygame as pg
import numpy as np
import random
import sys


class Camera:
    #  TODO: make controls depend on time between draws to unlink from frame rate
    def __init__(self, screensize = (1024,800), scrollspeed = 800):
        self.screensize = screensize
        self.aspect = screensize[0]/screensize[1]
        self.zoomlevel = 20  # how many integer points to fit on x-axis
        self.middle = np.array((0.0, 0.0))
        self.previous_mouse_motion = None
        self.scrollspeed = scrollspeed # higher is slower

    def get_zoom(self):
        width = self.screensize[0]/self.zoomlevel
        height = self.screensize[1]/self.zoomlevel
        return int(width), int(height)

    def get_world_coordinate_bounds(self):
        assert(self.zoomlevel >= 1)
        x = self.middle[0]
        y = self.middle[1]
        xleft = x - self.zoomlevel
        xright = x + self.zoomlevel
        ytop = y - self.zoomlevel/self.aspect
        ybottom = y + self.zoomlevel/self.aspect
        return np.array((xleft, xright, ytop, ybottom))

    def world_to_screen_coordinate(self, worldpos):
        xleft, xright, ytop, ybottom = self.get_world_coordinate_bounds()
        x = worldpos[0]
        y = worldpos[1]
        if x <= xleft or x >= xright or y >= ybottom or y <= ytop:
            raise ValueError("World coordinate outside screen")
        screen_x_percentage = (x - xleft) / (xright - xleft)
        screen_y_percentage = (y - ytop) / (ybottom - ytop)
        return (screen_x_percentage * self.screensize[0], screen_y_percentage * self.screensize[1])

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.previous_mouse_motion = np.array(event.pos)
            elif event.button == 5: #mousewheel scrolling down
                self.zoomlevel = min(300, self.zoomlevel*1.2)
            elif event.button == 4: #mousewheel scrolling up
                self.zoomlevel = max(self.zoomlevel*0.8, 1)
        elif event.type == pg.MOUSEMOTION:
            if pg.mouse.get_pressed()[0]:
                pos = np.array(event.pos)
                direction = (self.previous_mouse_motion - pos) * self.zoomlevel / self.scrollspeed
                self.previous_mouse_motion = pos
                self.middle += direction


class PygameEntity():
    def __init__(self, x, y, heading, image):
        self.x = x
        self.y = y
        self.image = image
        self.heading = heading

    def draw(self, surface, camera):
        pos = camera.world_to_screen_coordinate((self.x, self.y))
        scaled = pg.transform.scale(self.image, camera.get_zoom())
        rotated = pg.transform.rotate(scaled, ((270 + self.heading*360) % 360))
        surface.blit(rotated, pos)


class PygameVisualizer:
    def __init__(self, targets, tickrate = 20, screensize = (1024, 800)):
        """ 
        targets is a list of tuples (entity, sprite) of what to draw. entity should have x, y, and heading attributes
        sprites should be pointing to the right
        tickrate is how many times per second we will attempt to update and draw 
        """
        pg.init()
        pg.display.set_caption("Ants")
        self.running = True
        self.tickrate = tickrate
        self.clock = pg.time.Clock()
        self.camera = Camera(screensize)
        self.screen = pg.display.set_mode(screensize)
        self.entities = []
        for target in targets:
            entities, sprite = target
            sprite = pg.image.load(sprite).convert_alpha()
            for ent in entities:
                if type(ent) == dict:
                    self.entities.append(PygameEntity(ent["x"], ent["y"], ent["heading"], sprite))
                else:
                    self.entities.append(PygameEntity(ent.x, ent.y, ent.heading, sprite))

    def __draw(self):
        self.screen.fill((12, 156, 20))
        xleft, xright, ytop, ybottom = self.camera.get_world_coordinate_bounds()
        for ent in self.entities:
            if ent.x > xleft and ent.x < xright and ent.y > ytop and ent.y < ybottom:
                ent.draw(self.screen, self.camera)
        pg.display.update()

    def __handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
                sys.exit()
            elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.running = False
                sys.exit()
            else:
                self.camera.handle_event(event)

    def step_frame(self):
        self.__handle_events()
        self.__draw()
        self.clock.tick(self.tickrate)

    def run(self, updatefunc):
        """ Starts the visualizer, calling updatefunc once between every draw """
        if not callable(updatefunc):
            raise ValueError("updatefunc must be callable")
        while self.running:
            self.__handle_events()
            self.__draw()
            updatefunc(self.entities)
            self.clock.tick(self.tickrate)


class TestEntity:
    def __init__(self):
        self.x = random.randint(-50, 50)
        self.y = random.randint(-50, 50)
        self.heading = random.random()


def walk(entities):
    for ent in entities:
        ent.heading += random.uniform(-0.1, 0.1)
        step = np.e ** (2j * np.pi * ent.heading)
        ent.x += step.imag
        ent.y += step.real

if __name__ == "__main__":
    entities = [TestEntity() for _ in range(20)]
    entities[0].x = 0
    entities[0].y = 0
    pgv = PygameVisualizer([(entities, "ant.png")]) #suggested ant: https://www.flaticon.com/free-icon/ant_355680
    #pgv = PygameVisualizer([(ants, "ant.png"), (colonies, "col.jpg"), (pheros, "pheromone.gif")]) <-- example of one way to initalize the class
    pgv.run(walk)