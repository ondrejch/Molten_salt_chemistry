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
logger = logging.getLogger('Phase-Analysis-Report')

class PhaseAnalysisReportGenerator:
    """
    Generates reports and plots for phase presence, mole amounts, and composition over time.
    
    Works alongside the CondensedReportGenerator to analyze the condensed report data.
    """
    
    def __init__(self, condensed_report: OrderedDict):
        """
        Initialize the Phase Analysis Report Generator.
        
        Args:
            condensed_report (OrderedDict): Condensed report from CondensedReportGenerator
        """
        self.condensed_report = condensed_report
        self.timesteps = sorted([int(ts) for ts in self.condensed_report.keys()])
        self.str_timesteps = [str(ts) for ts in self.timesteps]
        # Track non-salt phases with moles > 0 for reporting
        self.significant_non_salt_phases = set()
        
    def generate_phase_presence_report(self) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Analyzes the condensed report and creates a report of which phases 
        have moles > 0.0 at each timestep.
        
        Returns:
            Tuple[List[str], List[Dict[str, Any]]]: Headers and rows for the CSV report
        """
        logger.info("Generating phase presence report")
        
        # Collect all unique phases across all timesteps
        all_solution_phases = set()
        all_pure_phases = set()
        
        # First pass: identify all phases across all timesteps
        for timestep, data in self.condensed_report.items():
            first_key = next(iter(data))
            
            # Extract solution phases
            if "solution phases" in data[first_key]:
                for phase, phase_data in data[first_key]["solution phases"].items():
                    if "moles" in phase_data and float(phase_data["moles"]) > 0.0:
                        all_solution_phases.add(phase)
            
            # Extract pure condensed phases
            if "pure condensed phases" in data[first_key]:
                for phase, phase_data in data[first_key]["pure condensed phases"].items():
                    if "moles" in phase_data and float(phase_data["moles"]) > 0.0:
                        all_pure_phases.add(phase)
        
        # Sort phases for consistent output
        all_solution_phases = sorted(all_solution_phases)
        all_pure_phases = sorted(all_pure_phases)
        
        # Create headers for CSV
        headers = ["Timestep", "# solution phases", "# pure condensed phases"]
        
        # Add solution phase headers
        for phase in all_solution_phases:
            headers.append(f"S:{phase}")
        
        # Add pure phase headers
        for phase in all_pure_phases:
            headers.append(f"P:{phase}")
        
        # Second pass: create rows for each timestep
        rows = []
        for timestep, data in self.condensed_report.items():
            first_key = next(iter(data))
            row = defaultdict(int)  # Default to 0 for phases not present
            
            # Add basic timestep info
            row["Timestep"] = timestep
            
            # Count phases and track presence
            solution_phases_count = 0
            pure_phases_count = 0
            
            # Process solution phases
            if "solution phases" in data[first_key]:
                solution_phase_data = data[first_key]["solution phases"]
                # Count phases with moles > 0
                for phase, phase_data in solution_phase_data.items():
                    if "moles" in phase_data and float(phase_data["moles"]) > 0.0:
                        row[f"S:{phase}"] = 1
                        solution_phases_count += 1
            
            # Process pure condensed phases
            if "pure condensed phases" in data[first_key]:
                pure_phase_data = data[first_key]["pure condensed phases"]
                # Count phases with moles > 0
                for phase, phase_data in pure_phase_data.items():
                    if "moles" in phase_data and float(phase_data["moles"]) > 0.0:
                        row[f"P:{phase}"] = 1
                        pure_phases_count += 1
            
            # Add phase counts
            row["# solution phases"] = solution_phases_count
            row["# pure condensed phases"] = pure_phases_count
            
            rows.append(dict(row))
        
        logger.info(f"Generated report with {len(rows)} timesteps and {len(headers) - 3} unique phases")
        return headers, rows
    
    def generate_phase_mole_amounts_report(self) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Analyzes the condensed report and creates a report of mole amounts for each phase at each timestep.
        
        Returns:
            Tuple[List[str], List[Dict[str, Any]]]: Headers and rows for the CSV report
        """
        logger.info("Generating phase mole amounts report")
        
        # Collect all unique phases across all timesteps
        all_solution_phases = set()
        all_pure_phases = set()
        
        # First pass: identify all phases across all timesteps
        for timestep, data in self.condensed_report.items():
            first_key = next(iter(data))
            
            # Extract solution phases
            if "solution phases" in data[first_key]:
                for phase in data[first_key]["solution phases"].keys():
                    all_solution_phases.add(phase)
            
            # Extract pure condensed phases
            if "pure condensed phases" in data[first_key]:
                for phase in data[first_key]["pure condensed phases"].keys():
                    all_pure_phases.add(phase)
        
        # Sort phases for consistent output
        all_solution_phases = sorted(all_solution_phases)
        all_pure_phases = sorted(all_pure_phases)
        
        # Create headers for CSV
        headers = ["Timestep"]
        
        # Add solution phase headers
        for phase in all_solution_phases:
            headers.append(f"S:{phase}")
        
        # Add pure phase headers
        for phase in all_pure_phases:
            headers.append(f"P:{phase}")
        
        # Second pass: create rows for each timestep
        rows = []
        for timestep, data in self.condensed_report.items():
            first_key = next(iter(data))
            row = {"Timestep": timestep}
            
            # Process solution phases
            if "solution phases" in data[first_key]:
                solution_phase_data = data[first_key]["solution phases"]
                for phase in all_solution_phases:
                    if phase in solution_phase_data and "moles" in solution_phase_data[phase]:
                        moles = float(solution_phase_data[phase]["moles"])
                        row[f"S:{phase}"] = moles
                        
                        # Add to significant non-salt phases if applicable
                        if moles > 0.0 and not phase.startswith("MSFL"):
                            self.significant_non_salt_phases.add(("solution", phase))
                    else:
                        row[f"S:{phase}"] = 0.0
            
            # Process pure condensed phases
            if "pure condensed phases" in data[first_key]:
                pure_phase_data = data[first_key]["pure condensed phases"]
                for phase in all_pure_phases:
                    if phase in pure_phase_data and "moles" in pure_phase_data[phase]:
                        moles = float(pure_phase_data[phase]["moles"])
                        row[f"P:{phase}"] = moles
                        
                        # Add to significant non-salt phases if applicable
                        if moles > 0.0:
                            self.significant_non_salt_phases.add(("pure", phase))
                    else:
                        row[f"P:{phase}"] = 0.0
            
            rows.append(row)
        
        logger.info(f"Generated mole amounts report with {len(rows)} timesteps and {len(headers) - 1} unique phases")
        return headers, rows
    
    def extract_phase_compositions(self, non_salt_only: bool = False) -> Dict[str, Dict[str, Dict[int, Dict[str, float]]]]:
        """
        Extracts phase compositions (species and mole percentages) for each phase at each timestep.
        
        Args:
            non_salt_only (bool): If True, extract only non-salt phases that have moles > 0
        
        Returns:
            Dict: Nested dictionary with composition data:
                 {phase_type: {phase_name: {timestep: {species: mole_percentage}}}}
        """
        logger.info(f"Extracting phase compositions ({'non-salt only' if non_salt_only else 'all phases'})")
        
        # Structure: {phase_type: {phase_name: {timestep: {species: mole_percentage}}}}
        compositions = {
            "solution": {},
            "pure": {}
        }
        
        # Ensure we have the significant non-salt phases identified
        if non_salt_only and not self.significant_non_salt_phases:
            # Generate the mole amounts report to populate significant_non_salt_phases
            self.generate_phase_mole_amounts_report()
        
        for timestep_str, data in self.condensed_report.items():
            timestep = int(timestep_str)
            first_key = next(iter(data))
            
            # Process solution phases
            if "solution phases" in data[first_key]:
                solution_phase_data = data[first_key]["solution phases"]
                for phase_name, phase_data in solution_phase_data.items():
                    # Skip salt phases (MSFL) if non_salt_only is True
                    if non_salt_only:
                        if ("solution", phase_name) not in self.significant_non_salt_phases:
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
            
            # Process pure condensed phases
            if "pure condensed phases" in data[first_key]:
                pure_phase_data = data[first_key]["pure condensed phases"]
                for phase_name, phase_data in pure_phase_data.items():
                    # Skip phases if non_salt_only is True and they're not in significant_non_salt_phases
                    if non_salt_only:
                        if ("pure", phase_name) not in self.significant_non_salt_phases:
                            continue
                    
                    # Skip phases with no moles
                    if "moles" in phase_data and float(phase_data["moles"]) <= 0.0:
                        continue
                    
                    if phase_name not in compositions["pure"]:
                        compositions["pure"][phase_name] = {}
                    
                    # Pure phases are 100% of themselves
                    compositions["pure"][phase_name][timestep] = {phase_name: 100.0}
        
        logger.info(f"Extracted composition data for {len(compositions['solution'])} solution phases and {len(compositions['pure'])} pure phases")
        return compositions
    
    def save_phase_presence_report(self, output_directory: str, filename: str = "Phase_Presence_Report.csv") -> str:
        """
        Save the phase presence report to a CSV file.
        
        Args:
            output_directory (str): Directory to save the report
            filename (str, optional): Name of the output file. Defaults to "Phase_Presence_Report.csv".
            
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
            
        logger.info(f"Saved phase presence report to {output_path}")
        return output_path
    
    def save_phase_mole_amounts_report(self, output_directory: str, filename: str = "Phase_Mole_Amounts_Report.csv") -> str:
        """
        Save the phase mole amounts report to a CSV file.
        
        Args:
            output_directory (str): Directory to save the report
            filename (str, optional): Name of the output file. Defaults to "Phase_Mole_Amounts_Report.csv".
            
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
            
        logger.info(f"Saved phase mole amounts report to {output_path}")
        return output_path
    
    def plot_non_salt_mole_amounts(self, output_directory: str, filename: str = "Non_Salt_Mole_Amounts.png") -> str:
        """
        Create a plot of all non-salt (non-MSFL) species mole amounts with time.
        
        Args:
            output_directory (str): Directory to save the plot
            filename (str, optional): Name of the output file. Defaults to "Non_Salt_Mole_Amounts.png".
            
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
            
            # Skip salt phases
            if phase_name.startswith("MSFL"):
                continue
                
            phase_data[header] = []
            
            for row in rows:
                phase_data[header].append(row[header])
        
        # Plot the data
        plt.figure(figsize=(12, 8))
        
        for phase, amounts in phase_data.items():
            # Skip phases with zero moles

    # Skip phases with zero moles throughout
            if max(amounts) > 0:
                plt.plot(self.timesteps, amounts, label=phase)
        
        plt.xlabel('Timestep')
        plt.ylabel('Mole Amount')
        plt.title('Non-Salt Phase Mole Amounts vs Time')
        plt.legend(loc='best', bbox_to_anchor=(1.02, 1), borderaxespad=0)
        plt.grid(True)
        plt.tight_layout()
        
        # Save the plot
        output_path = os.path.join(output_directory, filename)
        plt.savefig(output_path, dpi=300)
        plt.close()
        
        logger.info(f"Saved non-salt mole amounts plot to {output_path}")
        return output_path
    
    def plot_phase_compositions(self, output_directory: str, non_salt_only: bool = False,
                        significance_threshold: float = 0.0000000000000001, use_direct_labels: bool = True) -> List[str]:
        """
        Create composition vs time plots for each phase, showing only major components.
        
        Args:
            output_directory (str): Directory to save the plots
            non_salt_only (bool): If True, only create plots for non-salt phases with moles > 0
            significance_threshold (float): Only include species with percentage > this value at any point
            use_direct_labels (bool): If True, place labels directly on the graph rather than using a legend
            
        Returns:
            List[str]: Paths to the saved plots
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Get composition data
        compositions = self.extract_phase_compositions(non_salt_only=non_salt_only)
        
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
            plt.title(f'{phase_type.capitalize()} Phase Composition vs Time: {phase_name}{title_suffix}')
            
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
        
        # Create plots for solution phases
        for phase_name, phase_data in compositions["solution"].items():
            if phase_data:  # Check if there's any data for this phase
                output_path = create_composition_plot(phase_name, phase_data, "solution")
                output_paths.append(output_path)
                logger.info(f"Saved composition plot for solution phase {phase_name} to {output_path}")
        
        # Create plots for pure phases
        for phase_name, phase_data in compositions["pure"].items():
            if phase_data:  # Check if there's any data for this phase
                output_path = create_composition_plot(phase_name, phase_data, "pure")
                output_paths.append(output_path)
                logger.info(f"Saved composition plot for pure phase {phase_name} to {output_path}")
        
        return output_paths
    
    def save_phase_composition_report(self, output_directory: str, filename: str = "Phase_Composition_Report.csv", non_salt_only: bool = True) -> str:
        """
        Save a detailed report of phase compositions at each timestep to a CSV file.
        
        Args:
            output_directory (str): Directory to save the report
            filename (str, optional): Name of the output file. Defaults to "Phase_Composition_Report.csv".
            non_salt_only (bool): If True, only include non-salt phases with moles > 0
            
        Returns:
            str: Path to the saved file
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Get composition data
        compositions = self.extract_phase_compositions(non_salt_only=non_salt_only)
        
        # Prepare data for CSV
        rows = []
        
        for phase_type in ["solution", "pure"]:
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
            
        logger.info(f"Saved phase composition report to {output_path} ({len(rows)} rows, {'non-salt only' if non_salt_only else 'all phases'})")
        return output_path
    
    def generate_all_reports_and_plots(self, output_directory: str) -> Dict[str, List[str]]:
        """
        Generate all reports and plots and save them to the specified directory.
        
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
        
        # Generate the non-salt mole amounts plot
        non_salt_plot = self.plot_non_salt_mole_amounts(output_directory)
        plots.append(non_salt_plot)
        
        # Generate phase composition report ONLY for non-salt phases
        reports.append(self.save_phase_composition_report(output_directory, non_salt_only=True))
        
        # Generate composition plots for all phases (including MSFL) with the new parameters
        plots.extend(self.plot_phase_compositions(output_directory, non_salt_only=False, significance_threshold=1.0, use_direct_labels=True))
        

        
        return {
            "reports": reports,
            "plots": plots
        }



def main():
    """
    Main function to demonstrate usage of the PhaseAnalysisReportGenerator
    with the existing CondensedReportGenerator.
    """
    import argparse
    from CondensedReportGenerator2 import CondensedReportGenerator
    from Data_Load_and_Parse import DataLoaderParser
    
    parser = argparse.ArgumentParser(description='Phase Analysis Report Generator')
    parser.add_argument('input_dir', help='Directory containing input files')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
    parser.add_argument('--non-salt-only', action='store_true', help='Generate composition reports for non-salt phases only')
    args = parser.parse_args()
    
    # Load the data using DataLoaderParser from Component 1
    loader = DataLoaderParser(args.input_dir)
    _, _, thermochimica_data = loader.load_all_data()
    
    # Create an instance of the CondensedReportGenerator and generate the condensed report
    report_generator = CondensedReportGenerator(thermochimica_data)
    condensed_report = report_generator.generate_condensed_report()
    
    # Create an instance of the PhaseAnalysisReportGenerator
    phase_report_generator = PhaseAnalysisReportGenerator(condensed_report)
    
    # Generate all reports and plots
    outputs = phase_report_generator.generate_all_reports_and_plots(args.output_dir)
    
    logger.info(f"Generated {len(outputs['reports'])} reports and {len(outputs['plots'])} plots")
    logger.info(f"Reports: {', '.join(outputs['reports'])}")
    logger.info(f"Plots: {', '.join(outputs['plots'])}")


if __name__ == "__main__":
    main()