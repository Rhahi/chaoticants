# Random and Chaotic Ant Simulator

This simulator was written for a course project, [Chaos](http://www.matfys.lth.se/education/FMFN05/)

The project simulates a group of ant-like agents. During their initial serach attempt, the ants solely rely on blind search. The experimenter may tune the parameter so that the ant's direction is chosen either randomly (using numpy.random.rand), chaotically (using a logistic map), or both (mixing noise and chaos). With the simulator, the effectiveness of their food collection using chaotic or random walk can be compared.

## Requirements

* Python 3.8+
* Numpy
* Pygame
* Scipy

Simply using pip install command on the three packages will do. (Requires you to have [pip](https://pip.pypa.io/en/stable/installing/) installed.)
If it doesn't work, you may use `python -m pip install -r requirements.txt` to match the versions to match the developed version.

## Running simulation

* Configure options in main.py. By default, visualiser is enabled and only one experiment will run.
* Run main.py
* To scroll across the map, click and drag. WASD can also be used.
* Mouse scroll zooms in and out.
* Spacebar shows some more information about their heading or other directions. This was used for debugging purposes.

