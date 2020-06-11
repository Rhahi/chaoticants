import pygame as pg
import numpy as np
import random
import sys
import pdb

class CameraOptions:
    def __init__(self):
        self.mouse_scroll_speed = 800
        self.key_scroll_speed = 0.3  # lower is faster

class Camera:
    #  TODO: make controls depend on time between draws to unlink from frame rate
    def __init__(self, screensize = (1024,800), camera_options = None):
        if camera_options:
            self.camera_options = camera_options
        else:
            self.camera_options = CameraOptions()
        self.screensize = screensize
        self.aspect = screensize[0] / screensize[1]
        self.zoomlevel = 200  # how many integer points to fit on x-axis
        self.middle = np.array((0.0, 0.0))
        self.previous_mouse_motion = None
        self.wasd_state = [False]*4

    def tick(self, delta):
        W = 0
        A = 1
        S = 2
        D = 3
        scroll_dir = np.array([0, 0])
        if self.wasd_state[W]:
            scroll_dir[1] += -1
        if self.wasd_state[A]:
            scroll_dir[0] += -1
        if self.wasd_state[S]:
            scroll_dir[1] += +1
        if self.wasd_state[D]:
            scroll_dir[0] += +1
        self.scroll(scroll_dir, self.camera_options.key_scroll_speed * delta)
        


    def get_zoom(self):
        width = self.screensize[0] / (self.zoomlevel / 2)
        height = self.screensize[1] / (self.zoomlevel / 2)
        return int(width), int(height)

    def get_world_coordinate_bounds(self):
        assert(self.zoomlevel >= 1)
        x = self.middle[0]
        y = self.middle[1]
        xleft = x - self.zoomlevel / 2
        xright = x + self.zoomlevel / 2
        ytop = y - self.zoomlevel / 2 / self.aspect
        ybottom = y + self.zoomlevel / 2 / self.aspect
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

    def screen_to_world_coordinate(self, screenpos):
        x = screenpos[0]
        y = screenpos[1]
        x_scale = self.zoomlevel
        y_scale = self.zoomlevel / self.aspect
        xleft, _, ytop, _ = self.get_world_coordinate_bounds()
        x_ratio = x / self.screensize[0]
        y_ratio = y / self.screensize[1]
        world_x = xleft + x_ratio * x_scale
        world_y = ytop + y_ratio * y_scale
        return world_x, world_y

    def scroll(self, direction, strength):
        if direction.any():
            self.middle += direction * self.zoomlevel / strength

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:  # left mouse button
                self.previous_mouse_motion = np.array(event.pos)
            elif event.button == 3:  # right mouse button:
                print(self.screen_to_world_coordinate(event.pos))
            elif event.button == 5:  # mousewheel scrolling down
                self.zoomlevel = min(300, self.zoomlevel*1.2)
            elif event.button == 4:  # mousewheel scrolling up
                self.zoomlevel = max(self.zoomlevel*0.8, 1)
        elif event.type == pg.MOUSEMOTION:
            if pg.mouse.get_pressed()[0]:
                pos = np.array(event.pos)
                direction = (self.previous_mouse_motion - pos)
                self.previous_mouse_motion = pos
                self.scroll(direction, self.camera_options.mouse_scroll_speed)
        elif event.type == pg.KEYDOWN or event.type == pg.KEYUP:
            if event.key == pg.K_w:
                self.wasd_state[0] = event.type == pg.KEYDOWN
            if event.key == pg.K_a:
                self.wasd_state[1] = event.type == pg.KEYDOWN
            if event.key == pg.K_s:
                self.wasd_state[2] = event.type == pg.KEYDOWN
            if event.key == pg.K_d:
                self.wasd_state[3] = event.type == pg.KEYDOWN

class Profiler:
    def __init__(self):
        self.enabled = False
        self.start_times = {}
        self.end_times = {}
        
    
    def start_profiling(self, subject):
        if not self.enabled:
            return
        self.start_times[subject] = pg.time.get_ticks()
            
    def end_profiling(self, subject):
        if not self.enabled:
            return
        self.end_times[subject] = pg.time.get_ticks()

    def report_profiling(self):
        if not self.enabled:
            return

        times = {}
        for subject in self.start_times:
            if subject in self.end_times:
                times[subject] = self.end_times[subject] - self.start_times[subject]

        if len(times) == 0:
            print("Want to report profiling but no good data captured")
            return

        self.data = {}
        sorted_times = sorted(times.items(), key = lambda t: -t[1])
        slowest = None
        for subject, time in sorted_times:
            if not slowest:
                slowest = time
            print(f"Profiling: {subject} took {time} ms which is {(time/slowest):.2%} as slow as the slowest")
        print()

class PygameVisualizer:
    def __init__(self, targets, tickrate = 40, screensize = (1024, 800)):
        """ 
        targets is a list of tuples (entity, sprite) of what to draw. entity should have get_position(), and get_heading() functions
        sprites should be pointing to the right
        """
        pg.init()
        pg.display.set_caption("Ants")
        self.sprites = {}
        self.running = True
        self.tickrate = tickrate
        self.clock = pg.time.Clock()
        self.camera = Camera(screensize)
        self.screen = pg.display.set_mode(screensize)
        self.targets = targets
        self.delta = 0
        self.debug_mode = False
        self.profiler = Profiler()
        self.world_bounds = None
        self.debug_legend_data = {}
        self.debug_vector_scaling = 1000

    def __draw_pheromones(self, realm):
        xleft, xright, ytop, ybottom = map(int, self.world_bounds)
        array = realm.land[xleft+1:xright-1,ytop+1:ybottom-1]
        surf = pg.surfarray.make_surface(array)
        full_surf = pg.transform.scale(surf, self.screen.get_size())
        self.screen.blit(full_surf, (0, 0), special_flags=pg.BLEND_ADD)

    def __is_on_screen(self, pos):
        xleft, xright, ytop, ybottom = self.world_bounds
        x, y = pos
        return x > xleft and x < xright and y > ytop and y < ybottom

    def __draw_vector(self, pos, direction, magnitude, color):
        mag = magnitude * self.debug_vector_scaling / self.camera.zoomlevel
        res = np.e ** (2j * np.pi * direction)
        end_x = pos[0] + res.imag * mag
        end_y = pos[1] + res.real * mag
        pg.draw.aaline(self.screen, color, pos, (end_x, end_y))

    def __draw_legend(self, fontname = "arial", fontsize = 12):
        if not self.debug_mode or not self.debug_legend_data:
            return
        next_pos = (10, 10)
        for dd in self.debug_legend_data:
            font = pg.font.SysFont(fontname, fontsize)
            color = self.debug_legend_data[dd]["color"]
            text = font.render(dd, True, color)
            self.screen.blit(text, next_pos)
            next_pos = (0, text.get_height())
        
    def __draw_debug(self, ent, pos):
        if not self.debug_mode:
            return
        try:
            arrows = ent.get_arrows()
        except AttributeError:
            return
        for arrow_name in arrows:
            arrow = arrows[arrow_name]
            if arrow_name not in self.debug_legend_data:
                self.debug_legend_data[arrow_name] = arrow
            self.__draw_vector(pos, arrow["heading"], arrow["intensity"], arrow["color"])
        

        
    def __draw(self, realm=None):
        self.profiler.start_profiling("draw")
        self.screen.fill((34, 177, 76))
        if realm:
            self.profiler.start_profiling("pheromones")
            self.__draw_pheromones(realm)
            self.profiler.end_profiling("pheromones")

        self.profiler.start_profiling("entities")
        for entities, sprite_name in self.targets:
            if sprite_name not in self.sprites:
                self.sprites[sprite_name] = pg.image.load(sprite_name).convert_alpha()
            sprite = self.sprites[sprite_name]
            for ent in entities:
                x, y = ent.get_position()
                if self.__is_on_screen((x, y)):
                    pos = self.camera.world_to_screen_coordinate((x, y))
                    scaled = pg.transform.scale(sprite, self.camera.get_zoom())
                    rotated = pg.transform.rotate(scaled, ((270 + ent.get_heading()*360) % 360))
                    self.screen.blit(rotated, pos)
                    if self.debug_mode:
                        spritesize = scaled.get_size()
                        pos_middle = (pos[0] + spritesize[0]/2, pos[1] + spritesize[1]/2)
                        self.__draw_debug(ent, pos_middle)
                            
        self.profiler.end_profiling("entities")
        self.__draw_legend()
        pg.display.update()
        self.profiler.end_profiling("draw")

    def __handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
                sys.exit()
            elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.running = False
                sys.exit()
            elif (event.type == pg.KEYDOWN or event.type == pg.KEYUP) and event.key == pg.K_SPACE:
                self.debug_mode = event.type == pg.KEYDOWN
            elif (event.type == pg.KEYDOWN or event.type == pg.KEYUP) and event.key == pg.K_x:
                self.profiler.enabled = event.type == pg.KEYDOWN
            else:
                self.camera.handle_event(event)

    def tick(self, delta, realm=None):
        self.__handle_events()
        self.world_bounds = self.camera.get_world_coordinate_bounds()
        self.__draw(realm)
        self.camera.tick(delta)

    def step_frame(self, realm=None):
        self.tick(self.delta, realm)
        self.delta = self.clock.tick(self.tickrate)
        self.profiler.report_profiling()


class TestEntity:
    def __init__(self):
        self.x = random.randint(-50, 50)
        self.y = random.randint(-50, 50)
        self.heading = random.random()

    def get_position(self):
        return (self.x, self.y)

    def get_heading(self):
        return self.heading

    def walk(self):
        self.heading += random.uniform(-0.06, 0.06)
        step = np.e ** (2j * np.pi * self.heading)
        self.x += step.imag
        self.y += step.real


if __name__ == "__main__":
    entities = [TestEntity() for _ in range(20)]
    entities[0].x = 0
    entities[0].y = 0
    pgv = PygameVisualizer([(entities, "ant.png")]) #suggested ant: https://www.flaticon.com/free-icon/ant_355680
    #pgv = PygameVisualizer([(ants, "ant.png"), (colonies, "col.jpg"), (pheros, "pheromone.gif")]) <-- example of one way to initalize the class