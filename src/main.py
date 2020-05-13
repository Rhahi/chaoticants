# the main program that runs and animates the and behaviour
from ant import Realm, Ant, Colony
import animator

def progress_time(realm, colonies):
    for colony in colonies:
        for ant in colony.ants:
            ant.do()

        colony.do()
        colony.update()
    realm.update()

if __name__ == "__main__":
    realm = Realm(size=(2000, 2000))
    colony = Colony(realm=realm, nest_position=(1000,1000), starting_ants = 10)
    colonies = [colony] # there is only one colony for now.
    animator.plot(realm, colonies) # first plot
    
    for _ in range(5):
        #input() # for debuging purposes, this progresses when enter is pressed.
        progress_time(realm, colonies)
        animator.plot(realm, colonies)
