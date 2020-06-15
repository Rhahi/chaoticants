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

def main(stepping = False):
    realm = Realm(size=(1000, 1000))      
    antmath.build_antmath_matrix(50, 50)
    antmath.build_trail_matrix(10, 10)
    spawn_food(realm, count=200)
    colony = Colony(realm=realm, nest_position=(500,500), starting_ants = 50)
    colonies = [colony] # there is only one colony for now.
    
    ants = []
    ants_with_food = []

    pgv = PygameVisualizer(
        [(realm.food_list, "food.png")]
        + [(colonies, "home.png")]
        + [(ants, "ant.png")]
        + [(ants_with_food, "ant_red.png")]
        )
    pgv.camera.middle = tuple(colony.position)

    while True:
        progress_time(realm, colonies)
        pgv.step_frame(realm)
        
        ants[:] = []
        ants_with_food[:] = []

        for colony in colonies:
            a = [ant for ant in colony.ants if ant.states["food"] == 0]
            af = [ant for ant in colony.ants if ant.states["food"] != 0]
            ants += a
            ants_with_food += af

        if stepping:
            import msvcrt
            msvcrt.getch()


if __name__ == "__main__":
    main("step" in sys.argv)

