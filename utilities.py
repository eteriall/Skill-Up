import math
import random
from typing import Tuple
from xml.dom import minidom
from PIL import Image
import numpy as np


def cv_col(col: str) -> Tuple[int, ...]:
    return tuple(int(col[i:i + 2], 16) for i in (0, 2, 4))


def random_color():
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)


def arrow(c1, c2, O=45, l2=1):
    x1, y1 = c1
    x2, y2 = c2

    l1 = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    x3 = x2 + (l2 / l1) * ((x1 - x2) * math.cos(O) + (y1 - y2) * math.sin(O))

    y3 = y2 + (l2 / l1) * ((y1 - y2) * math.cos(O) - (x1 - x2) * math.sin(O))

    x4 = x2 + (l2 / l1) * ((x1 - x2) * math.cos(O) - (y1 - y2) * math.sin(O))

    y4 = y2 + (l2 / l1) * ((y1 - y2) * math.cos(O) + (y1 - y2) * math.sin(O))

    return (int(x3), int(y3)), (int(x4), int(y4))


def rect_collision(rect1, rect2):
    """
    rect1.x < rect2.x + rect2.w &&
    rect1.x + rect1.w > rect2.x &&
    rect1.y < rect2.y + rect2.h &&
    rect1.h + rect1.y > rect2.y
    """
    return rect1[0][0] < rect2[0][0] + rect2[1][0] \
           and rect1[0][0] + rect1[1][0] > rect2[0][0] \
           and rect1[0][1] < rect2[0][1] + rect2[1][1] \
           and rect1[0][1] + rect1[1][1] > rect2[0][1]


def generate_tile_map(rects, grid_size, cell_size=10) -> np.ndarray:
    arr = np.array(
        [[1 if intersects((x * cell_size, y * cell_size), rects) else 0 for y in range(grid_size[1])] for x in
         range(grid_size[0])])
    return arr


def intersects(point, colliders, collider_size=10):
    x, y = point
    x, y = x - collider_size // 2, y - collider_size // 2
    w, h = collider_size, collider_size
    s = any(map(lambda c:
                rect_collision(((x, y), (w, h)), c), colliders
                ))
    return s


def discrete_png(path_to_file, grid_size, image_delta=(0, 0), image_scale=1):
    img = Image.open(path_to_file)
    img.resize((int(grid_size[0] * image_scale), int(grid_size[1] * image_scale)), Image.ANTIALIAS)
    thresh = 10
    fn = lambda x: 255 if x > thresh else 0
    r = img.convert('L').point(fn, mode='1')
    return np.asarray(r).transpose()


def get_rects(path_to_file, svg_delta=(0, 0), svg_scale=1):
    # Load all colliders
    doc = minidom.parse(open(path_to_file))
    rects = [
        (
            rect.getAttribute('x') if rect.getAttribute('x') != '' else '0',
            rect.getAttribute('y') if rect.getAttribute('y') != '' else '0',
            rect.getAttribute('width'),
            rect.getAttribute('height'),
            rect.getAttribute('fill'))
        for rect in doc.getElementsByTagName('rect')]

    rects = map(lambda x: (
        (int(x[0]) + svg_delta[0], int(x[1]) + svg_delta[1]),
        (int(x[2]), int(x[3])),
        x[4]),
                rects)

    rects = map(lambda x: (*x[:2], cv_col(x[2].strip('#'))), rects)
    rects = list(
        map(
            lambda x: (tuple(int(k * svg_scale) for k in x[0]), tuple(int(k * svg_scale) for k in x[1]), x[2]),
            rects
        )
    )
    return rects


