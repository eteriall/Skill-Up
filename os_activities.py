import json
import os


def create_new_project(project_name):
    # screen_size, grid_size, grid_cell_size, svg_scale, svg_delta
    os.mkdir(f'Projects/{project_name}')
    os.mkdir(f'Projects/{project_name}/Models')
    os.mkdir(f'Projects/{project_name}/Simulations')

    """with open(f'Projects/{project_name}/scheme_setup.json', mode='a') as f:
        json.dump({
            "SCREEN_SIZE": screen_size,
            "GRID_SIZE": grid_size,
            "GRID_CELL_SIZE": grid_cell_size,
            "SVG_SCALE": svg_scale,
            "SVG_DELTA": svg_delta,
            "FONT_NAME": "Arial"
        }, f)"""


def save_points(points, meta, paths_file):
    open(paths_file, mode='a').close()
    d = open(paths_file, mode='r+')
    try:
        paths = json.load(d)['paths']
    except:
        paths = []
    paths += [points] if points != [] else []

    d.close()
    json.dump({"meta": meta, "paths": paths}, open(paths_file, mode='w'))


def get_simulations():
    pass


def load_meta(project_name):
    meta = json.load(open(f'Projects/{project_name}/scheme_setup.json', mode='r'))
    SCREEN_SIZE = meta['SCREEN_SIZE']
    GRID_SIZE = meta['GRID_SIZE']
    GRID_CELL_SIZE = meta['GRID_CELL_SIZE']
    SVG_SCALE = meta['SVG_SCALE']
    SVG_DELTA = meta['SVG_DELTA']
    FILENAME = meta['FILENAME']
    FONT_NAME = meta['FONT_NAME']
