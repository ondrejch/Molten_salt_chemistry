import os
import json
import logging
import csv
import numpy as np
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
    Calculates and reports redox potentials based on UF3/UF4 and Cr2+/Cr3+ ratios.
    
    Main functions:
    - calculate_uf3_uf4_ratio: Calculates the UF3/UF4 ratio from MSFL cations
    - calculate_cr2_cr3_ratio: Calculates the Cr2+/Cr3+ ratio from MSFL cations
    - process_all_timesteps: Processes all timesteps to calculate ratios
    - generate_redox_report: Creates CSV and plot of ratios
    - plot_gibbs_energy: Creates plot of integral Gibbs energy over time
    """
    
    def __init__(self, condensed_thermochimica_data: Dict[str, Any]):
        """
        Initialize the Redox Analyzer.
        
        Args:
            condensed_thermochimica_data (Dict[str, Any]): Dictionary of condensed thermochimica data
        """
        self.thermochimica_data = condensed_thermochimica_data
        self.uf_redox_ratios = {}
        self.cr_redox_ratios = {}
        
    def calculate_uf3_uf4_ratio(self, timestep_data: Dict[str, Any]) -> Optional[float]:
        """
        Calculate UF3/UF4 ratio from MSFL cations in a single timestep.
        
        Args:
            timestep_data (Dict[str, Any]): Data for a single timestep
            
        Returns:
            Optional[float]: UF3/UF4 ratio or None if cannot be calculated
        """
        # Navigate through the nested structure to get to the MSFL cations
        try:
            # Get data point - should be "1" based on your example
            for data_point_key in timestep_data:
                data_point = timestep_data[data_point_key]
                
                # Get solution phases
                solution_phases = data_point.get("solution phases", {})
                
                # Check if MSFL exists
                if "MSFL" not in solution_phases:
                    logger.warning("MSFL phase not found in solution phases")
                    return None
                
                msfl = solution_phases["MSFL"]
                
                # Check if MSFL has cations
                if "cations" not in msfl:
                    logger.warning("No cations found in MSFL phase")
                    return None
                
                cations = msfl["cations"]
                
                # Get the total moles in MSFL phase
                msfl_moles = msfl.get("moles", 0.0)
                
                # If moles is zero, phase is not present
                if msfl_moles <= 0:
                    logger.warning(f"MSFL phase has zero or negative moles ({msfl_moles})")
                    return None
                
                # Extract uranium species mole fractions
                u3_mole_fraction = cations.get("U[3+]", {}).get("mole fraction", 0.0)
                u_cn6_mole_fraction = cations.get("U[CN=VI]", {}).get("mole fraction", 0.0)
                u_cn7_mole_fraction = cations.get("U[CN=VII", {}).get("mole fraction", 0.0)
                u_dimer_mole_fraction = cations.get("U[Dimer]", {}).get("mole fraction", 0.0)
                
                # Calculate UF3 and UF4 amounts
                uf3_amount = u3_mole_fraction * msfl_moles
                
                # U[Dimer] contributes 2 UF4 equivalents per mole
                uf4_amount = (u_cn6_mole_fraction + u_cn7_mole_fraction + 2 * u_dimer_mole_fraction) * msfl_moles
                
                # Log the extracted values for debugging
                logger.debug(f"MSFL moles: {msfl_moles}")
                logger.debug(f"U[3+] mole fraction: {u3_mole_fraction}")
                logger.debug(f"U[CN=VI] mole fraction: {u_cn6_mole_fraction}")
                logger.debug(f"U[CN=VII] mole fraction: {u_cn7_mole_fraction}")
                logger.debug(f"U[Dimer] mole fraction: {u_dimer_mole_fraction}")
                logger.debug(f"UF3 amount: {uf3_amount}")
                logger.debug(f"UF4 amount: {uf4_amount}")
                
                # Check if UF4 amount is zero or very small to avoid division by zero
                if uf4_amount < 1e-30:
                    logger.warning("UF4 amount is too small or zero, cannot calculate redox ratio")
                    return None
                
                # Check if UF3 amount is zero or very small
                if uf3_amount < 1e-30:
                    logger.warning("UF3 amount is too small or zero, redox ratio is approximately zero")
                    return np.nextafter(0, 1)  # Return smallest positive float
                
                redox_ratio = uf3_amount / uf4_amount
                logger.debug(f"Redox ratio (UF3/UF4): {redox_ratio:.6e}")
                return redox_ratio
                
        except Exception as e:
            logger.error(f"Error calculating UF3/UF4 ratio: {str(e)}")
            return None

    def calculate_cr2_cr3_ratio(self, timestep_data: Dict[str, Any]) -> Optional[float]:
        """
        Calculate Cr2+/Cr3+ ratio from MSFL cations in a single timestep.
        
        Args:
            timestep_data (Dict[str, Any]): Data for a single timestep
            
        Returns:
            Optional[float]: Cr2+/Cr3+ ratio or None if cannot be calculated
        """
        # Navigate through the nested structure to get to the MSFL cations
        try:
            # Get data point
            for data_point_key in timestep_data:
                data_point = timestep_data[data_point_key]
                
                # Get solution phases
                solution_phases = data_point.get("solution phases", {})
                
                # Check if MSFL exists
                if "MSFL" not in solution_phases:
                    logger.warning("MSFL phase not found in solution phases")
                    return None
                
                msfl = solution_phases["MSFL"]
                
                # Check if MSFL has cations
                if "cations" not in msfl:
                    logger.warning("No cations found in MSFL phase")
                    return None
                
                cations = msfl["cations"]
                
                # Get the total moles in MSFL phase
                msfl_moles = msfl.get("moles", 0.0)
                
                # If moles is zero, phase is not present
                if msfl_moles <= 0:
                    logger.warning(f"MSFL phase has zero or negative moles ({msfl_moles})")
                    return None
                
                # Extract chromium species mole fractions
                cr2_mole_fraction = cations.get("Cr[2+]", {}).get("mole fraction", 0.0)
                cr3_mole_fraction = cations.get("Cr[3+]", {}).get("mole fraction", 0.0)
                
                # Calculate Cr2+ and Cr3+ amounts
                cr2_amount = cr2_mole_fraction * msfl_moles
                cr3_amount = cr3_mole_fraction * msfl_moles
                
                # Log the extracted values for debugging
                logger.debug(f"MSFL moles: {msfl_moles}")
                logger.debug(f"Cr[2+] mole fraction: {cr2_mole_fraction}")
                logger.debug(f"Cr[3+] mole fraction: {cr3_mole_fraction}")
                logger.debug(f"Cr2+ amount: {cr2_amount}")
                logger.debug(f"Cr3+ amount: {cr3_amount}")
                
                # Check if Cr3+ amount is zero or very small to avoid division by zero
                if cr3_amount < 1e-30:
                    logger.warning("Cr3+ amount is too small or zero, cannot calculate redox ratio")
                    return None
                
                # Check if Cr2+ amount is zero or very small
                if cr2_amount < 1e-30:
                    logger.warning("Cr2+ amount is too small or zero, redox ratio is approximately zero")
                    return np.nextafter(0, 1)  # Return smallest positive float
                
                redox_ratio = cr2_amount / cr3_amount
                logger.debug(f"Redox ratio (Cr2+/Cr3+): {redox_ratio:.6e}")
                return redox_ratio
                
        except Exception as e:
            logger.error(f"Error calculating Cr2+/Cr3+ ratio: {str(e)}")
            return None
    
    def process_all_timesteps(self) -> Tuple[Dict[int, float], Dict[int, float]]:
        """
        Process all timesteps to calculate UF3/UF4 and Cr2+/Cr3+ ratios.
        
        Returns:
            Tuple[Dict[int, float], Dict[int, float]]: 
                - Dictionary mapping timesteps to UF3/UF4 redox ratios
                - Dictionary mapping timesteps to Cr2+/Cr3+ redox ratios
        """
        logger.info("Processing all timesteps for redox ratios")
        uf_redox_ratios = {}
        cr_redox_ratios = {}
        
        for timestep_str, data in self.thermochimica_data.items():
            try:
                # Convert timestep string to integer
                timestep = int(timestep_str)
                
                # Calculate UF3/UF4 ratio for this timestep
                uf_ratio = self.calculate_uf3_uf4_ratio(data)
                if uf_ratio is not None:
                    uf_redox_ratios[timestep] = uf_ratio
                
                # Calculate Cr2+/Cr3+ ratio for this timestep
                cr_ratio = self.calculate_cr2_cr3_ratio(data)
                if cr_ratio is not None:
                    cr_redox_ratios[timestep] = cr_ratio
                
            except ValueError:
                logger.warning(f"Invalid timestep format: {timestep_str}")
                continue
        
        self.uf_redox_ratios = uf_redox_ratios
        self.cr_redox_ratios = cr_redox_ratios
        return uf_redox_ratios, cr_redox_ratios
    
    def generate_redox_report(self, output_dir: str = "output") -> Tuple[Dict[int, float], Dict[int, float], List[str], List[str]]:
        """
        Creates CSV and semi-log plots of UF3/UF4 and Cr2+/Cr3+ redox ratios.
        
        Args:
            output_dir (str, optional): Directory to save output files. Defaults to "output".
            
        Returns:
            Tuple[Dict[int, float], Dict[int, float], List[str], List[str]]: 
                - Dictionary mapping timesteps to UF3/UF4 redox ratios
                - Dictionary mapping timesteps to Cr2+/Cr3+ redox ratios
                - Paths to the CSV files
                - Paths to the plot images
        """
        logger.info("Generating redox reports")
        
        # Process all timesteps if not already done
        if not self.uf_redox_ratios or not self.cr_redox_ratios:
            self.process_all_timesteps()
        
        # Determine if there are problematic timesteps
        all_timesteps = set(int(ts) for ts in self.thermochimica_data.keys() if ts.isdigit())
        processed_uf_timesteps = set(self.uf_redox_ratios.keys())
        processed_cr_timesteps = set(self.cr_redox_ratios.keys())
        
        problematic_uf_timesteps = all_timesteps - processed_uf_timesteps
        problematic_cr_timesteps = all_timesteps - processed_cr_timesteps
        
        if problematic_uf_timesteps:
            logger.warning(f"Could not calculate UF3/UF4 ratios for {len(problematic_uf_timesteps)} timesteps")
            logger.warning(f"Problematic UF3/UF4 timesteps: {sorted(problematic_uf_timesteps)}")
        
        if problematic_cr_timesteps:
            logger.warning(f"Could not calculate Cr2+/Cr3+ ratios for {len(problematic_cr_timesteps)} timesteps")
            logger.warning(f"Problematic Cr2+/Cr3+ timesteps: {sorted(problematic_cr_timesteps)}")
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        csv_paths = []
        plot_paths = []
        
        # Generate UF3/UF4 report
        if self.uf_redox_ratios:
            # Save UF3/UF4 ratios to CSV with high precision
            uf_csv_path = os.path.join(output_dir, "uf3_uf4_ratios.csv")
            with open(uf_csv_path, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(["Timestep", "UF3/UF4 Ratio"])
                
                for timestep in sorted(self.uf_redox_ratios.keys()):
                    csv_writer.writerow([timestep, f"{self.uf_redox_ratios[timestep]:.10e}"])
            
            logger.info(f"Saved UF3/UF4 redox ratios to {uf_csv_path}")
            csv_paths.append(uf_csv_path)
            
            # Create semi-log plot of UF3/UF4 ratios
            plt.figure(figsize=(10, 6))
            
            # Get sorted timesteps and corresponding ratios
            sorted_timesteps = sorted(self.uf_redox_ratios.keys())

            # Skip the first timestep if there are multiple timesteps
            if len(sorted_timesteps) > 1:
                # Remove the first timestep
                sorted_timesteps = sorted_timesteps[1:]
    
            sorted_ratios = [self.uf_redox_ratios[t] for t in sorted_timesteps]
            sorted_ratios = [max(r, np.nextafter(0, 1)) for r in sorted_ratios]
            
            plt.semilogy(sorted_timesteps, sorted_ratios, marker='o', linestyle='-')
            plt.xlabel('Timestep')
            plt.ylabel('UF3/UF4 Ratio (log scale)')
            plt.title('Redox Ratio (UF3/UF4) vs. Timestep')
            plt.grid(True, which="both", ls="-")
            
            # Save the plot
            uf_plot_path = os.path.join(output_dir, "uf3_uf4_ratio_plot.png")
            plt.savefig(uf_plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Saved UF3/UF4 redox ratio plot to {uf_plot_path}")
            plot_paths.append(uf_plot_path)
        
        # Generate Cr2+/Cr3+ report
        if self.cr_redox_ratios:
            # Save Cr2+/Cr3+ ratios to CSV with high precision
            cr_csv_path = os.path.join(output_dir, "cr2_cr3_ratios.csv")
            with open(cr_csv_path, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(["Timestep", "Cr2+/Cr3+ Ratio"])
                
                for timestep in sorted(self.cr_redox_ratios.keys()):
                    csv_writer.writerow([timestep, f"{self.cr_redox_ratios[timestep]:.10e}"])
            
            logger.info(f"Saved Cr2+/Cr3+ redox ratios to {cr_csv_path}")
            csv_paths.append(cr_csv_path)
            
            # Create semi-log plot of Cr2+/Cr3+ ratios
            plt.figure(figsize=(10, 6))
            
            # Get sorted timesteps and corresponding ratios
            sorted_timesteps = sorted(self.cr_redox_ratios.keys())
            sorted_ratios = [self.cr_redox_ratios[t] for t in sorted_timesteps]
            
            # Replace any zeros with the smallest positive float for plotting
            sorted_ratios = [max(r, np.nextafter(0, 1)) for r in sorted_ratios]
            
            plt.semilogy(sorted_timesteps, sorted_ratios, marker='o', linestyle='-', color='green')
            plt.xlabel('Timestep')
            plt.ylabel('Cr2+/Cr3+ Ratio (log scale)')
            plt.title('Redox Ratio (Cr2+/Cr3+) vs. Timestep')
            plt.grid(True, which="both", ls="-")
            
            # Save the plot
            cr_plot_path = os.path.join(output_dir, "cr2_cr3_ratio_plot.png")
            plt.savefig(cr_plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Saved Cr2+/Cr3+ redox ratio plot to {cr_plot_path}")
            plot_paths.append(cr_plot_path)
        
        # Create combined semi-log plot if both ratios are available
        if self.uf_redox_ratios and self.cr_redox_ratios:
            plt.figure(figsize=(12, 7))
            
            # Sort the timesteps and get common timesteps
            all_sorted_timesteps = sorted(set(self.uf_redox_ratios.keys()) | set(self.cr_redox_ratios.keys()))
            
            # For the combined plot section:

            # Plot UF3/UF4 ratios
            uf_timesteps = sorted(self.uf_redox_ratios.keys())
            if len(uf_timesteps) > 1:
                uf_timesteps = uf_timesteps[1:]  # Skip first timestep
                
            uf_ratios = [max(self.uf_redox_ratios[t], np.nextafter(0, 1)) for t in uf_timesteps]
            plt.semilogy(uf_timesteps, uf_ratios, marker='o', linestyle='-', label='UF3/UF4')
            
            # Plot Cr2+/Cr3+ ratios
            cr_timesteps = sorted(self.cr_redox_ratios.keys())
            cr_ratios = [max(self.cr_redox_ratios[t], np.nextafter(0, 1)) for t in cr_timesteps]
            plt.semilogy(cr_timesteps, cr_ratios, marker='s', linestyle='-', color='green', label='Cr2+/Cr3+')
            
            plt.xlabel('Timestep')
            plt.ylabel('Redox Ratio (log scale)')
            plt.title('Redox Ratios vs. Timestep')
            plt.grid(True, which="both", ls="-")
            plt.legend()
            
            # Save the plot
            combined_plot_path = os.path.join(output_dir, "combined_redox_ratios_plot.png")
            plt.savefig(combined_plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Saved combined redox ratios plot to {combined_plot_path}")
            plot_paths.append(combined_plot_path)
        
        return self.uf_redox_ratios, self.cr_redox_ratios, csv_paths, plot_paths
    
    def plot_gibbs_energy(self, output_dir: str = "output") -> Tuple[Dict[int, float], str]:
        """
        Creates a semi-log plot of integral Gibbs energy at every timestep.
        
        Args:
            output_dir (str, optional): Directory to save output files. Defaults to "output".
            
        Returns:
            Tuple[Dict[int, float], str]: 
                - Dictionary mapping timesteps to Gibbs energy values
                - Path to the plot image
        """
        logger.info("Generating Gibbs energy plot")
        
        # Extract Gibbs energy values from all timesteps
        gibbs_energies = {}
        
        for timestep_str, data in self.thermochimica_data.items():
            try:
                # Convert timestep string to integer
                timestep = int(timestep_str)
                
                # Extract Gibbs energy from data
                # Navigate through nested structure to get to the Gibbs energy value
                for data_point_key in data:
                    data_point = data[data_point_key]
                    
                    # Get integral Gibbs energy
                    if "integral Gibbs energy" in data_point:
                        gibbs_energy = data_point["integral Gibbs energy"]
                        gibbs_energies[timestep] = gibbs_energy
                        break
                
            except ValueError:
                logger.warning(f"Invalid timestep format: {timestep_str}")
                continue
            except Exception as e:
                logger.error(f"Error extracting Gibbs energy for timestep {timestep_str}: {str(e)}")
                continue
        
        # Check if we have any data
        if not gibbs_energies:
            logger.warning("No Gibbs energy data found")
            return {}, ""
        
        logger.info(f"Extracted Gibbs energy values for {len(gibbs_energies)} timesteps")
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Save Gibbs energy values to CSV with high precision
        csv_path = os.path.join(output_dir, "gibbs_energy.csv")
        with open(csv_path, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Timestep", "Integral Gibbs Energy"])
            
            for timestep in sorted(gibbs_energies.keys()):
                csv_writer.writerow([timestep, f"{gibbs_energies[timestep]:.10e}"])
        
        logger.info(f"Saved Gibbs energy values to {csv_path}")
        
        # Create plot of Gibbs energy (absolute values, semi-log scale)
        plt.figure(figsize=(10, 6))
        
        # Get sorted timesteps and corresponding Gibbs energies (use absolute values)
        sorted_timesteps = sorted(gibbs_energies.keys())
        sorted_energies = [abs(gibbs_energies[t]) for t in sorted_timesteps]
        
        plt.semilogy(sorted_timesteps, sorted_energies, marker='o', linestyle='-', color='green')
        plt.xlabel('Timestep')
        plt.ylabel('|Integral Gibbs Energy| (J, log scale)')
        plt.title('Absolute Integral Gibbs Energy vs. Timestep')
        plt.grid(True, which="both", ls="-")
        
        # Save the plot
        plot_path = os.path.join(output_dir, "gibbs_energy_semilog_plot.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved Gibbs energy semi-log plot to {plot_path}")
        
        # Also create linear plot for comparison
        plt.figure(figsize=(10, 6))
        sorted_timesteps = sorted(gibbs_energies.keys())
        sorted_energies = [gibbs_energies[t] for t in sorted_timesteps]
        
        plt.plot(sorted_timesteps, sorted_energies, marker='o', linestyle='-', color='blue')
        plt.xlabel('Timestep')
        plt.ylabel('Integral Gibbs Energy (J)')
        plt.title('Integral Gibbs Energy vs. Timestep (Linear Scale)')
        plt.grid(True)
        plt.ticklabel_format(axis='y', style='sci', scilimits=(-4, 4))
        
        # Save the linear plot
        linear_plot_path = os.path.join(output_dir, "gibbs_energy_linear_plot.png")
        plt.savefig(linear_plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Saved Gibbs energy linear plot to {linear_plot_path}")
        
        return gibbs_energies, plot_path

    def get_redox_summary_statistics(self, redox_ratios: Dict[int, float], ratio_name: str = "UF3/UF4") -> Dict[str, float]:
        """
        Calculate summary statistics for the redox ratios.
        
        Args:
            redox_ratios (Dict[int, float]): Dictionary of redox ratios
            ratio_name (str, optional): Name of the ratio for logging. Defaults to "UF3/UF4".
            
        Returns:
            Dict[str, float]: Dictionary of summary statistics
        """
        if not redox_ratios:
            logger.warning(f"No {ratio_name} redox ratios available for statistics calculation")
            return {}
        
        ratios = list(redox_ratios.values())
        
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
        
        # Calculate geometric mean (more appropriate for very small numbers)
        # Replace zeros with smallest positive float
        nonzero_ratios = [max(r, np.nextafter(0, 1)) for r in ratios]
        log_values = [np.log(r) for r in nonzero_ratios]
        geometric_mean = np.exp(sum(log_values) / len(log_values))
        
        return {
            "min": min_ratio,
            "max": max_ratio,
            "mean": mean_ratio,
            "median": median_ratio,
            "geometric_mean": geometric_mean,
            "std_dev": std_deviation,
            "count": len(ratios)
        }
    
    def save_redox_summary(self, output_directory: str) -> List[str]:
        """
        Save the redox summary statistics for both UF3/UF4 and Cr2+/Cr3+ to JSON files.
        
        Args:
            output_directory (str): Directory to save the summaries
            
        Returns:
            List[str]: Paths to the saved files
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Process all timesteps if not already done
        if not self.uf_redox_ratios or not self.cr_redox_ratios:
            self.process_all_timesteps()
        
        output_paths = []
        
        # Save UF3/UF4 summary if available
        if self.uf_redox_ratios:
            # Calculate summary statistics
            uf_summary_stats = self.get_redox_summary_statistics(self.uf_redox_ratios, "UF3/UF4")
            
            # Add timestep information
            all_timesteps = len([ts for ts in self.thermochimica_data.keys() if ts.isdigit()])
            
            uf_summary = {
                "statistics": uf_summary_stats,
                "normal_timesteps": len(self.uf_redox_ratios),
                "problematic_timesteps": all_timesteps - len(self.uf_redox_ratios)
            }
            
            uf_output_path = os.path.join(output_directory, "uf3_uf4_summary.json")
            
            with open(uf_output_path, 'w') as f:
                json.dump(uf_summary, f, indent=2)
            
            logger.info(f"Saved UF3/UF4 redox summary to {uf_output_path}")
            output_paths.append(uf_output_path)
        
        # Save Cr2+/Cr3+ summary if available
        if self.cr_redox_ratios:
            # Calculate summary statistics
            cr_summary_stats = self.get_redox_summary_statistics(self.cr_redox_ratios, "Cr2+/Cr3+")
            
            # Add timestep information
            all_timesteps = len([ts for ts in self.thermochimica_data.keys() if ts.isdigit()])
            
            cr_summary = {
                "statistics": cr_summary_stats,
                "normal_timesteps": len(self.cr_redox_ratios),
                "problematic_timesteps": all_timesteps - len(self.cr_redox_ratios)
            }
            
            cr_output_path = os.path.join(output_directory, "cr2_cr3_summary.json")
            
            with open(cr_output_path, 'w') as f:
                json.dump(cr_summary, f, indent=2)
            
            logger.info(f"Saved Cr2+/Cr3+ redox summary to {cr_output_path}")
            output_paths.append(cr_output_path)
        
        return output_paths


def main():
    """
    Main function to demonstrate the usage of the RedoxAnalyzer.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Redox Analyzer')
    parser.add_argument('input_file', help='Path to condensed_thermochimica_report.json file')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
    parser.add_argument('--plot-gibbs', action='store_true', help='Generate plot of integral Gibbs energy')
    args = parser.parse_args()
    
    # Load the condensed Thermochimica report
    try:
        with open(args.input_file, 'r') as f:
            condensed_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading condensed Thermochimica report: {str(e)}")
        return
    
    # Create an instance of the RedoxAnalyzer
    analyzer = RedoxAnalyzer(condensed_data)
    
    # Generate the redox report
    uf_redox_ratios, cr_redox_ratios, csv_paths, plot_paths = analyzer.generate_redox_report(args.output_dir)
    
    logger.info(f"Generated UF3/UF4 redox report with {len(uf_redox_ratios)} valid timesteps")
    logger.info(f"Generated Cr2+/Cr3+ redox report with {len(cr_redox_ratios)} valid timesteps")
    
    for path in csv_paths:
        logger.info(f"CSV file: {path}")
    
    for path in plot_paths:
        logger.info(f"Plot file: {path}")
    
    # Get and save summary statistics
    summary_paths = analyzer.save_redox_summary(args.output_dir)
    for path in summary_paths:
        logger.info(f"Summary file: {path}")
    
    # Plot Gibbs energy if requested
    if args.plot_gibbs:
        gibbs_energies, gibbs_plot_path = analyzer.plot_gibbs_energy(args.output_dir)
        logger.info(f"Generated Gibbs energy plot with {len(gibbs_energies)} valid timesteps")
        logger.info(f"Plot file: {gibbs_plot_path}")
        
        # Save Gibbs energy summary
        gibbs_summary_path = analyzer.save_gibbs_energy_summary(gibbs_energies, args.output_dir)
        logger.info(f"Gibbs summary file: {gibbs_summary_path}")
        
        # Print some sample Gibbs energy values
        sample_timesteps = sorted(gibbs_energies.keys())[:5] if gibbs_energies else []
        logger.info("Sample Gibbs energy values:")
        for timestep in sample_timesteps:
            logger.info(f"Timestep {timestep}: Gibbs Energy = {gibbs_energies[timestep]:.6e} J")
    
    # Print some sample UF3/UF4 ratios
    sample_uf_timesteps = sorted(uf_redox_ratios.keys())[:5] if uf_redox_ratios else []
    logger.info("Sample UF3/UF4 redox ratios:")
    for timestep in sample_uf_timesteps:
        logger.info(f"Timestep {timestep}: UF3/UF4 = {uf_redox_ratios[timestep]:.6e}")
    
    # Print some sample Cr2+/Cr3+ ratios
    sample_cr_timesteps = sorted(cr_redox_ratios.keys())[:5] if cr_redox_ratios else []
    logger.info("Sample Cr2+/Cr3+ redox ratios:")
    for timestep in sample_cr_timesteps:
        logger.info(f"Timestep {timestep}: Cr2+/Cr3+ = {cr_redox_ratios[timestep]:.6e}")
    
    # Print summary statistics for UF3/UF4
    uf_summary_stats = analyzer.get_redox_summary_statistics(uf_redox_ratios, "UF3/UF4")
    logger.info(f"UF3/UF4 summary statistics:")
    for stat, value in uf_summary_stats.items():
        logger.info(f"{stat}: {value}")
    
    # Print summary statistics for Cr2+/Cr3+
    cr_summary_stats = analyzer.get_redox_summary_statistics(cr_redox_ratios, "Cr2+/Cr3+")
    logger.info(f"Cr2+/Cr3+ summary statistics:")
    for stat, value in cr_summary_stats.items():
        logger.info(f"{stat}: {value}")


if __name__ == "__main__":
    main()