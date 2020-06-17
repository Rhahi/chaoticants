import numpy as np
from scipy.spatial.transform import Rotation as R

sniffmatrix = None
trailmatrix = None

"""
    Directional reference:
    exponential -> np.e ** (2j * np.pi * self.heading) -> np.array([d.imag, d.real])
    
    exponential (angle) heading:
    0    ->  1+0j -> down
    0.25 ->  0+1j -> right
    0.5  -> -1+0j -> up
    0.75 ->  0-1j -> left
    1    ->       -> down

    2d array:
    (0j, 1) -> down
    (1j, 0) -> right
"""

def detect_straight_line(image):
    """
    gets a 2d numpy array and returns the inclination of the most likely line.
    assumes that there is only one line.
    """
    a = np.argmax(image, axis=0) #[i, x]
    b = np.array(np.argmax(image, axis=1)) #[y, i]
    x_raw = np.concatenate((np.arange(len(a)), b))
    y_raw = np.concatenate((a, np.arange(len(b))))
    x = []
    y = []

    assert len(x_raw) == len(y_raw)
    edge = len(x_raw)

    for i in range(edge):
        #remove the first edges, since having no maximum will return the first arg as argmax.
        xr = x_raw[i]
        yr = y_raw[i]
        if xr == 0 or yr == 0:
            continue
        x.append(xr)
        y.append(yr)

    if len(x) > 3:
        if np.std(x) >= np.std(y):
            inc = np.polyfit(x, y, deg=1)[0]
            incj = np.cos(inc) + np.sin(inc)*1j
        else:
            inc = np.polyfit(y, x, deg=1)[0]
            incj = np.sin(inc) + np.cos(inc)*1j 

        return complex_to_exponent(incj)
    else:
        return None

def _build_weight_matrix(height, width):
    center = np.array([height//2, width//2])
    base_weight = 2

    matrix = np.zeros((height, width))
    for ix, iy in np.ndindex(matrix.shape):
        dist = np.linalg.norm(center - (ix, iy))
        if dist == 0: continue
        matrix[ix, iy] = round(base_weight / dist,2)

    return matrix

def _build_direction_matrix(height, width):
    center = np.array([height//2, width//2])
    
    matrix = np.zeros((height, width), dtype=np.complex)
    for ix, iy in np.ndindex(matrix.shape):
        direction = center - (ix, iy)
        if direction.any() == 0: continue
        imag_dir = (-direction[0]*1j - direction[1])/np.linalg.norm(direction)
        matrix[ix, iy] = imag_dir

    return matrix

def mix(*argv):
    mix_sum = 0
    mag_sum = 0
    for m in argv:
        value, magnitude = m
        mix_sum += value * magnitude
        mag_sum += magnitude

    if mag_sum != 1.: raise ValueError("Mixing magnitudes should sum up to 1.")
    return mix_sum

def imag_to_array(d):
    return np.array([d.imag, d.real])

def unitvector(vec):
    return vec / np.linalg.norm(vec)

def logistic(x, x0, L, k):
    """
    logistic function, potentially used for ant smell threshold control.
    speculated values:
    L = 1
    k = 0.1
    x0 = 10
    """
    return L / (1 + np.e**(-k*(x-x0)))
def complex_to_exponent(c):
    dx = c.real
    dy = c.imag
    return direction_to_exponent(np.array([dy, dx]))

def direction_to_exponent(array):
    """
    converts x, y array into exponent form used in heading.
    examples:
    # in: (0, 1) -> out: 0
    # in: (1, 1) -> out: 0.125
    # in: (1, 0) -> out: 0.25
    """
    
    if np.linalg.norm(array) == 0: raise ValueError("zero distance has undefined direction")
    vec = unitvector(array)
    
    theta1 = np.arccos(vec[1])
    theta2 = np.arcsin(vec[0])
    x_angle_candidates = [theta1, 2*np.pi - theta1]
    y_angle_candidates = [(theta2 + 2*np.pi)%(2*np.pi), np.pi - theta2]

    for cx in x_angle_candidates:
        for cy in y_angle_candidates:
            if np.isclose(cx, cy):
                return cx / (2*np.pi)
    
    raise ValueError("Could not find proper direction")

def build_antmath_matrix(height, width):
    """
    this function must be run before using any antmath matrix operations.
    """
    
    w = _build_weight_matrix(height, width)
    d = _build_direction_matrix(height, width)
    f = np.multiply(w, d)
    global sniffmatrix
    sniffmatrix = f
    return f

if __name__ == "__main__":
    a = np.zeros((50,50))
    b = np.zeros((50,50))
    c = np.zeros((50,50))
    
    a[25,:] += 10
    print(detect_straight_line(a))

    b[:,25] += 10
    print(detect_straight_line(b))
    
    for i in range(50):
        c[i,i] += 10
    print(detect_straight_line(c), 1/8)