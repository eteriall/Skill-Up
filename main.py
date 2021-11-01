import json
import os
import pathlib
from tkinter import *
import tkinter as tk
from tkinter import simpledialog
from tkinter.filedialog import askopenfilename
from subprocess import Popen

from os_activities import create_new_project
import glob

from simulation import run_simulation
from visualize import run_visualization
from shutil import copyfile


class Project:
    def __init__(self, name):
        self.name = name

        self._simulations = []
        self._models = []
        self.update_simulations()

    def update_simulations(self):
        self._simulations = list(
            map(lambda x: x.split('/')[-1], glob.glob(f'Projects/{self.name}/Simulations/*')))

    @property
    def simulations(self):
        self.update_simulations()
        return self._simulations

    @property
    def models(self):
        self.update_models()
        return self._models

    def update_models(self):
        self._models = list(
            map(lambda x: x.split('/')[-1], glob.glob(f'Projects/{self.name}/Models/*')))

    def get_sim_meta(self, sim_name):
        path = f'Projects/{self.name}/Simulations/{sim_name}'
        meta = json.load(open(path, mode='r'))['meta']
        return meta

    def run_simulation(self, simulation_name):
        run_simulation(self.name, simulation_name)

    def run_visualization(self, simulation_name):
        run_visualization(self.name, simulation_name)

    def add_new_model(self):
        filename = askopenfilename(initialdir='/',
                                   message="Choose one or more files",
                                   multiple=True,
                                   title="File Selector")

        copyfile(filename, f'Projects/{self.name}/Models')
        self.update_models()


class SimulationSettingsWindow:
    def __init__(self, project):

        self.project = project
        self.w = tk.Tk()

        Label(self.w, text='Create new simulation', font=('rosatom', 16, 'bold'), pady=5).pack()

        self.fields = {
            'SIM_NAME': "",
            'SCREEN_SIZE': (500, 500),
            'GRID_SIZE': (50, 50),
            'GRID_CELL_SIZE': 10,
            'SVG_SCALE': 1,
            'SVG_DELTA': (0, 0),
            'FONT_NAME': 'Arial',
            'AGENTS_AMOUNT': 30,
            'PASSENGERS_SPAWN_RECTS': ((25, 45, 12, 2),),
            'goal': (1, 1)}
        self.box = None

        # Create main form
        self.ents = self.makeform(self.w)

        self.w.bind('<Return>', self.launch_sim)
        b1 = tk.Button(self.w, text='Launch',
                       command=self.launch_sim)
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self.w, text='Quit', command=self.w.destroy)
        b2.pack(side=tk.LEFT, padx=5, pady=5)

        # Add items to ListBox
        self.update_models()

        # Set cursor selector to first element
        self.box.selection_clear(0, END)
        self.box.selection_set(0)

    def fetch(self):
        s = {}
        for entry in self.ents:
            field = entry[0]
            text = entry[1].get()
            s[field] = text
        s['MODEL_FILENAME'] = self.box.get(self.box.curselection())
        return s

    def launch_sim(self):
        data = self.fetch()
        s = f'python3 simulation.py -pn {self.project.name} -sn {data["SIM_NAME"]} -ss "{data["SCREEN_SIZE"]}" -gs "{data["GRID_SIZE"]}"' \
            f' -gcs "{data["GRID_CELL_SIZE"]}" -svgs "{data["SVG_SCALE"]}" -svgd "{data["SVG_DELTA"]}"' \
            f' -mf "{data["MODEL_FILENAME"]}" -fn "{data["FONT_NAME"]}" -aa "{data["AGENTS_AMOUNT"]}"' \
            f' -psr "{data["PASSENGERS_SPAWN_RECTS"]}" -g "{data["goal"]}"'
        path = pathlib.Path(__file__).parent.resolve()
        print(s)
        os.system(s)

    def update_models(self):
        self.box.delete(0, 'end')
        for model in self.project.models:
            self.box.insert(END, model)

    def makeform(self, root):
        entries = []

        # Add Model Selection field
        row = tk.Frame(root)
        lab = tk.Label(row, width=15, text='Select SVG Model', anchor='w')
        self.box = tk.Listbox(row, height=3)

        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        lab.pack(side=tk.LEFT)
        self.box.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)

        # Add NewModel button
        Button(root, text='New model', width=30, command=self.project.add_new_model).pack()

        for field in self.fields:
            row = tk.Frame(root)
            lab = tk.Label(row, width=15, text=field, anchor='w')
            ent = tk.Entry(row)
            row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            lab.pack(side=tk.LEFT)
            ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
            entries.append((field, ent))
            ent.insert('end', json.dumps(self.fields[field]))

        return entries


class SimulationsWindow:
    def __init__(self, project_name):
        self.project = Project(project_name)

        self.w = Tk()
        self.w.geometry("250x263")

        Label(self.w, text='Select simulation to visualize', font=('rosatom', 16, 'bold')).pack()

        # Create SelectBox
        self.box = Listbox(self.w, selectmode=EXTENDED, height=5, width=22)
        self.box.pack()

        Button(self.w, command=self.visualize_simulation, text='Launch Visualizer', width=20).pack()
        Button(self.w, command=self.run_new_simulation, text='Create new simulation', width=20).pack()

        # Add scroll
        # scroll = Scrollbar(command=box.yview)
        # scroll.pack(side=LEFT, fill=Y)
        # box.config(yscrollcommand=scroll.set)

        self.box.bind('<<ListboxSelect>>', self.on_box_select)
        self.box.selection_clear(0, END)

        if len(self.project.simulations):
            self.box.selection_set(0)

        self.load_simulations()
        self.simulation_settings_window = None

    def on_box_select(self, *args):
        print('a')

    def load_simulations(self):
        # Clear the previous values
        self.box.delete(0, 'end')

        # Get the new
        simulations = self.project.simulations

        # Add new values to  ListBox
        for item in simulations:
            self.box.insert(END, item)

    def visualize_simulation(self):
        sim_name = self.box.get(self.box.curselection())

        path = pathlib.Path(__file__).parent.resolve()
        os.system(f"python3 {path}/visualize.py -pn '{self.project.name}' -sn '{sim_name}'")

    def run_new_simulation(self):

        self.simulation_settings_window = SimulationSettingsWindow(self.project, )


class MainWindow:
    def __init__(self):
        self.w = Tk()

        self.selected_project = tk.StringVar()
        self.selected_project.set("<- Select project")

        # Create SelectBox
        self.box = Listbox(self.w, selectmode=EXTENDED)
        self.box.pack(side=LEFT)

        # Add scroll
        # scroll = Scrollbar(command=box.yview)
        # scroll.pack(side=LEFT, fill=Y)
        # box.config(yscrollcommand=scroll.set)

        self.box.bind('<<ListboxSelect>>', self.project_box_on_select)

        self.update_box()

        f = Frame()
        f.pack(side=LEFT, padx=10)

        selected_project_label = Label(f, textvariable=self.selected_project, font=('Rosatom', 16))
        selected_project_label.pack()

        Button(f, text="Open Project", command=self.open_project) \
            .pack(fill=X)

        Button(f, text="Create new project", command=self.create_project) \
            .pack(fill=X)
        """_ = Label(f, text='---- or ----', pady=2).pack()
        self.new_project_name = Entry(f)
        self.new_project_name.pack()

        """

        self.simulation_window = None

    def update_box(self):
        # Add items to SelectBox
        self.box.delete(0, 'end')
        for item in get_projects():
            self.box.insert(END, item)

    def run(self):
        self.w.mainloop()

    def project_box_on_select(self, *args):
        self.selected_project.set(self.box.get(self.box.curselection()))
        # selected_project_label.setvar('font', ('Rosatom', 16, 'bold'))
        # selected_project_label.pack()

    def create_project(self):
        project_name = simpledialog.askstring("New project", "Choose a name for your project",
                                              parent=self.w)
        if project_name is not None:
            create_new_project(project_name)
        else:
            return
        self.update_box()

    def open_project(self, project_name=None):
        if project_name is None:
            try:
                project_name = self.box.get(self.box.curselection())
            except tk.TclError:
                return
        self.simulation_window = SimulationsWindow(project_name)


def get_projects():
    return list(next(os.walk('Projects'))[1])


if __name__ == "__main__":
    app = MainWindow()
    app.run()
