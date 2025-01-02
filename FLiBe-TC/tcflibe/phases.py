#!/bin/env python3
"""
Thermochimica phase calculations for FLiBe systems based on redox (fluorine potential) set by UF3 to UF4 pair.
PhaseAnalyzerFLiBeU - just FLiBe with uranium.
PhaseAnalyzerFLiBeUwithSS616 - FLiBe with uranium and SS316. Demonstration how to use inheritance.
Ondrej Chvala <ochvala@utexas.edu>
"""
import os
import numpy as np
import json
from tcflibe import FLiBeU, ss316, Thermochimica
DEBUG: int = 10


class PhaseAnalyzerFLiBeU:
    """ Thermochimica calculations for FLiBe-U, a base class """
    def __init__(self,
                 UF4_mol_pct: float = 5.0,
                 temps_k: str = '600:1000:10',
                 redoxes=np.linspace(-0.05, 0.05, 3).round(14)):
        self.cwd: str = os.getcwd()
        self.TC = Thermochimica()
        self.json_data_file_name = 'flibe.json'  # output file
        self.redoxes = redoxes  # UF3 to UF4 ratio
        self.temps_k: str = temps_k  # 'from : to : stride'
        self.UF4_mol_pct: float = UF4_mol_pct
        self.name: str = 'FLiBe-U'

    def set_elements(self, redox: float) -> dict:
        """ Sets FLiBe-U elements """
        return FLiBeU(self.UF4_mol_pct, redox)

    def run_redox_cases(self):
        """ Generates inputs and runs Thermochimica """
        for redox in self.redoxes:
            self.TC.header = f'{self.name}-U for UF4 = {self.UF4_mol_pct:.3f} mol%, UF3_to_UF4 = {redox:.6f}'
            self.TC.temps_k = self.temps_k
            self.TC.elements = self.set_elements(redox)
            case_dir: str = f'{self.name}_redox_{redox:.5f}'
            if not os.path.exists(case_dir):
                os.mkdir(case_dir)
            os.chdir(case_dir)
            with open(self.TC.deck_name, 'w') as f:
                f.write(self.TC.tc_input())
            print(f'Running {self.TC.header}')
            self.TC.run_tc()
            os.chdir(self.cwd)

    def analyze_jsons(self):
        """ Analyses Thermochimica JSON outputs and produces JSON summary file """
        results: dict = {}  # Output data
        for redox in self.redoxes:
            case_dir: str = f'{self.name}_redox_{redox:.5f}'
            results[redox] = {}
            with open(os.path.join(case_dir, self.TC.thermo_output_name), 'r') as f:
                data = json.load(f)
            for temperature_case in data.values():
                temp_k: float = temperature_case['temperature']
                gas: float = 0
                solution: float = 0
                solid: float = 0
                if DEBUG > 2:
                    print(f'{self.name} for UF4 = {self.UF4_mol_pct:.3f} mol%, UF3_to_UF4 = {redox:.6f}, T = {temp_k:.6f}')
                for phase_name, phase in temperature_case['solution phases'].items():
                    if float(phase['moles']) > 0.0:
                        if 'gas' in phase_name:
                            gas += float(phase["moles"])
                        elif 'MSFL' in phase_name or 'P3c1' in phase_name or 'P21_c' in phase_name:
                            solution += float(phase["moles"])
                        else:
                            raise ValueError(f'Unknown phase {phase_name}')
                        if DEBUG > 5:
                            print("solutions: ", phase_name, phase['phase model'], phase["moles"])
                for phase_name, phase in temperature_case['pure condensed phases'].items():
                    if float(phase['moles']) > 0.0:
                        solid += phase["moles"]
                        if DEBUG > 5:
                            print("condensed: ", phase_name, phase["moles"])
                results[redox][temp_k] = (gas, solution, solid)
                if DEBUG > 5:
                    print()

        with open(self.json_data_file_name, 'w') as f:
            json.dump(results, f, indent=4)

    def plot_results(self):
        """ Plots the phase structure of the salt """
        assert os.path.exists(self.json_data_file_name)
        with open(self.json_data_file_name, 'r') as f:
            results: dict = json.load(f)
        import matplotlib.pyplot as plt
        x: list = []
        y: list = []
        for redox in results.keys():
            x.append(redox)
        for temp_k in results[x[0]].keys():
            y.append(temp_k)

        # Setup 3D plotting data
        g_data = []
        for k in range(3):
            g_data.append(np.zeros((len(y), len(x))))
        titles = ['Gas', 'Liquid', 'Solid']
        cmaps = ['Blues', 'Greens', 'Reds']

        for redox in x:
            i: int = x.index(redox)
            for t in y:
                j: int = y.index(t)
                norm_factor: float = sum(results[redox][t])
                for k in range(3):
                    g_data[k][j][i] = results[redox][t][k] / norm_factor

        if DEBUG > 7:
            print(g_data[0])

        x = [float(xx) for xx in x]
        y = [float(xx) for xx in y]
        for k in range(3):  # Makes fraction plots separate for each phase
            plt.close('all')
            plt.xscale('linear')
            fig, ax = plt.subplots()
            c = ax.pcolormesh(x, y, g_data[k], cmap=cmaps[k])
            ax.set_title(f'{self.name} {titles[k]} fraction')
            ax.set_xlabel(f'Fluorine potential as UF3 / UF4')
            ax.set_ylabel(f'Temperature [K]')
            ax.axis([min(x), max(x), min(y), max(y)])
            fig.colorbar(c, ax=ax)
            fig.savefig(f'{self.name}_{titles[k]}.png')
            # fig.show()

        # Just for fun RGB image
        plt.close('all')
        fig, ax = plt.subplots()
        r = g_data[2]
        g = g_data[1]
        b = g_data[0]
        rgb = np.dstack((r, g, b))
        ax.set_title(f'{self.name} phase fractions as RGB image')
        ax.set_xlabel(f'Fluorine potential as UF3 / UF4')
        ax.set_ylabel(f'Temperature [K]')
        ax.pcolor(x, y, rgb)
        ax.axis([min(x), max(x), min(y), max(y)])
        fig.savefig(f'{self.name}_RGB.png')
        # fig.show()


class PhaseAnalyzerFLiBeUwithSS616(PhaseAnalyzerFLiBeU):
    """ Thermochimica calculations for FLiBe-U with SS316 using inheritance """
    def __init__(self, UF4_mol_pct: float = 5.0, temps_k: str = '600:1000:10',
                 redoxes=np.linspace(-0.05, 0.05, 3).round(14)):
        super().__init__(UF4_mol_pct, temps_k, redoxes)
        self.json_data_file_name = 'flibe_ss316.json'  # output file
        self.name: str = 'FLiBe-U_SS316'

    def set_elements(self, redox: float) -> dict:
        """ Sets FLiBe-U + SS-316 elements """
        return FLiBeU(self.UF4_mol_pct, redox) | ss316()  # Notice this union does not work if the dicts share keys!


def run_flibeu():
    """ FLiBe-U calculation """
    my_redoxes = np.linspace(-0.05, 0.1, 16).round(14)  # np.linspace(-0.05, 0.05, 3).round(14):
    my_temps_k: str = '600:1000:10'  # 'from : to : stride'
    my_UF4_mol_pct: float = 5.0
    flibeph = PhaseAnalyzerFLiBeU(UF4_mol_pct=my_UF4_mol_pct, redoxes=my_redoxes, temps_k=my_temps_k)
    flibeph.run_redox_cases()
    flibeph.analyze_jsons()
    flibeph.plot_results()


def run_flibeuss316():
    """ FLiBe-U with SS-316 calculation """
    my_redoxes = np.linspace(-0.05, 0.1, 16).round(14)  # np.linspace(-0.05, 0.05, 3).round(14):
    my_temps_k: str = '600:1000:10'  # 'from : to : stride'
    my_UF4_mol_pct: float = 5.0
    flibe_ss_ph = PhaseAnalyzerFLiBeUwithSS616(UF4_mol_pct=my_UF4_mol_pct, redoxes=my_redoxes, temps_k=my_temps_k)
    flibe_ss_ph.run_redox_cases()
    flibe_ss_ph.analyze_jsons()
    flibe_ss_ph.plot_results()


if __name__ == '__main__':
    # run_flibeu()
    run_flibeuss316()
