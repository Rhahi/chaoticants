import numpy as np
from ant import Colony, Realm
import matplotlib.pyplot as plt
import matplotlib._color_data as mcd

def retrieve_ant_positions(colonies):
    list_pos = [x.get_ant_positions() for x in colonies]
    return list_pos

def plot(realm, colonies):
    xkcd = mcd.XKCD_COLORS
    colors = [xkcd["xkcd:azure"], xkcd["xkcd:orange"], xkcd["xkcd:green"], xkcd["xkcd:red"],
        xkcd["xkcd:purple"], xkcd["xkcd:sienna"], xkcd["xkcd:pink"], xkcd["xkcd:cyan"], xkcd["xkcd:magenta"]]
    
    plt.figure()
    plt.title("Ant positions")
    plt.xlim(2495, 2505)
    plt.ylim(2495, 2505)

    data = retrieve_ant_positions(colonies)
    for i, pos in enumerate(data):
        plt.scatter(pos[0][:,0], pos[0][:,1], label="Colony {}".format(i), color=colors[i])

    plt.legend()
    plt.show()
