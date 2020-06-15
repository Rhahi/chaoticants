import numpy as np
import antmath
from queue import SimpleQueue
from enum import Enum

class Food():
    def __init__(self, position, amount):
        self.position = position
        self.amount = amount

    def take(self, amount):
        taken = min(amount, self.amount)
        self.amount -= taken
        return taken

    def get_position(self):
        return (self.position[0], self.position[1])

    def get_heading(self):
        return 0.25

    def get_arrows(self):
        return {
            "food": {
                "heading": 0.25,
                "color": (120, 120, 0),
                "intensity": self.amount / 10
            }
        }

class Realm():
    """
    The world where our ants and nests live in.
    Time is defined here, so that we don't need to define a global time variable.
    """
    def __init__(self, size):
        self.time = 0
        self.time_increment = 1 # the amount of time to progress per tick.
        
        self.land = np.zeros(size)
        self.next_land_queue = SimpleQueue()

        self.evaporate_rate = 0.95 # TODO fix magic number
        self.food_list = []
        self.flag_food_removed = False

    def spawn_food(self, position, amount):
        self.food_list.append(Food(position, amount))

    def check_boundary(self, position):
        p = np.array(position)
        if (p > self.land.shape).any() or (p < np.array([0,0])).any():
            return False
        else:
            return True

    def update(self):
        """
        reduces the pheromone exponentially.
        """
        self.land = np.dot(self.land, self.evaporate_rate) # exponential decay
        while not self.next_land_queue.empty():
            p, a = self.next_land_queue.get()
            self.land[p] += a
        
        self.food_list[:] = [f for f in self.food_list if not np.isclose(f.amount, 0)]
        self.time += self.time_increment

class Entity():
    def __init__(self, realm):
        self.realm = realm
        self.states = {}
        self.next_states = {}

    def _create_state(self, key, value):
        self.states[key] = value
        self.next_states[key] = None

    def do(self):
        pass

    def update(self):
        """
        update all the pending state changes, and set the future states undefined.
        if the future state is undefined, that means nothing will be changed.
        """
        for key in self.states:
            if self.next_states[key] is not None:
                self.states[key] = self.next_states[key]
                self.next_states[key] = None
    
    def get_position(self):
        if "position" in self.states:
            return (self.states["position"][0], self.states["position"][1])
        else:
            raise ValueError("undefined position")

    def get_heading(self):
        return 0.25

    def get_arrows(self):
        return {}


class AntModes(Enum):
    searching = 1
    returning = 2

class Ant(Entity):
    def __init__(self, nest, chaotic_constant = 4):
        super(Ant, self).__init__(nest.realm)
        assert antmath.sniffmatrix is not None, "Antmath matrix was not initialised!"
        self.birth_time = self.realm.time #can be used to determine the age of the ant
        self.nest = nest #pointer to the nest object.

        # constants to be tuned
        self.grab_amount = 10
        self.pheromone_amount = 10
        self.walk_speed = 1
        self.chaotic_constant = chaotic_constant
        self.smell_range = 25
        self.threshold_sniff = 1
        self.mix_home = 0.5
        
        # states of the ant
        self.heading = np.random.rand()
        self.turning = np.random.rand() / 10
        self._create_state("position", np.array(nest.position))
        #self._create_state("fatigue", 0) # fatigue is turned off as it does nothing right now.
        self._create_state("food", 0)
        self.mode = AntModes.searching

        # used for debugs
        self.arrows = {}

    def do(self):
        """
        defines the core behaviour of the ant, including foraging, homing, etc.
        """
        if self.mode == AntModes.searching:
            food, dist = self.search_food()
            if food:
                if dist < self.smell_range / 2:
                    self.grab(food)
                    self.mode = AntModes.returning
                else:
                    self.walk(food.position)
            else:
                self.walk()

        elif self.mode == AntModes.returning:
            if self.at_home():
                self.drop()
                self.mode = AntModes.searching
            else:
                self.make_pheromones()
                self.walk(self.nest.position)

    def walk(self, target=None):
        """
        considering the current state of the and the surroundings, the ant can walk through the realm.
        this will set its next position state, which gets updated when update() is called.
        """
        self.clear_arrows()
        def angle_towards(heading, target, maxturn=0.05, mix=1):
            diff = target - heading
            if abs(diff) > maxturn: diff = maxturn * diff / abs(diff)
            return antmath.mix([0, 1-mix], [diff, mix])
        
        # chaotic turning
        self.turning = self.chaotic_constant * self.turning * (1 - self.turning)

        # intermediate heading.
        c_base = self.turning * 4 / self.chaotic_constant - 0.5
        r_base = np.random.rand() - 0.5
        h_base = antmath.mix([c_base, 1-self.nest.mix_noise], [r_base, self.nest.mix_noise]) / 10 # division limits the maximum angle
        self.heading += h_base # basic "noise" injection from the previous heading.

        if target is None:
            s_base, mag_sniff = self.sniff()

            if mag_sniff > self.threshold_sniff: # the ant has sniffed anything of significance.
                m = antmath.logistic(mag_sniff, 0, 20, 0.1) - 10
                self.set_arrows("sniff", s_base, (255, 0, 0), m)
                self.heading += angle_towards(self.heading, s_base)

        else:
            self.heading += angle_towards(self.heading, self.direction_to_target(target))

        h = antmath.imag_to_array(np.e ** (2j * np.pi * self.heading))
        next_position = self.states["position"] + antmath.unitvector(h) * self.walk_speed

        self.set_arrows("heading", self.heading, (0,0,255), 10)

        if self.realm.check_boundary(next_position):
            self.next_states["position"] = next_position
        else:
            raise IndexError("The ant has escaped the map")

    def direction_to_target(self, target):
        p = self.states["position"]
        return antmath.direction_to_exponent(target-p)

    def make_pheromones(self):
        # create pheromone in current position.
        p = tuple(self.states["position"].astype(int))
        self.realm.next_land_queue.put((p, self.pheromone_amount))

    def at_home(self):
        if np.linalg.norm(self.states["position"] - self.nest.position) < self.nest.range:
            return True
        else: return False

    def search_food(self):
        """
        Looks for food in the nearby region.
        This method loops through all the food in the list, checks if it is nearby, and take it.
        also returns the distance and direction towards the nearby food.
        """
        p = self.states["position"]
        for food in self.realm.food_list:
            location = food.position
            dist = np.linalg.norm(p - location)
            if dist < self.smell_range:
                return food, dist
        return None, None

    def get_current_slice(self, r):
        p = self.states["position"].astype(int)
        left, right = p[0] - r, p[0] + r
        top, bottom = p[1] - r, p[1] + r
        return self.realm.land[left:right, top:bottom]

    def sniff(self):
        """
        returns imaginary direction of the deterimined "strongest smell"
        refer to antmath.py for detailed implementation of the sniffmatrix.
        
        warning: this method does not consider that the sniffmatrix can be outside of map.
        index can get out of bound when an ant is nearby the edge.
        """
        def matrix_sum(a, m):
            return np.sum(np.multiply(a, m))

        def amount(x):
            return np.linalg.norm(x)

        current_slice = self.get_current_slice(self.smell_range//5)
        current_sum = matrix_sum(current_slice, antmath.trailmatrix)

        if amount(current_sum) < 0.1:
            #the ant is not on trail, switching to remote sensing
            current_slice = self.get_current_slice(self.smell_range)
            current_sum = matrix_sum(current_slice, antmath.sniffmatrix)
            if amount(current_sum) < 0.1:
                return 0, 0
        
        return antmath.complex_to_exponent(current_sum), amount(current_sum)

    def grab(self, food):
        """
        reduces the amount of food in current position, ant is now holding the food
        requires that the food object was already chosen. Use search_food to check food in nearby region.
        """
        grabbed = food.take(self.grab_amount)
        self.next_states["food"] = grabbed

    def drop(self):
        """
        drop the food, and increase the food stored in the colony
        """
        self.nest.new_food += self.states["food"]
        self.next_states["food"] = 0

    def get_heading(self):
        return self.heading

    def set_arrows(self, name, heading, color, intensity):
        self.arrows[name] = {
            "heading": heading,
            "color": color,
            "intensity": intensity
        }

    def clear_arrows(self):
        self.arrows = {}

    def get_arrows(self):
        return self.arrows
        

class Colony(Entity):
    def __init__(self, realm, nest_position, starting_ants=0, starting_food=0, noise=0):
        """
        [static states]
        position: the position of the nest on the map
        realm: pointer to the map entity. This exists so that the ants can leave traces on this realm.

        [children entities]
        ants: list of ants that belong to this colony
        new-ants: new ants that are going to added in the next tick
        
        [variable states]
        stored-food
        """
        super(Colony, self).__init__(realm)
        #static states
        self.position = np.array(nest_position)
        self.range = 10 # MAGIC NUMBER; the distance it is considered for ants to be "home"
        self.mix_noise = noise # how much noise to inject to the chaotic function.
        self.mix_returning = 1
        
        #children entities
        self.ants = []
        self.new_ants = []

        #variable states
        self.food = starting_food
        self.new_food = 0

        #starts with given number of ants
        for _ in range(starting_ants):
            self.spawn_ant()
        
        #apply the changes made in this init function
        self.update() 

    def get_ant_positions(self):
        """
        returns positions of entities related to this colony
        The first item is a N times 2 numpy array of position values.
        The second item is a 1 times 2 numpy array of the nest position.
        this is used to map the ants and the nest on the map
        """
        number_of_ants = len(self.ants)
        positions = np.zeros((number_of_ants, 2))
        for i, ant in enumerate(self.ants):
            positions[i] = ant.states["position"]
        return positions, self.position

    def do(self):
        """
        actions the colony itself takes with given state. Currently it does nothing.
        This can be used to make the colony spawn more ants when there is enough ants,
        or even spawn new colonies (which is out of scope of this project)
        """
        pass

    def update(self):
        # apply all the actions currents made
        for ant in self.ants:
            ant.update()

        # add newborn ants to the roster
        self.ants += self.new_ants
        self.new_ants = []

        # update the state variables related to the nest itself
        self.food += self.new_food
        self.new_food = 0

    def spawn_ant(self):
        # add newborn ants to the list to be added during the next update tick
        self.new_ants.append(Ant(self))

    def get_position(self):
        return (self.position[0], self.position[1])