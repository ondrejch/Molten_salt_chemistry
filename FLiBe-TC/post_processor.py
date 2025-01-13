#!/usr/bin/env python3
"""
Unified post-processor for Thermochimica calculations.
Combines phase analysis and species concentration calculations
with support for processing multiple directories.
"""
import os
import numpy as np
import json
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, List, Tuple, Optional

class ThermochimicaProcessor:
    def __init__(self):
        """Initialize the Thermochimica processor"""
        # Dictionary to store phases and their conditions {phase: {redox: set(temperatures)}}
        self.nonzero_phases = defaultdict(lambda: defaultdict(set))
        # Dictionary to store processed data for plotting
        self.processed_data: Dict[str, Dict] = {}
        
    def process_directories(self, base_dir: Optional[Path] = None) -> None:
        """
        Process all directories containing my_tc.json files.
        
        Args:
            base_dir (Path, optional): Base directory to search. Defaults to current directory.
        """
        current_dir = base_dir if base_dir else Path.cwd()
        
        # Find all directories that match the pattern
        target_dirs = [d for d in current_dir.iterdir() 
                      if d.is_dir() and 
                      (d.name.startswith("FLiBe_redox_") or 
                       d.name.startswith("Struct_FLiBe_redox_"))]
        
        if not target_dirs:
            print("No matching directories found.")
            return
        
        # Create species plots directory
        species_plots_dir = Path("processed_results") / "species_plots"
        species_plots_dir.mkdir(exist_ok=True, parents=True)
        
        # Dictionary to store data for species comparison
        species_comparison_data = defaultdict(lambda: defaultdict(list))
        redox_values = []
        
        # Process each directory
        for directory in sorted(target_dirs):
            print(f"\nProcessing directory: {directory.name}")
            
            # Extract redox value
            try:
                redox = float(directory.name.split('_')[-1])
                redox_values.append(redox)
            except ValueError:
                print(f"Could not extract redox value from directory name: {directory.name}")
                continue
                
            self.process_single_directory(directory)
            
            # Collect data for species comparison
            for species, data in self.processed_data[directory.name]['moles_data'].items():
                species_comparison_data[species][redox] = {
                    'temperatures': self.processed_data[directory.name]['temperatures'],
                    'moles': data,
                    'mole_fractions': data / self.processed_data[directory.name]['total_mol']
                }
            
            print(f"Completed processing {directory.name}")
            
        # Generate species comparison plots
        self.generate_species_comparison_plots(species_comparison_data, redox_values, species_plots_dir)
        
        # Create output directory for other results
        output_dir = Path("processed_results")
        
        # Write the phase report
        self.write_phase_report(output_dir)
        
        # Generate plots for each processed directory
        self.generate_all_plots(output_dir)
        
        print("\nProcessing completed. Results saved in:", output_dir)

    def generate_species_comparison_plots(self, species_data: Dict, 
                                       redox_values: List[float],
                                       output_dir: Path) -> None:
        """
        Generate comparison plots for each species across different redox values.
        
        Args:
            species_data (Dict): Dictionary containing species data across redox values
            redox_values (List[float]): List of redox values
            output_dir (Path): Directory to save the plots
        """
        # Sort redox values for consistent plotting
        redox_values.sort()
        
        # Create plots for each species
        for species in species_data:
            # Create moles plot
            plt.figure(figsize=(12, 8))
            for redox in redox_values:
                if redox in species_data[species]:
                    data = species_data[species][redox]
                    plt.plot(data['temperatures'], data['moles'],
                            label=f'Redox {redox}',
                            marker='o', markersize=4, markevery=5)
            
            self._format_plot(f"Moles of {species} vs Temperature across Redox Values",
                            "Temperature (K)", "Moles")
            plt.savefig(output_dir / f"{species}_moles_comparison.png",
                       bbox_inches='tight', dpi=300)
            plt.close()
            
            # Create mole fraction plot
            plt.figure(figsize=(12, 8))
            for redox in redox_values:
                if redox in species_data[species]:
                    data = species_data[species][redox]
                    plt.plot(data['temperatures'], data['mole_fractions'],
                            label=f'Redox {redox}',
                            marker='o', markersize=4, markevery=5)
            
            self._format_plot(f"Mole Fraction of {species} vs Temperature across Redox Values",
                            "Temperature (K)", "Mole Fraction")
            plt.savefig(output_dir / f"{species}_molfrac_comparison.png",
                       bbox_inches='tight', dpi=300)
            plt.close()


    def process_single_directory(self, directory_path: Path) -> None:
        """
        Process a single directory containing my_tc.json file.
        
        Args:
            directory_path (Path): Path to the directory to process
        """
        json_file = directory_path / "my_tc.json"
        if not json_file.exists():
            print(f"No my_tc.json found in {directory_path}")
            return
        
        # Extract redox value from directory name
        try:
            redox = float(directory_path.name.split('_')[-1])
        except ValueError:
            print(f"Could not extract redox value from directory name: {directory_path.name}")
            return
        
        # Process the JSON file for phase analysis
        self.process_json_file(str(json_file), redox)
        
        # Process the JSON file for concentration analysis
        self.process_concentrations(str(json_file), directory_path.name)

    def process_json_file(self, filepath: str, redox: float) -> None:
        """
        Process a single JSON file and track non-zero phases.
        
        Args:
            filepath (str): Path to the JSON file
            redox (float): Redox value for the current directory
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Process each temperature point
        for temp_key in data.keys():
            temperature = float(data[temp_key]['temperature'])
            self._process_temperature_case(data[temp_key], redox, temperature)

    def _process_temperature_case(self, temperature_case: Dict, redox: float, 
                                temperature: float) -> None:
        """
        Track non-zero phases from a single temperature case.
        
        Args:
            temperature_case (Dict): Data for a single temperature point
            redox (float): Redox value
            temperature (float): Temperature value
        """
        # Process solution phases
        if 'solution phases' in temperature_case:
            for phase_name, phase_data in temperature_case['solution phases'].items():
                if float(phase_data.get('moles', 0.0)) > 0:
                    self.nonzero_phases[phase_name][redox].add(temperature)

        # Process pure condensed phases
        if 'pure condensed phases' in temperature_case:
            for phase_name, phase_data in temperature_case['pure condensed phases'].items():
                if float(phase_data.get('moles', 0.0)) > 0:
                    self.nonzero_phases[phase_name][redox].add(temperature)

    def process_concentrations(self, filepath: str, directory_name: str) -> None:
        """
        Process concentration data from a JSON file.
        
        Args:
            filepath (str): Path to the JSON file
            directory_name (str): Name of the directory being processed
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Extract and sort temperature data
        temp_data_pairs = [(float(data[k]['temperature']), k) for k in data.keys()]
        temp_data_pairs.sort()
        temperatures, sorted_keys = zip(*temp_data_pairs)
        
        # Collect non-zero species data
        non_zero_species = []
        for key in sorted_keys:
            temp_species = []
            for species, phase_data in data[key]['solution phases'].items():
                if phase_data['moles'] != 0:
                    temp_species.append((species, True))
            for species, phase_data in data[key]['pure condensed phases'].items():
                if phase_data['moles'] != 0:
                    temp_species.append((species, False))
            non_zero_species.append(temp_species)
        
        # Get unique species
        all_species = set(item for sublist in non_zero_species for item in sublist)
        
        # Extract moles data
        moles_data = {}
        for species, is_solution in all_species:
            species_key = species.replace('(s)', '').replace('(s2)', '').replace('(s3)', '')
            moles = []
            for key in sorted_keys:
                if is_solution:
                    moles.append(data[key]['solution phases'][species]['moles'])
                else:
                    moles.append(data[key]['pure condensed phases'][species]['moles'])
            moles_data[species_key] = np.array(moles)
        
        # Calculate total moles
        total_mol = np.zeros(len(sorted_keys))
        for key, moles in moles_data.items():
            total_mol += moles
        
        # Store processed data
        self.processed_data[directory_name] = {
            'temperatures': temperatures,
            'moles_data': moles_data,
            'total_mol': total_mol
        }

    def write_phase_report(self, output_dir: Path) -> None:
        """
        Write a report of all non-zero phases and their conditions.
        
        Args:
            output_dir (Path): Directory to save the report
        """
        output_path = output_dir / 'nonzero_phases_report.txt'
        
        with open(output_path, 'w') as f:
            f.write("Non-zero Phases Report\n")
            f.write("=" * 50 + "\n\n")
            
            # Sort phases alphabetically
            sorted_phases = sorted(self.nonzero_phases.keys())
            
            # Write solution phases
            f.write("Solution Phases:\n")
            f.write("-" * 20 + "\n")
            self._write_phase_section(f, sorted_phases, ['MSFL', 'gas_ideal', 'MSFL#3'])
            
            # Write pure condensed phases
            f.write("\nPure Condensed Phases:\n")
            f.write("-" * 20 + "\n")
            self._write_phase_section(f, sorted_phases, 
                                    exclude=['MSFL', 'gas_ideal', 'MSFL#3'])

    def _write_phase_section(self, f, phases: List[str], 
                           include: Optional[List[str]] = None,
                           exclude: Optional[List[str]] = None) -> None:
        """
        Write a section of the phase report.
        
        Args:
            f: File handle
            phases (List[str]): List of phases to process
            include (List[str], optional): List of phases to include
            exclude (List[str], optional): List of phases to exclude
        """
        for phase in phases:
            if ((include and phase in include) or 
                (exclude and phase not in exclude) or 
                (not include and not exclude)):
                f.write(f"\nPhase: {phase}\n")
                sorted_redox = sorted(self.nonzero_phases[phase].keys())
                for redox in sorted_redox:
                    temps = sorted(self.nonzero_phases[phase][redox])
                    f.write(f"\nRedox value: {redox}\n")
                    f.write("Temperatures [K]:\n")
                    temps_str = [f"{temp:8.2f}" for temp in temps]
                    for i in range(0, len(temps_str), 5):
                        f.write("  " + "  ".join(temps_str[i:i+5]) + "\n")

    def generate_all_plots(self, output_dir: Path) -> None:
        """
        Generate plots for all processed directories.
        
        Args:
            output_dir (Path): Directory to save the plots
        """
        for directory_name, data in self.processed_data.items():
            directory_output = output_dir / directory_name
            directory_output.mkdir(exist_ok=True, parents=True)
            
            self._plot_moles(data['temperatures'], data['moles_data'], 
                           directory_output / f"{directory_name}_moles")
            self._plot_mole_fractions(data['temperatures'], data['moles_data'],
                                    data['total_mol'], 
                                    directory_output / f"{directory_name}_molfrac")

    def _plot_moles(self, temperatures: List[float], moles_data: Dict,
                   base_filename: Path) -> None:
        """
        Create a plot of moles vs temperature.
        
        Args:
            temperatures (List[float]): Temperature values
            moles_data (Dict): Dictionary of moles data
            base_filename (Path): Base filename for the plot
        """
        plt.figure(figsize=(12, 8))
        colors = plt.cm.tab20(np.linspace(0, 1, len(moles_data)))
        markers = ['o', 's', '^', 'x', 'd', '*', 'v', '<', '>', 'p', 'h', '8', 'D', 'P']
        
        for (species, moles), color, marker in zip(moles_data.items(), colors, 
                                                 markers * 2):
            plt.plot(temperatures, moles, label=species, color=color,
                    marker=marker, markersize=6, markevery=5)
        
        self._format_plot("Moles of Different Compounds vs Temperature",
                         "Temperature (K)", "Moles")
        plt.savefig(f"{base_filename}.png", bbox_inches='tight', dpi=300)
        plt.close()

    def _plot_mole_fractions(self, temperatures: List[float], moles_data: Dict,
                            total_mol: np.ndarray, base_filename: Path) -> None:
        """
        Create a plot of mole fractions vs temperature.
        
        Args:
            temperatures (List[float]): Temperature values
            moles_data (Dict): Dictionary of moles data
            total_mol (np.ndarray): Array of total moles
            base_filename (Path): Base filename for the plot
        """
        plt.figure(figsize=(12, 8))
        colors = plt.cm.tab20(np.linspace(0, 1, len(moles_data)))
        markers = ['o', 's', '^', 'x', 'd', '*', 'v', '<', '>', 'p', 'h', '8', 'D', 'P']
        
        for (species, moles), color, marker in zip(moles_data.items(), colors,
                                                 markers * 2):
            mol_frac = moles / total_mol
            plt.plot(temperatures, mol_frac, label=species, color=color,
                    marker=marker, markersize=6, markevery=5)
        
        self._format_plot("Mole Fractions of Different Compounds vs Temperature",
                         "Temperature (K)", "Mole Fraction")
        plt.savefig(f"{base_filename}.png", bbox_inches='tight', dpi=300)
        plt.close()

    @staticmethod
    def _format_plot(title: str, xlabel: str, ylabel: str) -> None:
        """
        Apply common formatting to plots.
        
        Args:
            title (str): Plot title
            xlabel (str): X-axis label
            ylabel (str): Y-axis label
        """
        plt.grid(True, linestyle='--', which='major', color='grey', alpha=0.5)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        plt.gca().xaxis.set_major_locator(plt.MaxNLocator(10))
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left',
                  fontsize='small', framealpha=0.8)
        plt.tight_layout()

def main():
    """Main entry point for the script."""
    processor = ThermochimicaProcessor()
    processor.process_directories()

if __name__ == "__main__":
    main()