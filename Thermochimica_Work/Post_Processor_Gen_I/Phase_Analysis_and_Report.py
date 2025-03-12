import os
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Set, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Phase-Analysis-Reporter')

class PhaseAnalysisReporter:
    """
    Component 4: Phase Analysis and Reporting
    Generate phase-specific analysis and visualization.
    
    Main functions:
    - extract_phase_data: Extracts data for a specific phase type
    - calculate_phase_mole_percentages: Calculates mole percentages for each phase
    - generate_phase_plot_all: Creates semilog plot for all phases
    - generate_phase_plot_summary: Creates summary plot for different phase types
    """
    
    def __init__(self, condensed_report: Dict[str, Dict[str, Any]]):
        """
        Initialize the Phase Analysis Reporter.
        
        Args:
            condensed_report (Dict[str, Dict[str, Any]]): Condensed Thermochimica report from Component 2
        """
        self.condensed_report = condensed_report
        self.timesteps = sorted([int(ts) for ts in condensed_report.keys()])
        
    def extract_phase_data(self, phase_type: str) -> Dict[str, Dict[int, float]]:
        """
        Extract data for a specific phase type (salt, gas, solid) across all timesteps.
        
        Args:
            phase_type (str): Type of phase to extract (salt, gas, or solid)
            
        Returns:
            Dict[str, Dict[int, float]]: Dictionary mapping phase names to their mole amounts per timestep
        """
        logger.info(f"Extracting {phase_type} phase data")
        
        phase_data = {}
        
        for timestep_str, timestep_data in self.condensed_report.items():
            timestep = int(timestep_str)
            
            for phase_name, phase_info in timestep_data.items():
                # Skip phases that don't match the requested type
                if phase_info.get("classification") != phase_type:
                    continue
                
                # Initialize phase in phase_data if not already present
                if phase_name not in phase_data:
                    phase_data[phase_name] = {}
                
                # Extract moles based on phase type
                if phase_info.get("type") == "solution":
                    # For solution phases, calculate total moles from species mole fractions
                    # Note: This requires an assumption about total moles, which we might need to revisit
                    species_data = phase_info.get("species", {})
                    # Assuming mole fractions sum to 1 for a solution phase
                    total_species_moles = sum(species.get("mole_fraction", 0) for species in species_data.values())
                    phase_data[phase_name][timestep] = total_species_moles
                elif phase_info.get("type") == "pure":
                    # For pure phases, use the moles value directly
                    phase_data[phase_name][timestep] = phase_info.get("moles", 0)
        
        return phase_data
    
    def calculate_phase_mole_percentages(self) -> Dict[str, Dict[int, float]]:
        """
        Calculate mole percentages for each phase across all timesteps.
        
        Returns:
            Dict[str, Dict[int, float]]: Dictionary mapping phase names to their mole percentages per timestep
        """
        logger.info("Calculating phase mole percentages")
        
        # Extract data for all phase types
        salt_data = self.extract_phase_data("salt")
        gas_data = self.extract_phase_data("gas")
        solid_data = self.extract_phase_data("solid")
        
        # Combine all phase data
        all_phases_data = {**salt_data, **gas_data, **solid_data}
        
        # Calculate total moles for each timestep
        total_moles_per_timestep = {}
        for phase_name, timestep_moles in all_phases_data.items():
            for timestep, moles in timestep_moles.items():
                if timestep not in total_moles_per_timestep:
                    total_moles_per_timestep[timestep] = 0
                total_moles_per_timestep[timestep] += moles
        
        # Calculate mole percentages
        phase_percentages = {}
        for phase_name, timestep_moles in all_phases_data.items():
            phase_percentages[phase_name] = {}
            for timestep, moles in timestep_moles.items():
                total_moles = total_moles_per_timestep.get(timestep, 0)
                if total_moles > 0:
                    percentage = (moles / total_moles) * 100
                else:
                    percentage = 0
                phase_percentages[phase_name][timestep] = percentage
        
        return phase_percentages
    
    def generate_phase_plot_all(self, output_directory: str, filename: str = "Phase_Plot_All.png") -> str:
        """
        Create a semilog plot showing all phases across all timesteps.
        
        Args:
            output_directory (str): Directory to save the plot
            filename (str, optional): Name of the output file. Defaults to "Phase_Plot_All.png".
            
        Returns:
            str: Path to the saved plot file
        """
        logger.info("Generating all phases plot")
        
        # Calculate phase percentages
        phase_percentages = self.calculate_phase_mole_percentages()
        
        # Create the plot
        plt.figure(figsize=(12, 8))
        plt.yscale('log')
        
        # Define colors and markers for different phase types
        colors = {
            "salt": ["#ff0000", "#ff3333", "#ff6666", "#ff9999"],  # Reds
            "gas": ["#0000ff", "#3333ff", "#6666ff", "#9999ff"],   # Blues
            "solid": ["#00ff00", "#33ff33", "#66ff66", "#99ff99"]  # Greens
        }
        markers = {
            "salt": ["o", "s", "^", "d"],
            "gas": ["p", "*", "h", "8"],
            "solid": ["x", "+", ".", "1"]
        }
        
        # Track used colors and markers for each phase type
        used_colors = {"salt": 0, "gas": 0, "solid": 0}
        used_markers = {"salt": 0, "gas": 0, "solid": 0}
        
        # Plot each phase
        for phase_name, timestep_percentages in phase_percentages.items():
            # Get phase classification from the first timestep data
            phase_classification = None
            for timestep_str, timestep_data in self.condensed_report.items():
                if phase_name in timestep_data:
                    phase_classification = timestep_data[phase_name].get("classification")
                    break
            
            if phase_classification not in ["salt", "gas", "solid"]:
                phase_classification = "solid"  # Default to solid if classification is unknown
            
            # Get color and marker for this phase
            color_idx = used_colors[phase_classification] % len(colors[phase_classification])
            marker_idx = used_markers[phase_classification] % len(markers[phase_classification])
            color = colors[phase_classification][color_idx]
            marker = markers[phase_classification][marker_idx]
            
            # Update used colors and markers
            used_colors[phase_classification] += 1
            used_markers[phase_classification] += 1
            
            # Prepare x and y data for plotting
            x = sorted(timestep_percentages.keys())
            y = [timestep_percentages[ts] for ts in x]
            
            # Plot the data
            plt.plot(x, y, label=phase_name, color=color, marker=marker, markersize=5, linewidth=1.5)
        
        # Set plot labels and title
        plt.xlabel('Timestep')
        plt.ylabel('Mole Percentage (%)')
        plt.title('Phase Distribution over Time (All Phases)')
        plt.grid(True, which="both", ls="-", alpha=0.2)
        
        # Add legend outside the plot
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
        
        # Ensure the output directory exists
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Save the plot
        output_path = os.path.join(output_directory, filename)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        
        logger.info(f"Saved all phases plot to {output_path}")
        return output_path
    
    def generate_phase_plot_summary(self, output_directory: str, filename: str = "Phase_Plot_Summary.png") -> str:
        """
        Create a summary plot showing total mole percentages for each phase type (salt, gas, solid).
        
        Args:
            output_directory (str): Directory to save the plot
            filename (str, optional): Name of the output file. Defaults to "Phase_Plot_Summary.png".
            
        Returns:
            str: Path to the saved plot file
        """
        logger.info("Generating phase summary plot")
        
        # Extract data for each phase type
        salt_data = self.extract_phase_data("salt")
        gas_data = self.extract_phase_data("gas")
        solid_data = self.extract_phase_data("solid")
        
        # Calculate total moles per timestep for each phase type
        salt_total = {}
        gas_total = {}
        solid_total = {}
        total_moles = {}
        
        # Calculate totals for each phase type
        for phase_name, timestep_moles in salt_data.items():
            for timestep, moles in timestep_moles.items():
                if timestep not in salt_total:
                    salt_total[timestep] = 0
                salt_total[timestep] += moles
                
                if timestep not in total_moles:
                    total_moles[timestep] = 0
                total_moles[timestep] += moles
        
        for phase_name, timestep_moles in gas_data.items():
            for timestep, moles in timestep_moles.items():
                if timestep not in gas_total:
                    gas_total[timestep] = 0
                gas_total[timestep] += moles
                
                if timestep not in total_moles:
                    total_moles[timestep] = 0
                total_moles[timestep] += moles
        
        for phase_name, timestep_moles in solid_data.items():
            for timestep, moles in timestep_moles.items():
                if timestep not in solid_total:
                    solid_total[timestep] = 0
                solid_total[timestep] += moles
                
                if timestep not in total_moles:
                    total_moles[timestep] = 0
                total_moles[timestep] += moles
        
        # Calculate percentages
        salt_percentage = {}
        gas_percentage = {}
        solid_percentage = {}
        
        for timestep in total_moles.keys():
            if total_moles[timestep] > 0:
                salt_percentage[timestep] = (salt_total.get(timestep, 0) / total_moles[timestep]) * 100
                gas_percentage[timestep] = (gas_total.get(timestep, 0) / total_moles[timestep]) * 100
                solid_percentage[timestep] = (solid_total.get(timestep, 0) / total_moles[timestep]) * 100
        
        # Create the plot
        plt.figure(figsize=(12, 8))
        
        # Prepare x and y data for plotting
        timesteps = sorted(total_moles.keys())
        salt_y = [salt_percentage.get(ts, 0) for ts in timesteps]
        gas_y = [gas_percentage.get(ts, 0) for ts in timesteps]
        solid_y = [solid_percentage.get(ts, 0) for ts in timesteps]
        
        # Plot the data
        plt.plot(timesteps, salt_y, label='Salt Phases', color='#ff0000', marker='o', markersize=5, linewidth=2)
        plt.plot(timesteps, gas_y, label='Gas Phases', color='#0000ff', marker='s', markersize=5, linewidth=2)
        plt.plot(timesteps, solid_y, label='Solid Phases', color='#00ff00', marker='^', markersize=5, linewidth=2)
        
        # Set plot labels and title
        plt.xlabel('Timestep')
        plt.ylabel('Total Mole Percentage (%)')
        plt.title('Phase Type Distribution over Time')
        plt.grid(True, which="both", ls="-", alpha=0.2)
        
        # Add legend
        plt.legend()
        
        # Ensure the output directory exists
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Save the plot
        output_path = os.path.join(output_directory, filename)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        
        logger.info(f"Saved phase summary plot to {output_path}")
        return output_path
    
    def save_phase_data_csv(self, output_directory: str, filename: str = "Phase_Data.csv") -> str:
        """
        Save the phase mole percentages to a CSV file.
        
        Args:
            output_directory (str): Directory to save the CSV file
            filename (str, optional): Name of the output file. Defaults to "Phase_Data.csv".
            
        Returns:
            str: Path to the saved CSV file
        """
        logger.info("Saving phase data to CSV")
        
        # Calculate phase percentages
        phase_percentages = self.calculate_phase_mole_percentages()
        
        # Ensure the output directory exists
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Prepare the CSV data
        all_timesteps = sorted(set().union(*[set(data.keys()) for data in phase_percentages.values()]))
        all_phases = sorted(phase_percentages.keys())
        
        # Create CSV file
        output_path = os.path.join(output_directory, filename)
        
        with open(output_path, 'w') as f:
            # Write header
            f.write("Timestep," + ",".join(all_phases) + "\n")
            
            # Write data for each timestep
            for timestep in all_timesteps:
                line = str(timestep)
                for phase in all_phases:
                    line += f",{phase_percentages.get(phase, {}).get(timestep, 0):.6f}"
                f.write(line + "\n")
        
        logger.info(f"Saved phase data CSV to {output_path}")
        return output_path
    
    def generate_all_reports(self, output_directory: str) -> Dict[str, str]:
        """
        Generate all phase analysis reports and plots.
        
        Args:
            output_directory (str): Directory to save the reports and plots
            
        Returns:
            Dict[str, str]: Dictionary mapping report names to their file paths
        """
        logger.info("Generating all phase analysis reports")
        
        # Ensure the output directory exists
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Generate all reports
        reports = {}
        
        # Generate the all phases plot
        all_phases_plot = self.generate_phase_plot_all(output_directory)
        reports["all_phases_plot"] = all_phases_plot
        
        # Generate the phase summary plot
        summary_plot = self.generate_phase_plot_summary(output_directory)
        reports["summary_plot"] = summary_plot
        
        # Save phase data to CSV
        csv_path = self.save_phase_data_csv(output_directory)
        reports["phase_data_csv"] = csv_path
        
        return reports


def main():
    """
    Main function to demonstrate the usage of the PhaseAnalysisReporter.
    """
    import argparse
    from Condensed_Report_generator import CondensedReportGenerator
    from Data_Load_and_Parse import DataLoaderParser
    
    parser = argparse.ArgumentParser(description='Phase Analysis and Reporting')
    parser.add_argument('input_dir', help='Directory containing input files')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
    parser.add_argument('--condensed-report', help='Path to existing condensed report (optional)')
    args = parser.parse_args()
    
    # Load the condensed report or generate it
    if args.condensed_report and os.path.exists(args.condensed_report):
        with open(args.condensed_report, 'r') as f:
            condensed_report = json.load(f)
        logger.info(f"Loaded existing condensed report from {args.condensed_report}")
    else:
        # Load the data using DataLoaderParser from Component 1
        loader = DataLoaderParser(args.input_dir)
        _, _, thermochimica_data = loader.load_all_data()
        
        # Create an instance of the CondensedReportGenerator
        report_generator = CondensedReportGenerator(thermochimica_data)
        
        # Generate the condensed report
        condensed_report = report_generator.generate_condensed_report()
        logger.info("Generated condensed report")
    
    # Create an instance of the PhaseAnalysisReporter
    phase_reporter = PhaseAnalysisReporter(condensed_report)
    
    # Generate all reports
    reports = phase_reporter.generate_all_reports(args.output_dir)
    
    logger.info("Phase analysis and reporting complete")
    for report_name, file_path in reports.items():
        logger.info(f"{report_name}: {file_path}")


if __name__ == "__main__":
    main()