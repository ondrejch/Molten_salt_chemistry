#!/bin/env python3
"""
Thermochimica calculations for FLiBe-U + steel.
This needs work since there will always be some solid.
Ondrej Chvala <ochvala@utexas.edu>
"""
import os
import numpy as np
import json
from tcflibe import FLiBeU, ss316, Thermochimica

DEBUG: int = 10


class StructPhaseAnalyzer:
    def __init__(self,
                UF4_mol_pct: float = 5.0,
                temps_k: str = '600:1000:10',
                redoxes=np.linspace(-0.05, 0.05, 3).round(14),
                salt_moles: float = 1.0,
                steel_moles: float = 1.0):
        self.cwd: str = os.getcwd()
        self.TC = Thermochimica()
        self.json_data_file_name = 'struct_w_flibe.json'
        self.redoxes = redoxes
        self.temps_k: str = temps_k
        self.UF4_mol_pct: float = UF4_mol_pct
        self.salt_moles = salt_moles
        self.steel_moles = steel_moles

    def _combine_compositions(self, flibe_comp: dict, steel_comp: dict, salt_moles: float = 1.0, steel_moles: float = 1.0) -> dict:
        """
        Combines the compositions of FLiBe and steel with specified molar ratios
        
        Args:
            flibe_comp (dict): Normalized composition of FLiBe salt
            steel_comp (dict): Normalized composition of steel
            salt_moles (float): Number of moles of salt
            steel_moles (float): Number of moles of steel
        """
        combined = {}
        # Scale each composition by its number of moles
        for e, v in flibe_comp.items():
            combined[e] = v * salt_moles
        for e, v in steel_comp.items():
            if e in combined:
                combined[e] += v * steel_moles
            else:
                combined[e] = v * steel_moles
                
        # Normalize to sum to 1
        total = sum(combined.values())
        return {e: v/total for e, v in combined.items()}

    def run_redox_cases(self):
        """ Generates inputs and runs Thermochimica """
        for redox in self.redoxes:
            self.TC.header = f'FLiBe-U + SS316 for UF4 = {self.UF4_mol_pct:.3f} mol%, UF3_to_UF4 = {redox:.6f}'
            self.TC.temps_k = self.temps_k
            # Combine FLiBe and steel compositions
            flibe_comp = FLiBeU(self.UF4_mol_pct, redox)
            steel_comp = ss316()
            self.TC.elements = self._combine_compositions(flibe_comp, steel_comp, salt_moles=self.salt_moles, steel_moles=self.steel_moles)
            
            case_dir: str = f'Struct_FLiBe_redox_{redox:.5f}'
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
        results: dict = {}
        for redox in self.redoxes:
            case_dir: str = f'Struct_FLiBe_redox_{redox:.5f}'
            results[redox] = {}
            with open(os.path.join(case_dir, self.TC.thermo_output_name), 'r') as f:
                data = json.load(f)
            for temperature_case in data.values():
                temp_k: float = temperature_case['temperature']
                gas: float = 0
                solution: float = 0
                solid: float = 0
                
                # Process solution phases
                for phase_name, phase in temperature_case['solution phases'].items():
                    if float(phase['moles']) > 0.0:
                        if 'gas' in phase_name.lower():
                            gas += float(phase["moles"])
                        else:
                            # All non-gas solution phases count as liquid
                            solution += float(phase["moles"])
                        if DEBUG > 5:
                            print("solutions: ", phase_name, phase['phase model'], phase["moles"])
                
                # Process pure condensed phases
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
            ax.set_title(f'{titles[k]} fraction')
            ax.set_xlabel(f'Fluorine potential as UF3 / UF4')
            ax.set_ylabel(f'Temperature [K]')
            ax.axis([min(x), max(x), min(y), max(y)])
            fig.colorbar(c, ax=ax)
            fig.savefig(f'FLiBe_Steel2_{titles[k]}.png')
            # fig.show()

        # Just for fun RGB image
        plt.close('all')
        fig, ax = plt.subplots()
        r = g_data[2]
        g = g_data[1]
        b = g_data[0]
        rgb = np.dstack((r, g, b))
        ax.set_title(f'FLiBe-U + SS316 phase fractions as RGB image')
        ax.set_xlabel(f'Fluorine potential as UF3 / UF4')
        ax.set_ylabel(f'Temperature [K]')
        ax.pcolor(x, y, rgb)
        ax.axis([min(x), max(x), min(y), max(y)])
        fig.savefig(f'FLiBe_RGB.png')
        # fig.show()


if __name__ == '__main__':
    """ Set parameters for Thermochimica fuel salt calculation """
    redoxes = np.linspace(-0.05, 0.1, 16).round(14)  # np.linspace(-0.05, 0.05, 3).round(14):
    temps_k: str = '600:1000:10'  # 'from : to : stride'
    UF4_mol_pct: float = 5.0
    structph = StructPhaseAnalyzer(UF4_mol_pct=UF4_mol_pct, redoxes=redoxes, temps_k=temps_k)
    structph.run_redox_cases()
    structph.analyze_jsons()
    structph.plot_results()
