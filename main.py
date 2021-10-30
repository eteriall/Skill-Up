import json
import os
from tkinter import *
import tkinter as tk
from tkinter.filedialog import askopenfilename

from os_activities import create_new_project
import glob

from simulation import run_simulation
from visualize import run_visualization
from shutil import copyfile
import easygui


class Project:
    def __init__(self, name):
        self.name = name

        self._simulations = []
        self._models = []
        self.update_simulations()

    def update_simulations(self):
        self._simulations = list(
            map(lambda x: x.split('/')[-1][:-5], glob.glob(f'Projects/{self.name}/Simulations/*.json')))

    @property
    def simulations(self):
        self.update_simulations()
        return self._simulations

    @property
    def models(self):
        self.update_models()
        print(self._models)
        return self._models

    def update_models(self):
        self._models = list(
            map(lambda x: x.split('/')[-1][:-4], glob.glob(f'Projects/{self.name}/Models/*.svg')))

    def get_simulation_path(self, name):
        pass

    def run_simulation(self, simulation_name):
        run_simulation(self.name, simulation_name)

    def run_visualization(self, simulation_name):
        run_visualization(self.name, simulation_name)

    def add_new_model(self):
        filename = askopenfilename(initialdir='/',
                                   message="Choose one or more files",
                                   multiple=True,
                                   title="File Selector")

        filename(filename, f'Projects/{self.name}/Models')
        self.update_models()


class EntryWithPlaceholder(tk.Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", color='grey'):
        super().__init__(master)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']

        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)

        self.put_placeholder()

    def put_placeholder(self):
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def foc_in(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete('0', 'end')
            self['fg'] = self.default_fg_color

    def foc_out(self, *args):
        if not self.get():
            self.put_placeholder()


class SimulationSettingsWindow:
    def __init__(self, project):

        self.project = project
        self.w = tk.Tk()

        Label(self.w, text='Create new simulation', font=('rosatom', 16, 'bold'), pady=5).pack()

        self.fields = {'SCREEN_SIZE': (500, 500),
                       'GRID_SIZE': (50, 50),
                       'GRID_CELL_SIZE': 10,
                       'SVG_SCALE': 1,
                       'SVG_DELTA': (0, 0),
                       'MODEL_FILENAME': None,
                       'FONT_NAME': 'Arial',
                       'AGENTS_AMOUNT': 30,
                       'PASSENGERS_SPAWN_RECTS': ((25, 45, 12, 2),),
                       'goal': (1, 1)}
        self.box = None

        # Create main form
        ents = self.makeform(self.w)

        self.w.bind('<Return>', (lambda event, e=ents: self.fetch(e)))
        b1 = tk.Button(self.w, text='Show',
                       command=(lambda e=ents: self.fetch(e)))
        b1.pack(side=tk.LEFT, padx=5, pady=5)
        b2 = tk.Button(self.w, text='Quit', command=self.w.quit)
        b2.pack(side=tk.LEFT, padx=5, pady=5)
        self.update_models()

    def fetch(self, entries):
        for entry in entries:
            field = entry[0]
            text = entry[1].get()
            print('%s: "%s"' % (field, text))

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
        entries.append(('', self.box))

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

        Label(self.w, text='Select simulation to visualize', font=('rosatom', 16)).pack()

        # Create SelectBox
        self.box = Listbox(self.w, selectmode=EXTENDED)
        self.box.pack()

        Button(self.w, command=self.run_new_simulation, text='Launch Visualizer', width=20).pack()
        Button(self.w, command=self.run_new_simulation, text='Create new simulation', width=20).pack()

        # Add scroll
        # scroll = Scrollbar(command=box.yview)
        # scroll.pack(side=LEFT, fill=Y)
        # box.config(yscrollcommand=scroll.set)

        self.box.bind('<<ListboxSelect>>', self.on_box_select)

        self.load_simulations()
        self.simulation_settings_window = None

    def on_box_select(self, *args):
        pass

    def load_simulations(self):
        # Clear the previous values
        self.box.delete(0, 'end')

        # Get the new
        simulations = self.project.simulations

        # Add new values to  ListBox
        for item in simulations:
            self.box.insert(END, item)

    def run_new_simulation(self):
        self.simulation_settings_window = SimulationSettingsWindow(self.project)


class MainWindow:
    def __init__(self):
        self.w = Tk()

        self.selected_project = tk.StringVar()
        self.selected_project.set("<- Select project")

        # Create SelectBox
        self.projects_box = Listbox(selectmode=EXTENDED)
        self.projects_box.pack(side=LEFT)

        # Add scroll
        # scroll = Scrollbar(command=box.yview)
        # scroll.pack(side=LEFT, fill=Y)
        # box.config(yscrollcommand=scroll.set)

        self.projects_box.bind('<<ListboxSelect>>', self.project_box_on_select)

        # Add items to SelectBox
        for item in get_projects():
            self.projects_box.insert(END, item)

        f = Frame()
        f.pack(side=LEFT, padx=10)

        selected_project_label = Label(f, textvariable=self.selected_project, font=('Rosatom', 16))
        selected_project_label.pack()

        Button(f, text="Open Project", command=self.open_project) \
            .pack(fill=X)

        """_ = Label(f, text='---- or ----', pady=2).pack()
        self.new_project_name = Entry(f)
        self.new_project_name.pack()

        Button(f, text="Create new project", command=self.create_project) \
            .pack(fill=X)"""

        self.simulation_window = None

    def run(self):
        self.w.mainloop()

    def project_box_on_select(self, *args):
        self.selected_project.set(self.projects_box.get(self.projects_box.curselection()))
        # selected_project_label.setvar('font', ('Rosatom', 16, 'bold'))
        # selected_project_label.pack()

    def create_project(self):
        new_name = self.new_project_name.get().strip()
        if new_name != '':
            create_new_project(new_name)

    def open_project(self, project_name=None):
        if project_name is None:
            try:
                project_name = self.projects_box.get(self.projects_box.curselection())
            except tk.TclError:
                return
        self.simulation_window = SimulationsWindow(project_name)


def get_projects():
    return list(next(os.walk('Projects'))[1])


if __name__ == "__main__":
    app = MainWindow()
    app.run()
