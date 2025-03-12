import os
import json
import logging
from typing import Dict, Any, List, Set, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Condensed-Report-Generator')

class CondensedReportGenerator:
    """
    Component 2: Condensed Report Generator
    Creates a condensed version of all Thermochimica output data with phase classifications.
    
    Main functions:
    - identify_all_phases: Identifies all phases present across all timesteps
    - classify_phases: Classifies each phase as salt, gas, or solid
    - extract_species_data: Extracts information only for present species
    - generate_condensed_report: Creates the condensed report
    """
    
    def __init__(self, thermochimica_data: Dict[int, Dict[str, Any]]):
        """
        Initialize the Condensed Report Generator.
        
        Args:
            thermochimica_data (Dict[int, Dict[str, Any]]): Dictionary of thermochimica data from Component 1
        """
        self.thermochimica_data = thermochimica_data
        self.all_phases = set()
        self.phase_classifications = {}
        self.condensed_report = {}
        
    def identify_all_phases(self) -> Set[str]:
        """
        Identifies all phases present across all timesteps.
        
        Returns:
            Set[str]: Set of all unique phase names
        """
        logger.info("Identifying all phases across timesteps")
        all_phases = set()
        
        for timestep, data in self.thermochimica_data.items():
            json_data = data.get("json_data")
            if not json_data:
                continue
                
            # Thermochimica JSON typically has a single numeric key for the data point
            for key in json_data:
                if not key.isdigit():
                    continue
                    
                data_point = json_data[key]
                
                # Extract solution phases
                solution_phases = data_point.get("solution phases", {})
                for phase_name in solution_phases.keys():
                    all_phases.add(phase_name)
                
                # Extract pure condensed phases
                pure_phases = data_point.get("pure condensed phases", {})
                for phase_name in pure_phases.keys():
                    all_phases.add(phase_name)
        
        logger.info(f"Identified {len(all_phases)} unique phases")
        self.all_phases = all_phases
        return all_phases
    
    def classify_phases(self) -> Dict[str, str]:
        """
        Classifies each phase as salt, gas, or solid based on its characteristics.
        
        Classification rules:
        - "gas" if phase name contains "gas" (case insensitive)
        - "salt" if phase name contains "salt", "liquid", or "melt" (case insensitive)
        - "solid" for all other phases
        
        Returns:
            Dict[str, str]: Dictionary mapping phase names to their classifications
        """
        logger.info("Classifying phases")
        
        if not self.all_phases:
            self.identify_all_phases()
        
        phase_classifications = {}
        
        for phase_name in self.all_phases:
            phase_name_lower = phase_name.lower()
            
            if "gas" in phase_name_lower:
                classification = "gas"
            elif any(keyword in phase_name_lower for keyword in ["salt", "liquid", "melt"]):
                classification = "salt"
            else:
                classification = "solid"
            
            phase_classifications[phase_name] = classification
        
        # Log the classifications
        salt_phases = [p for p, c in phase_classifications.items() if c == "salt"]
        gas_phases = [p for p, c in phase_classifications.items() if c == "gas"]
        solid_phases = [p for p, c in phase_classifications.items() if c == "solid"]
        
        logger.info(f"Classified {len(salt_phases)} salt phases: {salt_phases}")
        logger.info(f"Classified {len(gas_phases)} gas phases: {gas_phases}")
        logger.info(f"Classified {len(solid_phases)} solid phases: {solid_phases}")
        
        self.phase_classifications = phase_classifications
        return phase_classifications
    
    def extract_species_data(self, timestep_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Extracts information only for present species from a timestep's data.
        
        Args:
            timestep_data (Dict[str, Any]): Data for a single timestep
            
        Returns:
            Dict[str, Dict[str, Any]]: Filtered data containing only present species
        """
        filtered_data = {}
        
        json_data = timestep_data.get("json_data")
        if not json_data:
            return filtered_data
        
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
                
                # Get the classification for this phase
                phase_classification = self.phase_classifications.get(phase_name, "unknown")
                
                # Initialize the phase in filtered data if not already present
                if phase_name not in filtered_data:
                    filtered_data[phase_name] = {
                        "classification": phase_classification,
                        "type": "solution",
                        "species": {}
                    }
                
                # Extract only species with non-zero mole fractions
                species_data = phase_data["species"]
                for species_name, species_info in species_data.items():
                    mole_fraction = species_info.get("mole fraction")
                    if mole_fraction and mole_fraction > 0:
                        filtered_data[phase_name]["species"][species_name] = {
                            "mole_fraction": mole_fraction
                        }
            
            # Process pure condensed phases
            pure_phases = data_point.get("pure condensed phases", {})
            for phase_name, phase_data in pure_phases.items():
                # Get the classification for this phase
                phase_classification = self.phase_classifications.get(phase_name, "unknown")
                
                # Initialize the phase in filtered data if not already present
                if phase_name not in filtered_data:
                    filtered_data[phase_name] = {
                        "classification": phase_classification,
                        "type": "pure",
                        "moles": phase_data.get("moles", 0)
                    }
        
        return filtered_data
    
    def generate_condensed_report(self) -> Dict[str, Dict[str, Any]]:
        """
        Creates a condensed report of all Thermochimica output data.
        
        Returns:
            Dict[str, Dict[str, Any]]: Condensed report with phase classifications and filtered data
        """
        logger.info("Generating condensed report")
        
        # Ensure phases have been classified
        if not self.phase_classifications:
            self.classify_phases()
        
        condensed_report = {}
        
        # Process each timestep
        for timestep, data in self.thermochimica_data.items():
            filtered_data = self.extract_species_data(data)
            
            if filtered_data:
                condensed_report[str(timestep)] = filtered_data
        
        logger.info(f"Generated condensed report for {len(condensed_report)} timesteps")
        self.condensed_report = condensed_report
        return condensed_report
    
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
        return output_path
    
    def get_phase_summary(self) -> Tuple[List[str], List[str], List[str]]:
        """
        Get summary lists of classified phases.
        
        Returns:
            Tuple[List[str], List[str], List[str]]: Lists of salt, gas, and solid phases
        """
        if not self.phase_classifications:
            self.classify_phases()
            
        salt_phases = [p for p, c in self.phase_classifications.items() if c == "salt"]
        gas_phases = [p for p, c in self.phase_classifications.items() if c == "gas"]
        solid_phases = [p for p, c in self.phase_classifications.items() if c == "solid"]
        
        return salt_phases, gas_phases, solid_phases
    
    def get_species_summary(self) -> Dict[str, List[str]]:
        """
        Get a summary of all species found in each phase type.
        
        Returns:
            Dict[str, List[str]]: Dictionary mapping phase types to lists of species
        """
        if not self.condensed_report:
            self.generate_condensed_report()
            
        species_by_type = {
            "salt": set(),
            "gas": set(),
            "solid": set()
        }
        
        for timestep_data in self.condensed_report.values():
            for phase_name, phase_data in timestep_data.items():
                classification = phase_data.get("classification", "unknown")
                
                if classification not in species_by_type:
                    continue
                    
                if "species" in phase_data:
                    species_by_type[classification].update(phase_data["species"].keys())
        
        # Convert sets to sorted lists
        return {k: sorted(v) for k, v in species_by_type.items()}


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
    
    # Get phase summaries
    salt_phases, gas_phases, solid_phases = report_generator.get_phase_summary()
    logger.info(f"Salt phases: {salt_phases}")
    logger.info(f"Gas phases: {gas_phases}")
    logger.info(f"Solid phases: {solid_phases}")
    
    # Get species summaries
    species_summary = report_generator.get_species_summary()
    for phase_type, species_list in species_summary.items():
        logger.info(f"{phase_type.capitalize()} species: {len(species_list)}")
        if len(species_list) > 0:
            logger.info(f"Sample species: {species_list[:5]}...")
    
    # Save the condensed report
    output_path = report_generator.save_condensed_report(args.output_dir)
    logger.info(f"Condensed report saved to {output_path}")


if __name__ == "__main__":
    main()