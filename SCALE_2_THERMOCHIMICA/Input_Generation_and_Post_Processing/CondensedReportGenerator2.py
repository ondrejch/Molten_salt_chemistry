import os
import json
import logging
from collections import OrderedDict
from typing import Dict, Any, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Condensed-Report-Generator')

class CondensedReportGenerator:
    """
    Component 2: Condensed Report Generator
    Stitches together all Thermochimica output data without modifying the structure.
    
    Main functions:
    - generate_condensed_report: Creates the condensed report by combining all timestep data
    - save_condensed_report: Saves the report to a JSON file
    """
    
    def __init__(self, thermochimica_data: Dict[int, Dict[str, Any]]):
        """
        Initialize the Condensed Report Generator.
        
        Args:
            thermochimica_data (Dict[int, Dict[str, Any]]): Dictionary of thermochimica data from Component 1
        """
        self.thermochimica_data = thermochimica_data
        self.condensed_report = OrderedDict()
        
    def generate_condensed_report(self) -> OrderedDict:
        """
        Creates a condensed report by stitching together all Thermochimica output data
        without modifying the structure. Orders timesteps sequentially.
        
        Returns:
            OrderedDict: Condensed report with original data structure
        """
        logger.info("Generating condensed report")
        
        # Get all timesteps and sort them numerically
        all_timesteps = sorted(self.thermochimica_data.keys())
        
        # Check for missing timesteps
        if all_timesteps:
            min_timestep = min(all_timesteps)
            max_timestep = max(all_timesteps)
            expected_timesteps = set(range(min_timestep, max_timestep + 1))
            missing_timesteps = expected_timesteps - set(all_timesteps)
            
            if missing_timesteps:
                logger.warning(f"Missing timesteps detected: {sorted(missing_timesteps)}")
        
        # Process each timestep in order
        for timestep in all_timesteps:
            data = self.thermochimica_data[timestep]
            
            # Extract the json_data directly without modification
            json_data = data.get("json_data")
            
            if json_data:
                # Store the data with the timestep as a string key for JSON compatibility
                self.condensed_report[str(timestep)] = json_data
            else:
                logger.warning(f"No JSON data found for timestep {timestep}")
        
        logger.info(f"Generated condensed report for {len(self.condensed_report)} timesteps")
        return self.condensed_report
    
    def save_condensed_report(self, output_directory: str, filename: str = "Condensed_Thermochimica_Report.json") -> str:
        """
        Save the condensed report to a JSON file.
        
        Args:
            output_directory (str): Directory to save the report
            filename (str, optional): Name of the output file. Defaults to "Condensed_Thermochimica_Report.json".
            
        Returns:
            str: Path to the saved file
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
            
        # Generate the report if it hasn't been generated yet
        if not self.condensed_report:
            self.generate_condensed_report()
            
        output_path = os.path.join(output_directory, filename)
        
        with open(output_path, 'w') as f:
            json.dump(self.condensed_report, f, indent=2)
            
        logger.info(f"Saved condensed report to {output_path}")
        
        # Generate a summary of the report
        timesteps = list(self.condensed_report.keys())
        summary_path = os.path.join(output_directory, "summary_" + filename + ".out")
        
        with open(summary_path, 'w') as f:
            f.write("# Condensed Report Summary\n\n")
            f.write(f"Total timesteps: {len(timesteps)}\n")
            
            if timesteps:
                f.write(f"First timestep: {timesteps[0]}\n")
                f.write(f"Last timestep: {timesteps[-1]}\n")
                
                # Extract information about phases in the first timestep
                first_data = self.condensed_report[timesteps[0]]
                first_key = next(iter(first_data))
                
                if "solution phases" in first_data[first_key]:
                    solution_phases = list(first_data[first_key]["solution phases"].keys())
                    f.write(f"\nSolution phases ({len(solution_phases)}):\n")
                    for phase in solution_phases:
                        if phase.startswith("MSFL"):
                            f.write(f"- {phase} (SALT PHASE)\n")
                        else:
                            f.write(f"- {phase}\n")
                
                if "pure condensed phases" in first_data[first_key]:
                    pure_phases = list(first_data[first_key]["pure condensed phases"].keys())
                    f.write(f"\nPure condensed phases ({len(pure_phases)}):\n")
                    for phase in pure_phases[:10]:  # Show first 10 to avoid excessive output
                        f.write(f"- {phase}\n")
                    if len(pure_phases) > 10:
                        f.write(f"- ... and {len(pure_phases) - 10} more phases\n")
            
        logger.info(f"Saved condensed report summary to {summary_path}")
        return output_path
    
    def get_salt_phases(self, timestep: Optional[str] = None) -> List[str]:
        """
        Get a list of salt phases (MSFL) for a specific timestep or across all timesteps.
        
        Args:
            timestep (Optional[str]): Specific timestep to check, or None for all timesteps
            
        Returns:
            List[str]: List of salt phase names
        """
        salt_phases = set()
        
        # Generate the report if it hasn't been generated yet
        if not self.condensed_report:
            self.generate_condensed_report()
        
        # Filter timesteps if specified
        timesteps_to_check = [timestep] if timestep else self.condensed_report.keys()
        
        for ts in timesteps_to_check:
            if ts not in self.condensed_report:
                continue
                
            data = self.condensed_report[ts]
            for key in data:
                if not key.isdigit():
                    continue
                    
                if "solution phases" in data[key]:
                    for phase_name in data[key]["solution phases"].keys():
                        if phase_name.startswith("MSFL"):
                            salt_phases.add(phase_name)
        
        return sorted(list(salt_phases))


def main():
    """
    Main function to demonstrate the usage of the CondensedReportGenerator.
    """
    import argparse
    from Data_Load_and_Parse import DataLoaderParser
    
    parser = argparse.ArgumentParser(description='Condensed Report Generator')
    parser.add_argument('input_dir', help='Directory containing input files')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
    args = parser.parse_args()
    
    # Load the data using DataLoaderParser from Component 1
    loader = DataLoaderParser(args.input_dir)
    _, _, thermochimica_data = loader.load_all_data()
    
    # Create an instance of the CondensedReportGenerator
    report_generator = CondensedReportGenerator(thermochimica_data)
    
    # Generate the condensed report
    report_generator.generate_condensed_report()
    
    # Get salt phases
    salt_phases = report_generator.get_salt_phases()
    logger.info(f"Salt phases detected: {salt_phases}")
    
    # Save the condensed report
    output_path = report_generator.save_condensed_report(args.output_dir)
    logger.info(f"Condensed report saved to {output_path}")


if __name__ == "__main__":
    main()