import numpy as np
from queue import SimpleQueue
from enum import Enum

class Food():
    def __init__(self, position, amount):
        self.position = position
        self.amount = amount

    def take(self, amount):
        taken = min(self.amount - amount, amount)
        self.amount -= taken
        return taken

    def get_position(self):
        return (self.position[0], self.position[1])

    def get_heading(self):
        return 0

class Realm():
    """
    The world where our ants and nests live in.
    Time is defined here, so that we don't need to define a global time variable.
    """
    def __init__(self, size):
        self.time = 0
        self.time_increment = 1 # the amount of time to progress per tick.
        
        self.land = np.zeros(size)
        self.gradient = np.gradient(self.land)
        self.next_land_queue = SimpleQueue()

        self.evaporate_rate = 0.7 # TODO fix magic number
        self.food_list = []

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
            #mport pdb; pdb.set_trace()
            self.land[p] += a
        #self.gradient = np.gradient(self.land)
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


class AntModes(Enum):
    searching = 1
    returning = 2

class Ant(Entity):
    def __init__(self, nest, chaotic_constant = 4):
        super(Ant, self).__init__(nest.realm)
        self.birth_time = self.realm.time #can be used to determine the age of the ant
        self.nest = nest #pointer to the nest object.

        # constants to be tuned
        self.grab_amount = 10
        self.pheromone_amount = 2
        self.heading = np.random.rand(1)
        self.turning = np.random.rand(1) / 10
        self.walk_speed = 1
        self.chaotic_constant = chaotic_constant
        self.smell_range = 10
        self.smell_threshold = 2
        
        # states of the ant
        self._create_state("position", np.array(nest.position))
        #self._create_state("fatigue", 0) # fatigue is turned off as it does nothing right now.
        self._create_state("food", 0)
        self.mode = AntModes.searching

    def do(self):
        """
        defines the core behaviour of the ant, including foraging, homing, etc.
        """
        if self.mode == AntModes.searching:
            food = self.search_food()
            if food:
                self.grab(food)
                self.mode = AntModes.returning
            else:
                self.walk()

        elif self.mode == AntModes.returning:
            if self.at_home():
                self.drop()
                self.mode = AntModes.searching
            else:
                self.make_pheromones()
                self.walk()
            # TODO: make ants properly return home, instead of just walking randomly again.

        #self.next_states["fatigue"] = self.states["fatigue"] + 1

    def pheromone_gradient(self):
        """
        retrieves pheromone gradient in current position
        returns magnitude of the gradient and direction (exponent form)
        """
        p = tuple(self.states["position"].astype(int))
        grad_x = self.realm.gradient[0][p]
        grad_y = self.realm.gradient[1][p]

        g = grad_x + grad_y * 1j
        mag = np.linalg.norm(g)
        if mag > 0:
            return mag, np.log(g/mag) * -1j # TODO figure out exact formula for this
        else:
            return mag, 0

    def walk(self):
        
        """
            considering the current state of the and the surroundings, the ant can walk through the realm.
            this will set its next position state, which gets updated when update() is called.
        """
        def logistic(x):
            return 1 / ( 1 + np.e ** (-1 * (x - self.smell_threshold)) )
        pheromone_mag, pheromone_heading = self.pheromone_gradient()

        # amount for ants to turn from current heading
        self.turning = self.chaotic_constant * self.turning * (1 - self.turning)

        # final heading. Div 4 means restricting chaotic movement to 90 degrees.
        self.heading += (
            (1 - self.nest.noise) * (self.turning - 0.5)
            + self.nest.noise * (np.random.rand(1) - 0.5)
        ) / 4

        # TODO: correct heading using pheromone.
        #self.heading = (pheromone_heading * logistic(pheromone_mag) + self.heading * (1 - logistic(pheromone_mag)))


        h_rotation = np.e ** (2j * np.pi * self.heading)
        h = np.array([h_rotation.imag[0], h_rotation.real[0]])
        next_position = self.states["position"] + h * self.walk_speed
        
        if self.realm.check_boundary(next_position):
            self.next_states["position"] = next_position
        else:
            raise IndexError("The ant has escaped the map")

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
        """
        p = self.states["position"]
        for food in self.realm.food_list:
            location = food.position
            dist = np.linalg.norm(p - location)
            if dist < np.sqrt(food.amount):
                return food
        return 0

    def sniff(self):
        """
        senses nearby pheromone and returns the gradient
        the magnitude of the gradient indicates that the pheromone is strong.
        """
        raise NotImplementedError

    def grab(self, food):
        """
        reduces the amount of food in current position, ant is now holding the food
        requires that the food object was already chosen. Use search_food to check food in nearby region.
        """
        grabbed = food.take(self.grab_amount)
        self.next_states["food"] = grabbed

    def drop(self):
        # drop the food, and increase the food stored in the colony
        self.nest.new_food += self.states["food"]
        self.next_states["food"] = 0

    def get_heading(self):
        return self.heading
        

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
        self.noise = noise # how much noise to inject to the chaotic function.

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