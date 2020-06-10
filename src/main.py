# the main program that runs and animates the and behaviour
from ant import Realm, Ant, Colony
from pygamevisualizer import PygameVisualizer
import sys
import numpy as np
import random
import antmath

def spawn_food(realm, count):
    for _ in range(count):
        position = np.array(realm.land.shape) * np.random.rand(2)
        amount = int(np.random.rand() * 50 + 50)

        realm.spawn_food(position, amount)

def progress_time(realm, colonies):
    for colony in colonies:
        for ant in colony.ants:
            ant.do()
                   
        colony.do()
        colony.update()
    realm.update()

def main():
    realm = Realm(size=(1000, 1000))
    antmath.build_antmath_matrix(50, 50)
    spawn_food(realm, count=200)
    colony = Colony(realm=realm, nest_position=(500,500), starting_ants = 20)
    colonies = [colony] # there is only one colony for now.
    
    pgv = PygameVisualizer([(realm.food_list, "food.png")] + [(colonies, "home.png")] + [(colony.ants, "ant.png") for colony in colonies] )
    pgv.camera.middle = tuple(colony.position)

    while True:
        progress_time(realm, colonies)
        pgv.step_frame(realm)


if __name__ == "__main__":
    main()

