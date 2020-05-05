import numpy as np

time = 0

class Entity():
    def __init__(self, realm):
        self.realm = realm
        self.states = {}
        self.next_states = {}

    def _update_template(self):
        self.next_states = self.states.copy()

    def _create_state(self, key, value):
        self.states[key] = value
        self.next_states[key] = None

    def do(self):
        pass

    def update(self):
        # update all the pending state changes, and set the future states undefined.
        # if the future state is undefined, that means nothing will be changed.
        for key in self.states:
            if self.next_states[key]:
                self.states[key] = self.next_states[key]
                self.next_states[key] = None
            


class Ant(Entity):
    def __init__(self, nest):
        self.birth_time = time
        self.nest = nest
        self._create_state("position", np.array(nest.position))
        self._create_state("grabbed-food", 0)

    def walk(self):
        """
            considering the current state of the and the surroundings, the ant can walk through the realm.
            this will set its next position state, which gets updated when update() is called.
        """
        p = self.states["position"]
        next_position = None

        def paper_walk():
            """
            some parameters are mentioned in the paper:
            mu: a positive constant. The system is chaotic when mu=3.
            yi: Indicates the degree of chaotic crawling. This is between 0 and 1. larger -> more chaos
            ri: self-organisation factor. 
            Vi: the serach region of ant i
            w : used to adjust the frequency of ants' periodic oscillation between th enest and the food source
            a : sufficiently-large positive constant to amplify yi.
            b : local search factor. Controls the local optimal path strategy.
            """
            raise NotImplementedError("Need to figure out what these variable should be")

            V = None # I have no idea what kind of number V should have. Should be incorporated into the state dictionary.
            y = None
            a = None
            b = None
            w = None

            food_position = None
            next_position = (
                (p + V) * np.exp( (1-np.exp(a*y)) * (3-psi*(p+V)) )
                - V
                + np.exp(2*a*y+b) * (np.abs(np.sin(w*time)) * (food_position - self.nest.position) * (p - self.nest.position))
            )
            return next_position

        def straight_walk():
            return p + np.array([1,1])

        def random_walk():
            return p + np.random.rand(2)

        next_position = random_walk()

        self.next_states["position"] = next_position

    def make_phermones(self):
        # create phermone in current position.
        # design decision: make phermone entity? or create a realm-map and leave phermone number on there?
        pass

    def grab(self):
        # reduce the amount of food in current position, ant is now holding the food
        pass

    def retrieve(self):
        # drop the food, and increase the food stored in the colony
        pass


class Colony(Entity):
    def __init__(self, realm, nest_position):
        self.position = nest_position
        self._create_state("stored-food", 0)
        self.ants = []
        self.new_ants = []

    def update(self):
        # apply all the actions currents made
        for ant in self.ants:
            ant.update()

        # add newborn ants to the roster
        self.ants += self.new_ants
        super.update()

    def spawn_ant(self):
        # add newborn ants to the list to be added during the next update tick
        self.new_ants.append(Ant(self))
