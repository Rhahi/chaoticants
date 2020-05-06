import numpy as np

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
            if self.next_states[key] is not None:
                self.states[key] = self.next_states[key]
                self.next_states[key] = None

class Ant(Entity):
    def __init__(self, nest):
        super(Ant, self).__init__(nest.realm)
        self.birth_time = self.realm.time #may be used to determine the age of the ant
        self.nest = nest #pointer to the nest object.
        self._create_state("position", np.array(nest.position))
        self._create_state("grabbed-food", 0)
        self._create_state("fatigue", 0)

    def do(self):
        """
        defines the core behaviour of the ant, including foraging, homing, etc.
        """
        self.walk() #testing purposes

    def walk(self):
        """
            considering the current state of the and the surroundings, the ant can walk through the realm.
            this will set its next position state, which gets updated when update() is called.
        """
        p = self.states["position"]
        next_position = None
        time = self.nest.realm.time

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
            psi = None

            food_position = None
            next_position = (
                (p + V) * np.exp( (1-np.exp(a*y)) * (3-psi*(p+V)) )
                - V
                + np.exp(2*a*y+b) * (np.abs(np.sin(w*time)) * (food_position - self.nest.position) * (p - self.nest.position))
            )
            return next_position

        def straight_walk():
            #walks in a straight diagonal line. Used for initial testing purposes.
            return p + np.array([1,1])

        def random_walk():
            #walks randomly. Used for initial testing purposes. Walk distance is [0...1)
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

class Realm():
    def __init__(self):
        self.time = 0
        self.time_increment = 1 # the amount of time to progress per tick.

        self.land = np.zeros((5000, 5000)) #for now, define the limit of the area in this.
        self.next_land = np.zeros(self.land.shape)

        self.offset = np.array([2500, 2500]) #now, treat coordinate 0, 0 as 5000, 5000
        self.evaporate_rate = 0.7 # TODO fix magic number

    def phermone(self, coordinate):
        """
        add phermone to the marked position in the realm.
        the coordinates must be integers.
        Beware that float will be converted to integers.
        """
        c = coordinate + self.offset
        assert (c < np.array([5000,5000])).all()
        y = int(c[0])
        x = int(c[1])
        
        self.next_land[y,x] += 1

    def update(self):
        """
        reduces the phermone exponentially.
        """
        self.land = np.dot(self.land, self.evaporate_rate) # exponential decay
        self.land += self.next_land # add newly added phermones
        self.next_land = np.zeros(self.land.shape) # reset the next phermones array
        self.time += self.time_increment



class Colony(Entity):
    def __init__(self, realm, nest_position, faction=0, starting_ants=0):
        """
        [static states]
        position: the position of the nest on the map
        faction: marks the faction id of the colony, in case there are going to be multiple colonies.
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
        self.faction = faction

        #children entities
        self.ants = []
        self.new_ants = []

        #variable states
        self._create_state("stored-food", 0)

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
        coordinates = np.zeros((number_of_ants, 2))
        for i, ant in enumerate(self.ants):
            coordinates[i] = ant.states["position"]
        return coordinates, self.position

    def do(self):
        """
        actions the colony itself takes with given state currently it does nothing.
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

        # update the state variables related to the nest itself
        super(Colony, self).update()

    def spawn_ant(self):
        # add newborn ants to the list to be added during the next update tick
        self.new_ants.append(Ant(self))