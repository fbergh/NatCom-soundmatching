import os
import datetime
import json
import numpy as np
import matplotlib.pyplot as plt

class Logger:
    def __init__(self, path, description=""):
        super().__init__()
        self.date = str(datetime.datetime.now()).replace(" ", "-").replace(":","-")
        self.path = os.path.join(path, self.date + '.json')
        if not os.path.exists(path):
            os.mkdir(path)
        self.log = {'description': description, 'targets': []}
        self._curr_target = None

    def set_header(self, header_parameters):
        for k in header_parameters:
            self.log[k] = header_parameters[k]

    def set_target(self, target):
        self._curr_target = len(self.log['targets'])
        self.log['targets'].append({'target': target, 'runs': []})

    def add_run(self, best, best_fit, n_gens, early_stopping,
                runtime, gen_stats):
        if self._curr_target is None:
            raise AssertionError('No target so far. ' +
                                 'Can\'t add a new run for an unknown target')

        run_obj = {
            'best': best,
            'best_fit': float(best_fit),
            'n_gens': n_gens,
            'early_stopping': early_stopping,
            'runtime': runtime,
            'gen_stats': gen_stats
        }

        self.log['targets'][self._curr_target]['runs'].append(run_obj)

    def calculate_metrics(self, for_all_targets=True):
        metrics = {}
        metrics['mean_fitness'] = self._mean_fitness(for_all_targets)
        metrics['proportion_of_early_stopping'] = self._proportion_of_early_stopping(for_all_targets)
        metrics['fitness_evaluations_per_run'] = self._evaluations_per_run(for_all_targets)
        if for_all_targets:
            self.log['metrics'] = metrics
        else:
            self.log['targets'][-1]['metrics'] = metrics

    def _mean_fitness(self, for_all_targets):
        fitness = 0
        iterable = self.log['targets'] if for_all_targets else [self.log['targets'][-1]]
        for t in iterable:
            target_fitness = [r['best_fit'] for r in t['runs']]
            fitness += np.mean(target_fitness)
        if for_all_targets:
            fitness /= len(self.log['targets'])
        return fitness

    def _proportion_of_early_stopping(self, for_all_targets):
        total = 0
        iterable = self.log['targets'] if for_all_targets else [self.log['targets'][-1]]
        for t in iterable:
            targen_prop = [r['early_stopping'] for r in t['runs']]
            total += np.sum(targen_prop) / len(t['runs'])
        if for_all_targets:
            total /= len(self.log['targets'])
        return total

    def _evaluations_per_run(self, for_all_targets):
        mean_n_gens = 0
        iterable = self.log['targets'] if for_all_targets else [self.log['targets'][-1]]
        for t in iterable:
            targen_n_gens = [r['n_gens'] for r in t['runs']]
            mean_n_gens += np.mean(targen_n_gens)
        if for_all_targets:
            mean_n_gens /= len(self.log['targets'])
        return mean_n_gens * self.log['pop_size']

    def close(self):
        self.calculate_metrics()
        with open(self.path, 'w') as outfile:
            json.dump(self.log, outfile, indent = "  ")
