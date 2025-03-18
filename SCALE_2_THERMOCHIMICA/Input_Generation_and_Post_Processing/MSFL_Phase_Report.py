import os
import csv
import logging
import numpy as np
import matplotlib.pyplot as plt
from collections import OrderedDict, defaultdict
from typing import Dict, Any, List, Set, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MSFL-Phase-Analysis-Report')

class MSFLPhaseAnalysisReportGenerator:
    """
    Generates reports and plots for MSFL phase presence, mole amounts, and composition over time.
    
    Works alongside the CondensedReportGenerator to analyze the condensed report data,
    but focuses exclusively on MSFL (molten salt) phases.
    """
    
    def __init__(self, condensed_report: OrderedDict):
        """
        Initialize the MSFL Phase Analysis Report Generator.
        
        Args:
            condensed_report (OrderedDict): Condensed report from CondensedReportGenerator
        """
        self.condensed_report = condensed_report
        self.timesteps = sorted([int(ts) for ts in self.condensed_report.keys()])
        self.str_timesteps = [str(ts) for ts in self.timesteps]
        # Track MSFL phases with moles > 0 for reporting
        self.significant_msfl_phases = set()
        
    def generate_phase_presence_report(self) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Analyzes the condensed report and creates a report of which MSFL phases 
        have moles > 0.0 at each timestep.
        
        Returns:
            Tuple[List[str], List[Dict[str, Any]]]: Headers and rows for the CSV report
        """
        logger.info("Generating MSFL phase presence report")
        
        # Collect all unique MSFL phases across all timesteps
        all_msfl_phases = set()
        
        # First pass: identify all MSFL phases across all timesteps
        for timestep, data in self.condensed_report.items():
            first_key = next(iter(data))
            
            # Extract solution phases (MSFL only)
            if "solution phases" in data[first_key]:
                for phase, phase_data in data[first_key]["solution phases"].items():
                    if phase.startswith("MSFL") and "moles" in phase_data and float(phase_data["moles"]) > 0.0:
                        all_msfl_phases.add(phase)
        
        # Sort phases for consistent output
        all_msfl_phases = sorted(all_msfl_phases)
        
        # Create headers for CSV
        headers = ["Timestep", "# MSFL phases"]
        
        # Add MSFL phase headers
        for phase in all_msfl_phases:
            headers.append(f"S:{phase}")
        
        # Second pass: create rows for each timestep
        rows = []
        for timestep, data in self.condensed_report.items():
            first_key = next(iter(data))
            row = defaultdict(int)  # Default to 0 for phases not present
            
            # Add basic timestep info
            row["Timestep"] = timestep
            
            # Count phases and track presence
            msfl_phases_count = 0
            
            # Process solution phases (MSFL only)
            if "solution phases" in data[first_key]:
                solution_phase_data = data[first_key]["solution phases"]
                # Count MSFL phases with moles > 0
                for phase, phase_data in solution_phase_data.items():
                    if phase.startswith("MSFL") and "moles" in phase_data and float(phase_data["moles"]) > 0.0:
                        row[f"S:{phase}"] = 1
                        msfl_phases_count += 1
            
            # Add phase counts
            row["# MSFL phases"] = msfl_phases_count
            
            rows.append(dict(row))
        
        logger.info(f"Generated MSFL report with {len(rows)} timesteps and {len(headers) - 2} unique MSFL phases")
        return headers, rows
    
    def generate_phase_mole_amounts_report(self) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Analyzes the condensed report and creates a report of mole amounts for each MSFL phase at each timestep.
        
        Returns:
            Tuple[List[str], List[Dict[str, Any]]]: Headers and rows for the CSV report
        """
        logger.info("Generating MSFL phase mole amounts report")
        
        # Collect all unique MSFL phases across all timesteps
        all_msfl_phases = set()
        
        # First pass: identify all MSFL phases across all timesteps
        for timestep, data in self.condensed_report.items():
            first_key = next(iter(data))
            
            # Extract MSFL solution phases
            if "solution phases" in data[first_key]:
                for phase in data[first_key]["solution phases"].keys():
                    if phase.startswith("MSFL"):
                        all_msfl_phases.add(phase)
        
        # Sort phases for consistent output
        all_msfl_phases = sorted(all_msfl_phases)
        
        # Create headers for CSV
        headers = ["Timestep"]
        
        # Add MSFL phase headers
        for phase in all_msfl_phases:
            headers.append(f"S:{phase}")
        
        # Second pass: create rows for each timestep
        rows = []
        for timestep, data in self.condensed_report.items():
            first_key = next(iter(data))
            row = {"Timestep": timestep}
            
            # Process MSFL solution phases
            if "solution phases" in data[first_key]:
                solution_phase_data = data[first_key]["solution phases"]
                for phase in all_msfl_phases:
                    if phase in solution_phase_data and "moles" in solution_phase_data[phase]:
                        moles = float(solution_phase_data[phase]["moles"])
                        row[f"S:{phase}"] = moles
                        
                        # Add to significant MSFL phases if applicable
                        if moles > 0.0:
                            self.significant_msfl_phases.add(("solution", phase))
                    else:
                        row[f"S:{phase}"] = 0.0
            
            rows.append(row)
        
        logger.info(f"Generated MSFL mole amounts report with {len(rows)} timesteps and {len(headers) - 1} unique MSFL phases")
        return headers, rows
    
    def extract_phase_compositions(self) -> Dict[str, Dict[str, Dict[int, Dict[str, float]]]]:
        """
        Extracts phase compositions (species and mole percentages) for each MSFL phase at each timestep.
        
        Returns:
            Dict: Nested dictionary with composition data:
                 {phase_type: {phase_name: {timestep: {species: mole_percentage}}}}
        """
        logger.info("Extracting MSFL phase compositions")
        
        # Structure: {phase_type: {phase_name: {timestep: {species: mole_percentage}}}}
        compositions = {
            "solution": {}
        }
        
        # Ensure we have the significant MSFL phases identified
        if not self.significant_msfl_phases:
            # Generate the mole amounts report to populate significant_msfl_phases
            self.generate_phase_mole_amounts_report()
        
        for timestep_str, data in self.condensed_report.items():
            timestep = int(timestep_str)
            first_key = next(iter(data))
            
            # Process solution phases (MSFL only)
            if "solution phases" in data[first_key]:
                solution_phase_data = data[first_key]["solution phases"]
                for phase_name, phase_data in solution_phase_data.items():
                    # Process only MSFL phases
                    if not phase_name.startswith("MSFL"):
                        continue
                    
                    # Skip phases with no moles
                    if "moles" in phase_data and float(phase_data["moles"]) <= 0.0:
                        continue
                    
                    if phase_name not in compositions["solution"]:
                        compositions["solution"][phase_name] = {}
                    
                    if "species" in phase_data:
                        compositions["solution"][phase_name][timestep] = {}
                        for species, species_data in phase_data["species"].items():
                            if "mole fraction" in species_data:
                                mole_percentage = float(species_data["mole fraction"]) * 100
                                compositions["solution"][phase_name][timestep][species] = mole_percentage
        
        logger.info(f"Extracted composition data for {len(compositions['solution'])} MSFL phases")
        return compositions
    
    def save_phase_presence_report(self, output_directory: str, filename: str = "MSFL_Phase_Presence_Report.csv") -> str:
        """
        Save the MSFL phase presence report to a CSV file.
        
        Args:
            output_directory (str): Directory to save the report
            filename (str, optional): Name of the output file. Defaults to "MSFL_Phase_Presence_Report.csv".
            
        Returns:
            str: Path to the saved file
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
            
        headers, rows = self.generate_phase_presence_report()
        output_path = os.path.join(output_directory, filename)
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
            
        logger.info(f"Saved MSFL phase presence report to {output_path}")
        return output_path
    
    def save_phase_mole_amounts_report(self, output_directory: str, filename: str = "MSFL_Phase_Mole_Amounts_Report.csv") -> str:
        """
        Save the MSFL phase mole amounts report to a CSV file.
        
        Args:
            output_directory (str): Directory to save the report
            filename (str, optional): Name of the output file. Defaults to "MSFL_Phase_Mole_Amounts_Report.csv".
            
        Returns:
            str: Path to the saved file
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
            
        headers, rows = self.generate_phase_mole_amounts_report()
        output_path = os.path.join(output_directory, filename)
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
            
        logger.info(f"Saved MSFL phase mole amounts report to {output_path}")
        return output_path
    
    def plot_msfl_mole_amounts(self, output_directory: str, filename: str = "MSFL_Mole_Amounts.png") -> str:
        """
        Create a plot of all MSFL species mole amounts with time.
        
        Args:
            output_directory (str): Directory to save the plot
            filename (str, optional): Name of the output file. Defaults to "MSFL_Mole_Amounts.png".
            
        Returns:
            str: Path to the saved plot
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Get mole amount data
        headers, rows = self.generate_phase_mole_amounts_report()
        
        # Convert to a format suitable for plotting
        phase_data = {}
        for header in headers:
            if header == "Timestep":
                continue
                
            phase_type, phase_name = header.split(":", 1)
            
            # Only include MSFL phases
            if not phase_name.startswith("MSFL"):
                continue
                
            phase_data[header] = []
            
            for row in rows:
                phase_data[header].append(row[header])
        
        # Plot the data
        plt.figure(figsize=(12, 8))
        
        for phase, amounts in phase_data.items():
            # Skip phases with zero moles throughout
            if max(amounts) > 0:
                plt.plot(self.timesteps, amounts, label=phase)
        
        plt.xlabel('Timestep')
        plt.ylabel('Mole Amount')
        plt.title('MSFL Phase Mole Amounts vs Time')
        plt.legend(loc='best', bbox_to_anchor=(1.02, 1), borderaxespad=0)
        plt.grid(True)
        plt.tight_layout()
        
        # Save the plot
        output_path = os.path.join(output_directory, filename)
        plt.savefig(output_path, dpi=300)
        plt.close()
        
        logger.info(f"Saved MSFL mole amounts plot to {output_path}")
        return output_path
    
    def plot_phase_compositions(self, output_directory: str,
                                significance_threshold: float = 0.0000000000000001, 
                                use_direct_labels: bool = True) -> List[str]:
        """
        Create composition vs time plots for each MSFL phase, showing only major components.
        
        Args:
            output_directory (str): Directory to save the plots
            significance_threshold (float): Only include species with percentage > this value at any point
            use_direct_labels (bool): If True, place labels directly on the graph rather than using a legend
            
        Returns:
            List[str]: Paths to the saved plots
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Get composition data
        compositions = self.extract_phase_compositions()
        
        # List to store output paths
        output_paths = []
        
        # Function to create a composition plot for a phase
        def create_composition_plot(phase_name, phase_data, phase_type):
            # Get all species across all timesteps
            all_species = set()
            for ts_data in phase_data.values():
                all_species.update(ts_data.keys())
            
            # Create a data structure for plotting
            plot_data = {species: [] for species in all_species}
            
            # Fill in the data for all timesteps
            for ts in self.timesteps:
                if ts in phase_data:
                    for species in all_species:
                        plot_data[species].append(phase_data[ts].get(species, 0.0))
                else:
                    # If the phase doesn't exist at this timestep, add zeros
                    for species in all_species:
                        plot_data[species].append(0.0)
            
            # Filter to only include significant species
            significant_species = {}
            for species, percentages in plot_data.items():
                if max(percentages) > significance_threshold:
                    significant_species[species] = percentages
            
            # Create the plot
            plt.figure(figsize=(12, 8))
            
            for species, percentages in significant_species.items():
                line, = plt.plot(self.timesteps, percentages)
                
                if use_direct_labels:
                    # Find a good position for the label (at the maximum value point)
                    max_index = percentages.index(max(percentages))
                    x_pos = self.timesteps[max_index]
                    y_pos = percentages[max_index]
                    
                    # Add the label directly on the plot
                    plt.annotate(species, 
                                (x_pos, y_pos),
                                textcoords="offset points",
                                xytext=(0,5), 
                                ha='center',
                                color=line.get_color(),
                                fontweight='bold')
            
            plt.xlabel('Timestep')
            plt.ylabel('Mole Percentage (%)')
            title_suffix = " (Major Components)" if significance_threshold > 0 else ""
            plt.title(f'MSFL Phase Composition vs Time: {phase_name}{title_suffix}')
            
            # No legend when using direct labels
            if not use_direct_labels:
                plt.legend(loc='best', bbox_to_anchor=(1.02, 1), borderaxespad=0)
                
            plt.grid(True)
            plt.tight_layout()
            
            # Save the plot
            safe_phase_name = phase_name.replace('/', '_').replace('\\', '_')
            label_method = "DirectLabels" if use_direct_labels else "Legend"
            output_path = os.path.join(output_directory, f"Composition_{phase_type}_{safe_phase_name}_{label_method}.png")
            plt.savefig(output_path, dpi=300)
            plt.close()
            
            return output_path
        
        # Create plots for MSFL solution phases
        for phase_name, phase_data in compositions["solution"].items():
            if phase_data:  # Check if there's any data for this phase
                output_path = create_composition_plot(phase_name, phase_data, "solution")
                output_paths.append(output_path)
                logger.info(f"Saved composition plot for MSFL phase {phase_name} to {output_path}")
        
        return output_paths
    
    def save_phase_composition_report(self, output_directory: str, filename: str = "MSFL_Phase_Composition_Report.csv") -> str:
        """
        Save a detailed report of MSFL phase compositions at each timestep to a CSV file.
        
        Args:
            output_directory (str): Directory to save the report
            filename (str, optional): Name of the output file. Defaults to "MSFL_Phase_Composition_Report.csv".
            
        Returns:
            str: Path to the saved file
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Get composition data
        compositions = self.extract_phase_compositions()
        
        # Prepare data for CSV
        rows = []
        
        for phase_type in ["solution"]:
            for phase_name, phase_data in compositions[phase_type].items():
                for timestep, species_data in phase_data.items():
                    for species, percentage in species_data.items():
                        rows.append({
                            "Timestep": timestep,
                            "Phase Type": phase_type,
                            "Phase Name": phase_name,
                            "Species": species,
                            "Mole Percentage": percentage
                        })
        
        # Sort rows by timestep, phase type, phase name, and species
        rows.sort(key=lambda x: (x["Timestep"], x["Phase Type"], x["Phase Name"], x["Species"]))
        
        # Write to CSV
        output_path = os.path.join(output_directory, filename)
        headers = ["Timestep", "Phase Type", "Phase Name", "Species", "Mole Percentage"]
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
            
        logger.info(f"Saved MSFL phase composition report to {output_path} ({len(rows)} rows)")
        return output_path


    def extract_cation_compositions(self) -> Dict[str, Dict[int, Dict[str, float]]]:
        """
        Extracts cation compositions (cation names and mole fractions) for each MSFL phase at each timestep.
        
        Returns:
            Dict: Nested dictionary with cation data:
                {phase_name: {timestep: {cation_name: mole_fraction}}}
        """
        logger.info("Extracting MSFL cation compositions")
        
        # Structure: {phase_name: {timestep: {cation_name: mole_fraction}}}
        cation_compositions = {}
        
        for timestep_str, data in self.condensed_report.items():
            timestep = int(timestep_str)
            first_key = next(iter(data))
            
            # Process solution phases (MSFL only)
            if "solution phases" in data[first_key]:
                solution_phase_data = data[first_key]["solution phases"]
                for phase_name, phase_data in solution_phase_data.items():
                    # Process only MSFL phases
                    if not phase_name.startswith("MSFL"):
                        continue
                    
                    # Skip phases with no moles
                    if "moles" in phase_data and float(phase_data["moles"]) <= 0.0:
                        continue
                    
                    if phase_name not in cation_compositions:
                        cation_compositions[phase_name] = {}
                    
                    if "cations" in phase_data:
                        cation_compositions[phase_name][timestep] = {}
                        for cation, cation_data in phase_data["cations"].items():
                            if "mole fraction" in cation_data:
                                mole_fraction = float(cation_data["mole fraction"])
                                cation_compositions[phase_name][timestep][cation] = mole_fraction
        
        logger.info(f"Extracted cation composition data for {len(cation_compositions)} MSFL phases")
        return cation_compositions

    def plot_cation_compositions(self, output_directory: str,
                            significance_threshold: float = 0.01, 
                            use_direct_labels: bool = True) -> List[str]:
        """
        Create cation composition vs time plots for each MSFL phase, showing only major cations.
        
        Args:
            output_directory (str): Directory to save the plots
            significance_threshold (float): Only include cations with fraction > this value at any point
            use_direct_labels (bool): If True, place labels directly on the graph rather than using a legend
            
        Returns:
            List[str]: Paths to the saved plots
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Get cation composition data
        cation_compositions = self.extract_cation_compositions()
        
        # List to store output paths
        output_paths = []
        
        # Function to create a cation composition plot for a phase
        def create_cation_plot(phase_name, phase_data):
            # Get all cations across all timesteps
            all_cations = set()
            for ts_data in phase_data.values():
                all_cations.update(ts_data.keys())
            
            # Create a data structure for plotting
            plot_data = {cation: [] for cation in all_cations}
            
            # Convert timesteps to integers for proper sorting
            timesteps = sorted([int(ts) for ts in phase_data.keys()])
            
            # Fill in the data for all timesteps
            for ts in timesteps:
                for cation in all_cations:
                    if ts in phase_data and cation in phase_data[ts]:
                        plot_data[cation].append(phase_data[ts][cation] * 100)  # Convert to percentage
                    else:
                        # If the cation doesn't exist at this timestep, add zero
                        plot_data[cation].append(0.0)
            
            # Filter to only include significant cations
            significant_cations = {}
            for cation, percentages in plot_data.items():
                if max(percentages) > significance_threshold * 100:  # Compare with percentage threshold
                    significant_cations[cation] = percentages
            
            # Create the plot
            plt.figure(figsize=(12, 8))
            
            for cation, percentages in significant_cations.items():
                line, = plt.plot(timesteps, percentages)
                
                if use_direct_labels:
                    # Find a good position for the label (at the maximum value point)
                    max_index = percentages.index(max(percentages))
                    x_pos = timesteps[max_index]
                    y_pos = percentages[max_index]
                    
                    # Add the label directly on the plot
                    plt.annotate(cation, 
                                (x_pos, y_pos),
                                textcoords="offset points",
                                xytext=(0,5), 
                                ha='center',
                                color=line.get_color(),
                                fontweight='bold')
            
            plt.xlabel('Timestep')
            plt.ylabel('Cation Mole Percentage (%)')
            title_suffix = " (Major Cations)" if significance_threshold > 0 else ""
            plt.title(f'MSFL Cation Composition vs Time: {phase_name}{title_suffix}')
            
            # No legend when using direct labels
            if not use_direct_labels:
                plt.legend(loc='best', bbox_to_anchor=(1.02, 1), borderaxespad=0)
                
            plt.grid(True)
            plt.tight_layout()
            
            # Save the plot
            safe_phase_name = phase_name.replace('/', '_').replace('\\', '_')
            label_method = "DirectLabels" if use_direct_labels else "Legend"
            output_path = os.path.join(output_directory, f"Cation_Composition_{safe_phase_name}_{label_method}.png")
            plt.savefig(output_path, dpi=300)
            plt.close()
            
            return output_path
        
        # Create plots for each MSFL phase
        for phase_name, phase_data in cation_compositions.items():
            if phase_data:  # Check if there's any data for this phase
                output_path = create_cation_plot(phase_name, phase_data)
                output_paths.append(output_path)
                logger.info(f"Saved cation composition plot for MSFL phase {phase_name} to {output_path}")
        
        return output_paths

    def save_cation_composition_report(self, output_directory: str, filename: str = "MSFL_Cation_Composition_Report.csv") -> str:
        """
        Save a detailed report of MSFL cation compositions at each timestep to a CSV file.
        
        Args:
            output_directory (str): Directory to save the report
            filename (str, optional): Name of the output file. Defaults to "MSFL_Cation_Composition_Report.csv".
            
        Returns:
            str: Path to the saved file
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Get cation composition data
        cation_compositions = self.extract_cation_compositions()
        
        # Prepare data for CSV
        rows = []
        
        for phase_name, phase_data in cation_compositions.items():
            for timestep, cation_data in phase_data.items():
                for cation, mole_fraction in cation_data.items():
                    rows.append({
                        "Timestep": timestep,
                        "Phase Name": phase_name,
                        "Cation": cation,
                        "Mole Fraction": mole_fraction,
                        "Mole Percentage": mole_fraction * 100
                    })
        
        # Sort rows by timestep, phase name, and cation
        rows.sort(key=lambda x: (x["Timestep"], x["Phase Name"], x["Cation"]))
        
        # Write to CSV
        output_path = os.path.join(output_directory, filename)
        headers = ["Timestep", "Phase Name", "Cation", "Mole Fraction", "Mole Percentage"]
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
            
        logger.info(f"Saved MSFL cation composition report to {output_path} ({len(rows)} rows)")
        return output_path

    def plot_cation_compositions_log_scale(self, output_directory: str, use_direct_labels: bool = True) -> List[str]:
        """
        Create cation composition vs time plots for each MSFL phase on a semi-logarithmic scale,
        showing ALL cations without filtering by significance.
        
        Args:
            output_directory (str): Directory to save the plots
            use_direct_labels (bool): If True, place labels directly on the graph rather than using a legend
            
        Returns:
            List[str]: Paths to the saved plots
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Get cation composition data
        cation_compositions = self.extract_cation_compositions()
        
        # List to store output paths
        output_paths = []
        
        # Function to create a cation composition plot for a phase on log scale
        def create_cation_log_plot(phase_name, phase_data):
            # Get all cations across all timesteps
            all_cations = set()
            for ts_data in phase_data.values():
                all_cations.update(ts_data.keys())
            
            # Convert to sorted list for consistent coloring
            all_cations = sorted(list(all_cations))
            
            # Create a data structure for plotting
            plot_data = {cation: [] for cation in all_cations}
            
            # Convert timesteps to integers for proper sorting
            timesteps = sorted([int(ts) for ts in phase_data.keys()])
            
            # Fill in the data for all timesteps
            for ts in timesteps:
                for cation in all_cations:
                    if ts in phase_data and cation in phase_data[ts]:
                        # Convert to percentage
                        value = phase_data[ts][cation] * 100
                        # Ensure no zero values for log scale (use a small value instead)
                        plot_data[cation].append(max(value, 1e-10))
                    else:
                        # If the cation doesn't exist at this timestep, add a small value
                        plot_data[cation].append(1e-10)
            
            # Create the plot with a semi-logarithmic scale
            plt.figure(figsize=(14, 10))
            
            # Generate a colormap with enough distinct colors
            colors = plt.cm.get_cmap('tab20', len(all_cations))
            
            for i, cation in enumerate(all_cations):
                percentages = plot_data[cation]
                color = colors(i % 20)  # Cycle through colors if more than 20 cations
                line, = plt.semilogy(timesteps, percentages, label=cation, color=color)
                
                if use_direct_labels:
                    # Find a good position for the label
                    # Use the last timestep value for labels to avoid overcrowding
                    x_pos = timesteps[-1]
                    y_pos = percentages[-1]
                    
                    # Only label if the final value is above a certain threshold to avoid clutter
                    if y_pos > 1e-8:
                        plt.annotate(cation, 
                                    (x_pos, y_pos),
                                    textcoords="offset points",
                                    xytext=(5, 0), 
                                    ha='left',
                                    va='center',
                                    color=color,
                                    fontweight='bold',
                                    fontsize=8)
            
            plt.xlabel('Timestep')
            plt.ylabel('Cation Mole Percentage (%)')
            plt.title(f'MSFL Cation Composition vs Time (Log Scale): {phase_name}')
            
            # Add a legend if not using direct labels
            if not use_direct_labels:
                plt.legend(loc='best', bbox_to_anchor=(1.02, 1), borderaxespad=0)
            
            # Add a grid for better readability on log scale
            plt.grid(True, which="both", ls="-", alpha=0.2)
            
            # Set y-axis limits to ensure good visibility of both large and small values
            plt.ylim(bottom=1e-8, top=110)
            
            plt.tight_layout()
            
            # Save the plot
            safe_phase_name = phase_name.replace('/', '_').replace('\\', '_')
            label_method = "DirectLabels" if use_direct_labels else "Legend"
            output_path = os.path.join(output_directory, f"Cation_Composition_LogScale_{safe_phase_name}_{label_method}.png")
            plt.savefig(output_path, dpi=300)
            plt.close()
            
            return output_path
        
        # Create plots for each MSFL phase
        for phase_name, phase_data in cation_compositions.items():
            if phase_data:  # Check if there's any data for this phase
                output_path = create_cation_log_plot(phase_name, phase_data)
                output_paths.append(output_path)
                logger.info(f"Saved log-scale cation composition plot for MSFL phase {phase_name} to {output_path}")
        
        return output_paths

    def generate_all_reports_and_plots(self, output_directory: str) -> Dict[str, List[str]]:
        """
        Generate all MSFL reports and plots and save them to the specified directory.
        
        Args:
            output_directory (str): Directory to save all outputs
            
        Returns:
            Dict[str, List[str]]: Dictionary with keys 'reports' and 'plots', containing lists of file paths
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        reports = []
        plots = []
        
        # Generate reports
        reports.append(self.save_phase_presence_report(output_directory))
        reports.append(self.save_phase_mole_amounts_report(output_directory))
        
        # Generate the MSFL mole amounts plot
        msfl_plot = self.plot_msfl_mole_amounts(output_directory)
        plots.append(msfl_plot)
        
        # Generate phase composition report for MSFL phases
        reports.append(self.save_phase_composition_report(output_directory))
        
        # Generate composition plots for MSFL phases with the specified parameters
        plots.extend(self.plot_phase_compositions(output_directory, significance_threshold=1.0, use_direct_labels=True))
        
        # Generate cation composition report and plots
        reports.append(self.save_cation_composition_report(output_directory))
        
        # Generate regular cation composition plots (filtered to show only major components)
        plots.extend(self.plot_cation_compositions(output_directory, significance_threshold=0.01, use_direct_labels=True))
        
        # Generate log-scale cation composition plots (showing all components)
        plots.extend(self.plot_cation_compositions_log_scale(output_directory, use_direct_labels=True))
        
        return {
            "reports": reports,
            "plots": plots
        }

def main():
    """
    Main function to demonstrate usage of the MSFLPhaseAnalysisReportGenerator
    with the existing CondensedReportGenerator.
    """
    import argparse
    from CondensedReportGenerator2 import CondensedReportGenerator
    from Data_Load_and_Parse import DataLoaderParser
    
    parser = argparse.ArgumentParser(description='MSFL Phase Analysis Report Generator')
    parser.add_argument('input_dir', help='Directory containing input files')
    parser.add_argument('--output-dir', default='msfl_output', help='Directory to save output files')
    args = parser.parse_args()
    
    # Load the data using DataLoaderParser from Component 1
    loader = DataLoaderParser(args.input_dir)
    _, _, thermochimica_data = loader.load_all_data()
    
    # Create an instance of the CondensedReportGenerator and generate the condensed report
    report_generator = CondensedReportGenerator(thermochimica_data)
    condensed_report = report_generator.generate_condensed_report()
    
    # Create an instance of the MSFLPhaseAnalysisReportGenerator
    msfl_report_generator = MSFLPhaseAnalysisReportGenerator(condensed_report)
    
    # Generate all reports and plots
    outputs = msfl_report_generator.generate_all_reports_and_plots(args.output_dir)
    
    logger.info(f"Generated {len(outputs['reports'])} reports and {len(outputs['plots'])} plots")
    logger.info(f"Reports: {', '.join(outputs['reports'])}")
    logger.info(f"Plots: {', '.join(outputs['plots'])}")


if __name__ == "__main__":
    main()