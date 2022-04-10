from multiprocessing import Pool

def launching_function(experiment):
    experiment.launch()

class Experiment:
    def __init__(self, experiment_units):
        self.experiment_units = experiment_units

    def add_experiment_unit(self, unit):
        self.experiment_units.append(unit)

    def launch(self, n_processes):
        with Pool(n_processes) as pool:
            pool.map(launching_function, self.experiment_units)

