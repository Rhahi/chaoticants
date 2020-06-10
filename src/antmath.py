import numpy as np
from scipy.spatial.transform import Rotation as R

sniffmatrix = None

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

def _build_weight_matrix(height, width):
    center = np.array([height//2, width//2])
    base_weight = 100

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
    x_angle_candidates = [theta1, 2*np.pi - theta1]
    
    theta2 = np.arcsin(vec[0])
    y_angle_candidates = [abs(theta2), np.pi - theta2]

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
    w = _build_weight_matrix(5, 5)
    d = _build_direction_matrix(5, 5)
    print(np.multiply(w, d))