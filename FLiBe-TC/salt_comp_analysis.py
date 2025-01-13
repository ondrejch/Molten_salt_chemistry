#!/bin/env python3
"""
Analysis of species concentrations in solution and gas phases from Thermochimica calculations,
with support for processing multiple directories.
"""
import os
import numpy as np
import json
import matplotlib.pyplot as plt
from pathlib import Path

class SpeciesAnalyzer:
    def __init__(self, phase_name, species_list=None):
        """
        Initialize the species analyzer
        
        Args:
            phase_name (str): Name of the phase to analyze (e.g., 'MSFL' or 'gas_ideal')
            species_list (list): List of species to plot. If None, all species will be plotted
        """
        self.phase_name = phase_name
        self.species_list = species_list
        self.results = {}
        
    def process_directory(self, directory_path):
        """
        Process a single directory containing my_tc.json file.
        
        Args:
            directory_path (Path): Path to the directory to process
        """
        json_file = directory_path / "my_tc.json"
        if not json_file.exists():
            print(f"No my_tc.json found in {directory_path}")
            return
        
        # Create output directory if it doesn't exist
        output_dir = Path("processed_results")
        output_dir.mkdir(exist_ok=True)
        
        # Create subdirectory for this specific analysis
        analysis_dir = output_dir / directory_path.name
        analysis_dir.mkdir(exist_ok=True)
        
        # Extract redox value from directory name
        try:
            redox = float(directory_path.name.split('_')[-1])
        except ValueError:
            print(f"Could not extract redox value from directory name: {directory_path.name}")
            return
            
        # Process the JSON file
        self.process_json_file(str(json_file), redox, analysis_dir)

    def process_json_file(self, filepath, redox, output_dir):
        """Process a single JSON file and store results"""
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        self.results[redox] = {}
        
        # Extract actual temperature values and sort data points
        temp_data_pairs = [(float(data[k]['temperature']), k) for k in data.keys()]
        temp_data_pairs.sort()
        
        # Process each temperature point
        for temp, key in temp_data_pairs:
            species_data = self._process_temperature_case(data[key])
            self.results[redox][temp] = species_data

    def _process_temperature_case(self, temperature_case):
        """Extract species concentrations from a single temperature case"""
        species_data = {}
        
        # Get the phase data from solution phases
        phase_data = temperature_case['solution phases'].get(self.phase_name, {})
        
        if self.phase_name == 'MSFL':
            # Handle solution phase (MSFL) data
            total_moles = float(phase_data.get('moles', 0.0))
            
            if total_moles > 0:
                cations = phase_data.get('cations', {})
                for cation, data in cations.items():
                    mole_fraction = float(data.get('mole fraction', 0.0))
                    species_data[cation] = mole_fraction * total_moles
            else:
                # If phase not present, set all cations to 0
                if 'cations' in phase_data:
                    for cation in phase_data['cations']:
                        species_data[cation] = 0.0
        else:
            # Handle gas phase data
            if 'species' in phase_data:
                for species, data in phase_data['species'].items():
                    if self.species_list is None or species in self.species_list:
                        mole_fraction = float(data.get('mole fraction', 0.0))
                        species_data[species] = mole_fraction
                    
        return species_data
    
    def plot_results(self, output_dir):
        """Creates heatmap plots for each species concentration"""
        if not self.results:
            print("No results to plot")
            return
            
        # Setup the coordinate grids
        redoxes = sorted(list(self.results.keys()))
        temps = sorted(list(self.results[redoxes[0]].keys()))
        
        # Get all species if not specified
        if self.species_list is None:
            self.species_list = set()
            for redox in self.results:
                for temp in self.results[redox]:
                    self.species_list.update(self.results[redox][temp].keys())
        
        # Create a plot for each species
        for species in self.species_list:
            # Setup species concentration data
            Z = np.zeros((len(temps), len(redoxes)))
            for i, redox in enumerate(redoxes):
                for j, temp in enumerate(temps):
                    if redox in self.results and temp in self.results[redox]:
                        Z[j, i] = self.results[redox][temp].get(species, 0.0)
            
            # Create the plot
            plt.close('all')
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Create standard heatmap
            c = ax.pcolormesh(redoxes, temps, Z, cmap='viridis', shading='auto')
            
            # Commented out logarithmic plotting option for future use
            # from matplotlib.colors import LogNorm
            # Z_masked = np.ma.masked_where(Z <= 0, Z)
            # if np.any(Z_masked > 0):
            #     min_val = Z_masked[Z_masked > 0].min()
            #     max_val = Z_masked.max()
            #     c = ax.pcolormesh(redoxes, temps, Z_masked, 
            #                     cmap='viridis', 
            #                     shading='auto',
            #                     norm=LogNorm(vmin=min_val, vmax=max_val))
            
            # Add labels and title
            ax.set_title(f'{species} in {self.phase_name}')
            ax.set_xlabel('Fluorine potential as UF3 / UF4')
            ax.set_ylabel('Temperature [K]')
            
            # Add grid
            ax.grid(True, linestyle='--', which='major', color='grey', alpha=0.3)
            
            # Add colorbar
            label = 'Moles' if self.phase_name == 'MSFL' else 'Mole Fraction'
            cbar = fig.colorbar(c, ax=ax, label=label)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save the plot
            output_path = output_dir / f'{self.phase_name}_{species}_concentration.png'
            fig.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()

def main():
    """
    Process all directories containing my_tc.json files.
    """
    # Get the current directory
    current_dir = Path.cwd()
    
    # Find all directories that match the pattern
    target_dirs = [d for d in current_dir.iterdir() 
                  if d.is_dir() and 
                  (d.name.startswith("FLiBe_redox_") or d.name.startswith("Struct_FLiBe_redox_"))]
    
    if not target_dirs:
        print("No matching directories found.")
        return
    
    # Create analyzer instances for both MSFL and gas phases
    analyzers = [
        SpeciesAnalyzer(phase_name='MSFL'),
        SpeciesAnalyzer(phase_name='gas_ideal')  # Changed from 'gas' to 'gas_ideal'
    ]
    
    # Process each directory for both analyzers
    for directory in sorted(target_dirs):
        print(f"\nProcessing directory: {directory.name}")
        for analyzer in analyzers:
            analyzer.process_directory(directory)
            print(f"Completed processing {directory.name} for {analyzer.phase_name}")
    
    # Create output directory for plots
    output_dir = Path("processed_results") / "species_plots"
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Create plots for both analyzers
    for analyzer in analyzers:
        analyzer.plot_results(output_dir)
    
    print("\nPlotting completed. Results saved in:", output_dir)

if __name__ == "__main__":
    main()