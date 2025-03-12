import os
import json
import logging
import csv
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Tuple, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Redox-Analyzer')

class RedoxAnalyzer:
    """
    Component 3: Redox Analyzer
    Calculates and reports redox potentials based on UF3/UF4 ratios.
    
    Main functions:
    - calculate_uf3_amount: Calculates total UF3 for a timestep
    - calculate_uf4_amount: Calculates total UF4 for a timestep
    - calculate_redox_ratio: Calculates the UF3/UF4 ratio
    - generate_redox_report: Creates CSV and plot of ratios
    """
    
    def __init__(self, thermochimica_data: Dict[int, Dict[str, Any]]):
        """
        Initialize the Redox Analyzer.
        
        Args:
            thermochimica_data (Dict[int, Dict[str, Any]]): Dictionary of thermochimica data from Component 1
        """
        self.thermochimica_data = thermochimica_data
        self.redox_ratios = {}
        
    def calculate_uf3_amount(self, timestep_data: Dict[str, Any]) -> float:
        """
        Calculates total UF3 for a timestep.
        Specifically sums all UF3 species.
        
        Args:
            timestep_data (Dict[str, Any]): Data for a single timestep
            
        Returns:
            float: Total amount of UF3
        """
        total_uf3 = 0.0
        json_data = timestep_data.get("json_data")
        
        if not json_data:
            logger.warning("No JSON data available for timestep")
            return total_uf3
        
        # Thermochimica JSON typically has a single numeric key for the data point
        for key in json_data:
            if not key.isdigit():
                continue
                
            data_point = json_data[key]
            
            # Process solution phases
            solution_phases = data_point.get("solution phases", {})
            for phase_name, phase_data in solution_phases.items():
                # Skip phases with no species data
                if "species" not in phase_data:
                    continue
                
                species_data = phase_data["species"]
                for species_name, species_info in species_data.items():
                    # Check if this is a UF3 species
                    if "UF3" in species_name:
                        mole_fraction = species_info.get("mole fraction", 0.0)
                        phase_moles = phase_data.get("moles", 0.0)
                        uf3_amount = mole_fraction * phase_moles
                        total_uf3 += uf3_amount
                        logger.debug(f"Found UF3 in {phase_name} phase, species {species_name}: {uf3_amount}")
            
            # Process pure condensed phases
            pure_phases = data_point.get("pure condensed phases", {})
            for phase_name, phase_data in pure_phases.items():
                # Check if this is a UF3 phase
                if "UF3" in phase_name:
                    uf3_amount = phase_data.get("moles", 0.0)
                    total_uf3 += uf3_amount
                    logger.debug(f"Found UF3 in pure phase {phase_name}: {uf3_amount}")
        
        logger.debug(f"Total UF3 amount: {total_uf3}")
        return total_uf3
    
    def calculate_uf4_amount(self, timestep_data: Dict[str, Any]) -> float:
        """
        Calculates total UF4 for a timestep.
        Specifically sums:
        - U[CN=VI]F4 (uranium fluoride with coordination number 6)
        - U[CN=VII]F4 (uranium fluoride with coordination number 7)
        - 2 * U[Dimer]F8 (each dimer contributes 2 UF4 equivalents)
        
        Args:
            timestep_data (Dict[str, Any]): Data for a single timestep
            
        Returns:
            float: Total amount of UF4
        """
        total_uf4 = 0.0
        json_data = timestep_data.get("json_data")
        
        if not json_data:
            logger.warning("No JSON data available for timestep")
            return total_uf4
        
        # Thermochimica JSON typically has a single numeric key for the data point
        for key in json_data:
            if not key.isdigit():
                continue
                
            data_point = json_data[key]
            
            # Process solution phases
            solution_phases = data_point.get("solution phases", {})
            for phase_name, phase_data in solution_phases.items():
                # Skip phases with no species data
                if "species" not in phase_data:
                    continue
                
                species_data = phase_data["species"]
                for species_name, species_info in species_data.items():
                    # Check for different UF4 species types
                    if "U[CN=VI]F4" in species_name:
                        mole_fraction = species_info.get("mole fraction", 0.0)
                        phase_moles = phase_data.get("moles", 0.0)
                        uf4_amount = mole_fraction * phase_moles
                        total_uf4 += uf4_amount
                        logger.debug(f"Found U[CN=VI]F4 in {phase_name} phase, species {species_name}: {uf4_amount}")
                    
                    elif "U[CN=VII]F4" in species_name:
                        mole_fraction = species_info.get("mole fraction", 0.0)
                        phase_moles = phase_data.get("moles", 0.0)
                        uf4_amount = mole_fraction * phase_moles
                        total_uf4 += uf4_amount
                        logger.debug(f"Found U[CN=VII]F4 in {phase_name} phase, species {species_name}: {uf4_amount}")
                    
                    elif "U[Dimer]F8" in species_name:
                        mole_fraction = species_info.get("mole fraction", 0.0)
                        phase_moles = phase_data.get("moles", 0.0)
                        # Each dimer contributes 2 UF4 equivalents
                        uf4_amount = 2 * mole_fraction * phase_moles
                        total_uf4 += uf4_amount
                        logger.debug(f"Found U[Dimer]F8 in {phase_name} phase, species {species_name}: {uf4_amount} (counting as 2 UF4)")
            
            # Process pure condensed phases
            pure_phases = data_point.get("pure condensed phases", {})
            for phase_name, phase_data in pure_phases.items():
                # Check for different UF4 phase types
                if "U[CN=VI]F4" in phase_name or "U[CN=VII]F4" in phase_name:
                    uf4_amount = phase_data.get("moles", 0.0)
                    total_uf4 += uf4_amount
                    logger.debug(f"Found UF4 in pure phase {phase_name}: {uf4_amount}")
                elif "U[Dimer]F8" in phase_name:
                    uf8_amount = phase_data.get("moles", 0.0)
                    # Each dimer contributes 2 UF4 equivalents
                    uf4_amount = 2 * uf8_amount
                    total_uf4 += uf4_amount
                    logger.debug(f"Found U[Dimer]F8 in pure phase {phase_name}: {uf4_amount} (counting as 2 UF4)")
        
        logger.debug(f"Total UF4 amount: {total_uf4}")
        return total_uf4
    
    def calculate_redox_ratio(self, timestep_data: Dict[str, Any]) -> Optional[float]:
        """
        Calculates the UF3/UF4 ratio.
        
        Ratio = UF3 / (U[CN=VI]F4 + U[CN=VII]F4 + 2*U[Dimer]F8)
        
        Args:
            timestep_data (Dict[str, Any]): Data for a single timestep
            
        Returns:
            Optional[float]: UF3/UF4 ratio, or None if calculation cannot be performed
        """
        uf3_amount = self.calculate_uf3_amount(timestep_data)
        uf4_amount = self.calculate_uf4_amount(timestep_data)
        
        # Check if UF4 amount is zero or very small to avoid division by zero
        if uf4_amount < 1e-10:
            logger.warning("UF4 amount is too small or zero, cannot calculate redox ratio")
            return None
        
        # Check if UF3 amount is zero or very small
        if uf3_amount < 1e-10:
            logger.warning("UF3 amount is too small or zero, redox ratio is approximately zero")
            return 0.0
        
        redox_ratio = uf3_amount / uf4_amount
        logger.debug(f"Redox ratio (UF3/UF4): {redox_ratio}")
        return redox_ratio
    
    def generate_redox_report(self) -> Tuple[Dict[int, float], str, str]:
        """
        Creates CSV and plot of redox ratios.
        Handles missing/abnormal data by identifying and excluding it from the plot.
        
        Returns:
            Tuple[Dict[int, float], str, str]: 
                - Dictionary mapping timesteps to redox ratios
                - Path to the CSV file
                - Path to the plot image
        """
        logger.info("Generating redox report")
        
        # Calculate redox ratios for all timesteps
        redox_ratios = {}
        
        for timestep, data in self.thermochimica_data.items():
            ratio = self.calculate_redox_ratio(data)
            if ratio is not None:
                redox_ratios[timestep] = ratio
        
        self.redox_ratios = redox_ratios
        
        # Determine if there are problematic timesteps
        all_timesteps = set(self.thermochimica_data.keys())
        processed_timesteps = set(redox_ratios.keys())
        problematic_timesteps = all_timesteps - processed_timesteps
        
        if problematic_timesteps:
            logger.warning(f"Could not calculate redox ratios for {len(problematic_timesteps)} timesteps")
            logger.warning(f"Problematic timesteps: {sorted(problematic_timesteps)}")
        
        # Create output directory if it doesn't exist
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Save redox ratios to CSV
        csv_path = os.path.join(output_dir, "redox_ratios.csv")
        with open(csv_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Timestep", "UF3/UF4 Ratio"])
            
            for timestep in sorted(redox_ratios.keys()):
                csv_writer.writerow([timestep, redox_ratios[timestep]])
        
        logger.info(f"Saved redox ratios to {csv_path}")
        
        # Create plot of redox ratios
        plt.figure(figsize=(10, 6))
        
        # Get sorted timesteps and corresponding ratios
        sorted_timesteps = sorted(redox_ratios.keys())
        sorted_ratios = [redox_ratios[t] for t in sorted_timesteps]
        
        plt.plot(sorted_timesteps, sorted_ratios, marker='o', linestyle='-')
        plt.xlabel('Timestep')
        plt.ylabel('UF3/UF4 Ratio')
        plt.title('Redox Ratio (UF3/UF4) vs. Timestep')
        plt.grid(True)
        
        # Add annotations for any unusually high or low values
        mean_ratio = sum(sorted_ratios) / len(sorted_ratios)
        std_ratio = (sum((r - mean_ratio) ** 2 for r in sorted_ratios) / len(sorted_ratios)) ** 0.5
        
        for timestep, ratio in redox_ratios.items():
            # If the ratio is more than 3 standard deviations from the mean, annotate it
            if abs(ratio - mean_ratio) > 3 * std_ratio:
                plt.annotate(f"t={timestep}\n{ratio:.3f}", 
                             xy=(timestep, ratio),
                             xytext=(10, 10),
                             textcoords="offset points",
                             arrowprops=dict(arrowstyle="->"))
        
        # Save the plot
        plot_path = os.path.join(output_dir, "redox_ratio_plot.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved redox ratio plot to {plot_path}")
        
        return redox_ratios, csv_path, plot_path
    
    def get_redox_summary_statistics(self) -> Dict[str, float]:
        """
        Calculate summary statistics for the redox ratios.
        
        Returns:
            Dict[str, float]: Dictionary of summary statistics
        """
        if not self.redox_ratios:
            logger.warning("No redox ratios available for statistics calculation")
            return {}
        
        ratios = list(self.redox_ratios.values())
        
        # Calculate basic statistics
        min_ratio = min(ratios)
        max_ratio = max(ratios)
        mean_ratio = sum(ratios) / len(ratios)
        
        # Calculate median
        sorted_ratios = sorted(ratios)
        n = len(sorted_ratios)
        if n % 2 == 0:
            median_ratio = (sorted_ratios[n//2 - 1] + sorted_ratios[n//2]) / 2
        else:
            median_ratio = sorted_ratios[n//2]
        
        # Calculate standard deviation
        variance = sum((r - mean_ratio) ** 2 for r in ratios) / len(ratios)
        std_deviation = variance ** 0.5
        
        return {
            "min": min_ratio,
            "max": max_ratio,
            "mean": mean_ratio,
            "median": median_ratio,
            "std_dev": std_deviation,
            "count": len(ratios)
        }
    
    def save_redox_summary(self, output_directory: str, filename: str = "redox_summary.json") -> str:
        """
        Save the redox summary statistics to a JSON file.
        
        Args:
            output_directory (str): Directory to save the summary
            filename (str, optional): Name of the output file. Defaults to "redox_summary.json".
            
        Returns:
            str: Path to the saved file
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Generate the redox report if it hasn't been generated yet
        if not self.redox_ratios:
            self.generate_redox_report()
        
        # Calculate summary statistics
        summary_stats = self.get_redox_summary_statistics()
        
        # Add timestep information
        summary = {
            "statistics": summary_stats,
            "normal_timesteps": len(self.redox_ratios),
            "problematic_timesteps": len(self.thermochimica_data) - len(self.redox_ratios)
        }
        
        output_path = os.path.join(output_directory, filename)
        
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Saved redox summary to {output_path}")
        return output_path


def main():
    """
    Main function to demonstrate the usage of the RedoxAnalyzer.
    """
    import argparse
    from Data_Load_and_Parse import DataLoaderParser
    
    parser = argparse.ArgumentParser(description='Redox Analyzer')
    parser.add_argument('input_dir', help='Directory containing input files')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
    args = parser.parse_args()
    
    # Load the data using DataLoaderParser from Component 1
    loader = DataLoaderParser(args.input_dir)
    _, _, thermochimica_data = loader.load_all_data()
    
    # Create an instance of the RedoxAnalyzer
    analyzer = RedoxAnalyzer(thermochimica_data)
    
    # Generate the redox report
    redox_ratios, csv_path, plot_path = analyzer.generate_redox_report()
    
    logger.info(f"Generated redox report with {len(redox_ratios)} valid timesteps")
    logger.info(f"CSV file: {csv_path}")
    logger.info(f"Plot file: {plot_path}")
    
    # Get and save summary statistics
    summary_path = analyzer.save_redox_summary(args.output_dir)
    logger.info(f"Summary file: {summary_path}")
    
    # Print some sample ratios
    sample_timesteps = sorted(redox_ratios.keys())[:5]
    logger.info("Sample redox ratios:")
    for timestep in sample_timesteps:
        logger.info(f"Timestep {timestep}: UF3/UF4 = {redox_ratios[timestep]:.6f}")
    
    # Print summary statistics
    summary_stats = analyzer.get_redox_summary_statistics()
    logger.info(f"Summary statistics:")
    for stat, value in summary_stats.items():
        logger.info(f"{stat}: {value}")


if __name__ == "__main__":
    main()