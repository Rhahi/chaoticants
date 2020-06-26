# the main program that runs and animates the and behaviour
from ant import Realm, Ant, Colony
from pygamevisualizer import PygameVisualizer
import sys
import numpy as np
import antmath
import os

ASSETS_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'assets')

def spawn_random_food(realm, count, total_amount=None):
    if total_amount:
        amounts = np.random.multinomial(total_amount, [1/count]*count)
        for a in amounts:
            dist = np.random.rand(1) * 100
            angle = np.random.rand() * np.pi * 2
            position = np.array([500, 500]) + [np.cos(angle), np.sin(angle)] * dist
            realm.spawn_food(position, a)
    else:
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
        "quick-test": [
            [center+(0,70), 20],
            [center+(0,-70), 20],
            [center+(70,0), 20],
            [center+(-70,0), 20]
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
    # static settings
    realm_size = (1000, 1000)
    nest_position = (500, 500)
    
    # experiment settings
    use_visualiser = True
    number_of_simulations = 3
    seed_list = np.linspace(1, number_of_simulations, number_of_simulations, dtype=int)

    # simulation settings
    realm = Realm(size=realm_size, evaporation=0.99)
    sniff_radius = 50
    food_radius = 30
    starting_ants = 30
    noise_ratio = 0.2
    pattern_name = "quick-test"
    # end of settings section.
    
    results = []
    
    for i in range(number_of_simulations):
        np.random.seed(seed_list[i])
        antmath.build_antmath_matrix(sniff_radius*2, sniff_radius*2)
        colony = Colony(realm=realm, nest_position=nest_position,
            starting_ants=starting_ants, chaotic_constant=4, noise=noise_ratio,
            sniff_radius=sniff_radius, food_radius=food_radius)
        colonies = [colony] # there is only one colony for now.
        
        if pattern_name == "random":
            spawn_random_food(realm, count=10, total_amount=2000)
        else: spawn_predefined_food(realm, center=colony.position, pattern=pattern_name)

        if use_visualiser:
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
            if use_visualiser:
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
                num_ticks = realm.time
                print("simulation ended after", num_ticks, "ticks.")
                results.append(num_ticks)
                break

    print(f"""\naverage time: {np.mean(results)}, noise:{noise_ratio}, configuration: \"{pattern_name}\",
        \nall results: {results}""")


if __name__ == "__main__":
    main("step" in sys.argv)

