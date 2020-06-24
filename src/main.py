# the main program that runs and animates the and behaviour
from ant import Realm, Ant, Colony
from pygamevisualizer import PygameVisualizer
import sys
import numpy as np
import random
import antmath
import os

ASSETS_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'assets')

def spawn_random_food(realm, count):
    for _ in range(count):
        position = np.array(realm.land.shape) * np.random.rand(2)
        amount = int(np.random.rand() * 50 + 50)
        realm.spawn_food(position, amount)

def spawn_predefined_food(realm, center, pattern):
    food_patterns = {
        "equal-cross": [
            [center+(0,100), 500],
            [center+(0,-100), 500],
            [center+(100,0), 500],
            [center+(-100,0), 500]
        ],
        "skewed-cross": [
            [center+(0,100), 100],
            [center+(0,-100), 1000],
            [center+(100,0), 200],
            [center+(-100,0), 200]
        ],
    }
    if pattern in food_patterns:
        for position, amount in food_patterns[pattern]:
            realm.spawn_food(position, amount)
    else:
        raise ValueError("Undefined pattern")
    
def progress_time(realm, colonies):
    for colony in colonies:
        for ant in colony.ants:
            ant.do()
                   
        colony.do()
        colony.update()
    realm.update()

def main(stepping = False):
    realm = Realm(size=(1000, 1000), evaporation=0.99)
    sniff_radius = 50      
    antmath.build_antmath_matrix(sniff_radius*2, sniff_radius*2)
    
    colony = Colony(realm=realm, nest_position=(500,500),
        starting_ants=30, chaotic_constant=4, noise=0.2,
        sniff_radius=sniff_radius)
    colonies = [colony] # there is only one colony for now.

    #spawn_random_food(realm, count=200) #uncomment this line to use random food distribution.
    spawn_predefined_food(realm, center=colony.position, pattern="equal-cross")
    
    ants = []
    ants_with_food = []

    pgv = PygameVisualizer(
        [(realm.food_list, os.path.join(ASSETS_PATH, "food.png"))]
        + [(colonies, os.path.join(ASSETS_PATH, "home.png"))]
        + [(ants, os.path.join(ASSETS_PATH, "ant.png"))]
        + [(ants_with_food, os.path.join(ASSETS_PATH, "ant_with_food.png"))],
        tickrate=0 #zero means that there is no framerate cap
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

        

        if len(realm.food_list) == 0:
            print("simulation ended after", realm.time, "ticks.")
            break


if __name__ == "__main__":
    main("step" in sys.argv)

