# the main program that runs and animates the and behaviour
from ant import Realm, Ant, Colony
from pygamevisualizer import PygameVisualizer
import numpy as np
import random

def progress_time(realm, colonies):
    for colony in colonies:

        for ant in colony.ants:
            ant.do()

            # test function to test pheromone and ant movement
            if random.random()<0.01:
                ant.make_pheromones()
        if random.random()<0.02:
            colony.spawn_ant()
            
        colony.do()
        colony.update()
    realm.update()

if __name__ == "__main__":
    realm = Realm(size=(1000, 1000))
    colony = Colony(realm=realm, nest_position=(500,500), starting_ants = 10)
    colonies = [colony] # there is only one colony for now.
    
    pgv = PygameVisualizer( [(colonies, "home.png")] + [(colony.ants, "ant.png") for colony in colonies] )
    pgv.camera.middle = tuple(colony.position)

    while True:
        progress_time(realm, colonies)
        pgv.step_frame(realm)