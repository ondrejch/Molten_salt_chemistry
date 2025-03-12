import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Phase-Specific-Data-Processor')

class PhaseSpecificDataProcessor:
    """
    Component 5: Phase-Specific Data Processor
    Generates phase-specific JSON files with surrogate and mole percentages.
    
    Main functions:
    - calculate_surrogate_mole_percent: Calculates surrogate mole percentages
    - calculate_phase_mole_percent: Calculates phase mole percentages
    - generate_phase_json: Creates phase-specific JSON file
    """
    
    def __init__(self, condensed_report: Dict[str, Dict[str, Any]], surrogate_vector: Dict[str, Any]):
        """
        Initialize the Phase-Specific Data Processor.
        
        Args:
            condensed_report (Dict[str, Dict[str, Any]]): Condensed Thermochimica report from Component 2
            surrogate_vector (Dict[str, Any]): Surrogate vector data from Component 1
        """
        self.condensed_report = condensed_report
        self.surrogate_vector = surrogate_vector
        self.phase_data = {
            "salt": {},
            "gas": {},
            "solid": {}
        }
    
    def extract_phase_data(self) -> Dict[str, Dict[str, Dict]]:
        """
        Extract data for all phases by type (salt, gas, solid).
        
        Returns:
            Dict[str, Dict[str, Dict]]: Dictionary of phase data by type and timestep
        """
        logger.info("Extracting phase data by type")
        
        result = {
            "salt": {},
            "gas": {},
            "solid": {}
        }
        
        for timestep, timestep_data in self.condensed_report.items():
            # Initialize data structures for this timestep
            for phase_type in result.keys():
                if timestep not in result[phase_type]:
                    result[phase_type][timestep] = {}
            
            # Extract data for each phase in this timestep
            for phase_name, phase_data in timestep_data.items():
                classification = phase_data.get("classification", "unknown")
                
                if classification in result:
                    result[classification][timestep][phase_name] = phase_data
        
        # Log the results
        for phase_type, timestep_data in result.items():
            total_phases = sum(len(phases) for phases in timestep_data.values())
            logger.info(f"Extracted {total_phases} {phase_type} phases across {len(timestep_data)} timesteps")
        
        self.phase_data = result
        return result
    
    def calculate_surrogate_mole_percent(self, timestep: str, phase_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate surrogate mole percentages for a phase.
        
        Args:
            timestep (str): The timestep to process
            phase_data (Dict[str, Any]): Data for a specific phase
            
        Returns:
            Dict[str, float]: Dictionary mapping surrogate names to their mole percentages
        """
        # We need to get surrogate information from the surrogate_vector
        surrogate_info = self.surrogate_vector.get("surrogate_vector", {}).get("0", {})
        
        # For solution phases, we need to map species to surrogates
        # This mapping would typically be provided or derived from chemical formulas
        # Here we'll use a simplified approach based on name matching
        surrogate_mole_percents = {}
        
        if "species" in phase_data:
            # Solution phase
            species_data = phase_data["species"]
            
            for species_name, species_info in species_data.items():
                mole_fraction = species_info.get("mole_fraction", 0)
                
                # Simplified mapping: extract surrogate prefix from species name
                # This is a heuristic and might need adjustment based on actual naming conventions
                surrogate_prefix = species_name.split("[")[0].strip() if "[" in species_name else species_name
                
                # Add to the surrogate mole percent
                if surrogate_prefix in surrogate_mole_percents:
                    surrogate_mole_percents[surrogate_prefix] += mole_fraction
                else:
                    surrogate_mole_percents[surrogate_prefix] = mole_fraction
                    
        elif "moles" in phase_data:
            # Pure condensed phase - the phase name itself is the surrogate
            moles = phase_data.get("moles", 0)
            
            # Extract the surrogate from the phase name (simplified approach)
            surrogate_name = phase_data.get("surrogate_name", phase_data.get("phase_name", "unknown"))
            
            surrogate_mole_percents[surrogate_name] = 1.0  # 100% of this phase is this surrogate
        
        # Normalize to percentages
        total_moles = sum(surrogate_mole_percents.values())
        if total_moles > 0:
            for surrogate in surrogate_mole_percents:
                surrogate_mole_percents[surrogate] = (surrogate_mole_percents[surrogate] / total_moles) * 100
        
        return surrogate_mole_percents
    
    def calculate_phase_mole_percent(self, phase_type: str, timestep: str) -> Dict[str, float]:
        """
        Calculate phase mole percentages within a given phase type for a timestep.
        
        Args:
            phase_type (str): The phase type (salt, gas, solid)
            timestep (str): The timestep to process
            
        Returns:
            Dict[str, float]: Dictionary mapping phase names to their mole percentages
        """
        phase_mole_percents = {}
        
        # Get all phases of this type for the timestep
        timestep_phases = self.phase_data.get(phase_type, {}).get(timestep, {})
        
        # Calculate total moles across all phases of this type
        total_moles = 0
        for phase_name, phase_data in timestep_phases.items():
            if "species" in phase_data:
                # For solution phases, sum the mole fractions of all species
                # This is a simplification, as mole fractions are already normalized within a phase
                species_sum = sum(species_info.get("mole_fraction", 0) 
                                 for species_info in phase_data["species"].values())
                total_moles += species_sum
            elif "moles" in phase_data:
                # For pure condensed phases, use the moles value
                total_moles += phase_data.get("moles", 0)
        
        # Calculate percentage for each phase
        if total_moles > 0:
            for phase_name, phase_data in timestep_phases.items():
                if "species" in phase_data:
                    species_sum = sum(species_info.get("mole_fraction", 0) 
                                     for species_info in phase_data["species"].values())
                    phase_mole_percents[phase_name] = (species_sum / total_moles) * 100
                elif "moles" in phase_data:
                    phase_mole_percents[phase_name] = (phase_data.get("moles", 0) / total_moles) * 100
        
        return phase_mole_percents
    
    def generate_phase_json(self, phase_type: str) -> Dict[str, Dict[str, Any]]:
        """
        Create a phase-specific JSON structure.
        
        Args:
            phase_type (str): The phase type (salt, gas, solid)
            
        Returns:
            Dict[str, Dict[str, Any]]: Phase-specific JSON structure
        """
        logger.info(f"Generating {phase_type} phase JSON")
        
        phase_json = {}
        
        # Process each timestep
        for timestep in sorted(self.condensed_report.keys(), key=int):
            # Calculate phase mole percentages for this timestep
            phase_mole_percents = self.calculate_phase_mole_percent(phase_type, timestep)
            
            timestep_data = {}
            
            # Process each phase in this timestep
            for phase_name, phase_data in self.phase_data.get(phase_type, {}).get(timestep, {}).items():
                # Calculate surrogate mole percentages for this phase
                surrogate_mole_percents = self.calculate_surrogate_mole_percent(timestep, phase_data)
                
                # Get the phase percentage
                phase_percent = phase_mole_percents.get(phase_name, 0)
                
                # Build the phase entry
                phase_entry = {
                    "phase_percent": phase_percent,
                    "surrogate_mole_percent": surrogate_mole_percents
                }
                
                # Add additional data from the original phase info
                if "type" in phase_data:
                    phase_entry["type"] = phase_data["type"]
                
                if "species" in phase_data:
                    # For solution phases, include species information
                    phase_entry["species"] = {}
                    for species_name, species_info in phase_data["species"].items():
                        phase_entry["species"][species_name] = {
                            "mole_fraction": species_info.get("mole_fraction", 0)
                        }
                elif "moles" in phase_data:
                    # For pure condensed phases, include moles information
                    phase_entry["moles"] = phase_data.get("moles", 0)
                
                timestep_data[phase_name] = phase_entry
            
            if timestep_data:
                phase_json[timestep] = timestep_data
        
        logger.info(f"Generated {phase_type} phase JSON with {len(phase_json)} timesteps")
        return phase_json
    
    def process_all_phases(self) -> Tuple[Dict, Dict, Dict]:
        """
        Process all phase types and generate their respective JSON structures.
        
        Returns:
            Tuple[Dict, Dict, Dict]: Tuple of salt, gas, and solid phase JSON structures
        """
        logger.info("Processing all phases")
        
        # Extract phase data by type
        self.extract_phase_data()
        
        # Generate JSON for each phase type
        salt_json = self.generate_phase_json("salt")
        gas_json = self.generate_phase_json("gas")
        solid_json = self.generate_phase_json("solid")
        
        return salt_json, gas_json, solid_json
    
    def save_phase_jsons(self, output_directory: str) -> Dict[str, str]:
        """
        Save phase-specific JSON files.
        
        Args:
            output_directory (str): Directory to save the JSON files
            
        Returns:
            Dict[str, str]: Dictionary mapping phase types to their output file paths
        """
        logger.info(f"Saving phase JSON files to {output_directory}")
        
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Process all phases
        salt_json, gas_json, solid_json = self.process_all_phases()
        
        # Save the JSON files
        output_paths = {}
        
        salt_path = os.path.join(output_directory, "Salt.json")
        with open(salt_path, 'w') as f:
            json.dump(salt_json, f, indent=2)
        output_paths["salt"] = salt_path
        
        gas_path = os.path.join(output_directory, "Gas.json")
        with open(gas_path, 'w') as f:
            json.dump(gas_json, f, indent=2)
        output_paths["gas"] = gas_path
        
        solid_path = os.path.join(output_directory, "Solids.json")
        with open(solid_path, 'w') as f:
            json.dump(solid_json, f, indent=2)
        output_paths["solid"] = solid_path
        
        logger.info(f"Saved phase JSON files: {', '.join(output_paths.values())}")
        return output_paths


def main():
    """
    Main function to demonstrate the usage of the PhaseSpecificDataProcessor.
    """
    import argparse
    from Condensed_Report_generator import CondensedReportGenerator
    from Data_Load_and_Parse import DataLoaderParser
    
    parser = argparse.ArgumentParser(description='Phase-Specific Data Processor')
    parser.add_argument('input_dir', help='Directory containing input files')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
    args = parser.parse_args()
    
    # Load the data using DataLoaderParser from Component 1
    loader = DataLoaderParser(args.input_dir)
    fuel_salt_data, surrogate_vector, thermochimica_data = loader.load_all_data()
    
    # Generate condensed report using CondensedReportGenerator from Component 2
    report_generator = CondensedReportGenerator(thermochimica_data)
    condensed_report = report_generator.generate_condensed_report()
    
    # Create an instance of the PhaseSpecificDataProcessor
    processor = PhaseSpecificDataProcessor(condensed_report, surrogate_vector)
    
    # Save the phase-specific JSON files
    output_paths = processor.save_phase_jsons(args.output_dir)
    
    # Log the output paths
    for phase_type, path in output_paths.items():
        logger.info(f"{phase_type.capitalize()} phase data saved to {path}")


if __name__ == "__main__":
    main()