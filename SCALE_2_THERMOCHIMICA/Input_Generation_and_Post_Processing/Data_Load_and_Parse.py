import os
import json
import logging
from typing import Dict, Any, Tuple, List, Optional, Set

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Post-Processor')

class DataLoaderParser:
    """
    Component 1: Data Loader and Parser
    Loads and parses all input files for the Post-Processing module.
    
    Handles:
    - ThEIRENE_FuelSalt_processed_elements.json: Contains element data with atom densities and mole percentages
    - surrogate_vector.json: Contains surrogate mappings with atom densities and contribution percentages
    - Thermochimica output files: Contains thermodynamic calculation results for each timestep
    """
    
    def __init__(self, base_directory: str):
        """
        Initialize the Data Loader and Parser.
        
        Args:
            base_directory (str): Base directory containing all input files
        """
        self.base_directory = base_directory
        self.fuel_salt_data = None
        self.surrogate_vector = None
        self.thermochimica_data = None
        
    def load_all_data(self) -> Tuple[Dict, Dict, Dict]:
        """
        Load all required data from the base directory.
        
        Returns:
            Tuple[Dict, Dict, Dict]: Fuel salt data, surrogate vector data, and thermochimica data
        """
        logger.info(f"Loading data from {self.base_directory}")
        
        # Load fuel salt data
        fuel_salt_path = os.path.join(self.base_directory, "ThEIRENE_FuelSalt_processed_elements.json")
        self.fuel_salt_data = self.load_fuel_salt_data(fuel_salt_path)
        
        # Load surrogate vector
        surrogate_path = os.path.join(self.base_directory, "surrogate_vector.json")
        self.surrogate_vector = self.load_surrogate_vector(surrogate_path)
        
        # Load thermochimica outputs
        self.thermochimica_data = self.load_thermochimica_outputs(self.base_directory)
        
        return self.fuel_salt_data, self.surrogate_vector, self.thermochimica_data
    
    def load_fuel_salt_data(self, file_path: str) -> Dict:
        """
        Load and parse the ThEIRENE_FuelSalt_processed_elements.json file.
        This file contains element data with atom densities and mole percentages,
        as well as isotopic breakdown (surrogate_percentages).
        
        Expected structure:
        {
            "surrogate_vector": {
                "0": {
                    "element_name": {
                        "atom_density": float,
                        "mole_percent": float
                    },
                    ...
                }
            },
            "surrogate_percentages": {
                "0": {
                    "element_name": {
                        "isotope_name": {
                            "atom_density": float,
                            "contribution_percentage": float
                        },
                        ...
                    },
                    ...
                }
            }
        }
        
        Args:
            file_path (str): Path to the fuel salt data file
            
        Returns:
            Dict: Structured dictionary of fuel salt data
        """
        logger.info(f"Loading fuel salt data from {file_path}")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Validate the structure
            if not self._validate_fuel_salt_structure(data):
                logger.warning("Fuel salt data has an unexpected structure")
            
            logger.info("Fuel salt data loaded successfully")
            return data
        except FileNotFoundError:
            logger.error(f"Fuel salt data file not found: {file_path}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Error parsing fuel salt data file: {file_path}")
            return {}
    
    def _validate_fuel_salt_structure(self, data: Dict) -> bool:
        """
        Validate the structure of the fuel salt data.
        
        Args:
            data (Dict): The fuel salt data to validate
            
        Returns:
            bool: True if the structure is valid, False otherwise
        """
        if not isinstance(data, dict):
            return False
        
        # Check for required top-level keys
        required_keys = ["surrogate_vector", "surrogate_percentages"]
        if not all(key in data for key in required_keys):
            return False
        
        # Check for timestep "0" in surrogate_vector
        if "0" not in data["surrogate_vector"]:
            return False
        
        # Check for timestep "0" in surrogate_percentages
        if "0" not in data["surrogate_percentages"]:
            return False
        
        # Validate that elements in surrogate_vector match those in surrogate_percentages
        elements_in_vector = set(data["surrogate_vector"]["0"].keys())
        elements_in_percentages = set(data["surrogate_percentages"]["0"].keys())
        
        if elements_in_vector != elements_in_percentages:
            logger.warning("Elements in surrogate_vector and surrogate_percentages do not match")
            mismatched_elements = elements_in_vector.symmetric_difference(elements_in_percentages)
            logger.warning(f"Mismatched elements: {mismatched_elements}")
        
        return True
    
    def load_surrogate_vector(self, file_path: str) -> Dict:
        """
        Load and parse the surrogate_vector.json file.
        This file contains surrogate mappings with atom densities and contribution percentages.
        
        Expected structure:
        {
            "surrogate_vector": {
                "0": {
                    "surrogate_name": {
                        "atom_density": float,
                        "mole_percent": float
                    },
                    ...
                }
            },
            "surrogate_percentages": {
                "0": {
                    "surrogate_name": {
                        "element_name": {
                            "atom_density": float,
                            "contribution_percentage": float
                        },
                        ...
                    },
                    ...
                }
            }
        }
        
        Args:
            file_path (str): Path to the surrogate vector file
            
        Returns:
            Dict: Structured dictionary of surrogate vector data
        """
        logger.info(f"Loading surrogate vector from {file_path}")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Validate the structure
            if not self._validate_surrogate_vector_structure(data):
                logger.warning("Surrogate vector has an unexpected structure")
            
            logger.info("Surrogate vector loaded successfully")
            return data
        except FileNotFoundError:
            logger.error(f"Surrogate vector file not found: {file_path}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Error parsing surrogate vector file: {file_path}")
            return {}
    
    def _validate_surrogate_vector_structure(self, data: Dict) -> bool:
        """
        Validate the structure of the surrogate vector data.
        
        Args:
            data (Dict): The surrogate vector data to validate
            
        Returns:
            bool: True if the structure is valid, False otherwise
        """
        if not isinstance(data, dict):
            return False
        
        # Check for required top-level keys
        required_keys = ["surrogate_vector", "surrogate_percentages"]
        if not all(key in data for key in required_keys):
            return False
        
        # Check for timestep "0" in surrogate_vector
        if "0" not in data["surrogate_vector"]:
            return False
        
        # Check for timestep "0" in surrogate_percentages
        if "0" not in data["surrogate_percentages"]:
            return False
        
        # Validate that surrogates in surrogate_vector match those in surrogate_percentages
        surrogates_in_vector = set(data["surrogate_vector"]["0"].keys())
        surrogates_in_percentages = set(data["surrogate_percentages"]["0"].keys())
        
        if surrogates_in_vector != surrogates_in_percentages:
            logger.warning("Surrogates in surrogate_vector and surrogate_percentages do not match")
            mismatched_surrogates = surrogates_in_vector.symmetric_difference(surrogates_in_percentages)
            logger.warning(f"Mismatched surrogates: {mismatched_surrogates}")
        
        return True
    
    def load_thermochimica_outputs(self, base_directory: str) -> Dict[int, Dict[str, Any]]:
        """
        Load all Thermochimica output files from the directory structure.
        
        File structure:
        base_directory/
        └── tc_inputs/
            ├── timestep_0/
            │   ├── ThEIRNE_Cycle_t0.ti       # Input file
            │   ├── ThEIRNE_Cycle_t0.log      # Text output from run
            │   └── ThEIRNE_Cycle_t0.json     # Primary data source for this timestep
            ├── timestep_1/
            │   ├── ThEIRNE_Cycle_t1.ti
            │   ├── ThEIRNE_Cycle_t1.log
            │   └── ThEIRNE_Cycle_t1.json
            └── ... (timestep_2 through timestep_366)
        
        Args:
            base_directory (str): Base directory containing tc_inputs/timestep_X folders
            
        Returns:
            Dict[int, Dict[str, Any]]: Dictionary mapping timesteps to their respective output data
        """
        logger.info("Loading Thermochimica outputs")
        thermochimica_data = {}
        
        # Define the expected directory structure
        tc_inputs_dir = os.path.join(base_directory, "tc_inputs")
        
        if not os.path.exists(tc_inputs_dir):
            logger.error(f"tc_inputs directory not found: {tc_inputs_dir}")
            return thermochimica_data
        
        # Iterate through all subdirectories
        for subdir in os.listdir(tc_inputs_dir):
            if not subdir.startswith("timestep_"):
                continue
            
            # Extract timestep number
            try:
                timestep = int(subdir.split("_")[1])
            except (IndexError, ValueError):
                logger.warning(f"Could not parse timestep from directory name: {subdir}")
                continue
            
            timestep_dir = os.path.join(tc_inputs_dir, subdir)
            
            # Find relevant files in this timestep directory
            json_file = None
            log_file = None
            input_file = None
            
            for file in os.listdir(timestep_dir):
                if file.endswith(".json"):
                    json_file = os.path.join(timestep_dir, file)
                elif file.endswith(".log"):
                    log_file = os.path.join(timestep_dir, file)
                elif file.endswith(".ti"):
                    input_file = os.path.join(timestep_dir, file)
            
            # Load data from the files
            json_data = self._load_json_file(json_file) if json_file else None
            log_data = self._load_log_file(log_file) if log_file else None
            input_data = self._load_log_file(input_file) if input_file else None
            
            if json_data or log_data:
                thermochimica_data[timestep] = {
                    "json_data": json_data,
                    "log_data": log_data,
                    "input_data": input_data
                }
                
                # Validate the JSON structure if it exists
                if json_data:
                    if not self._validate_thermochimica_json(json_data):
                        logger.warning(f"Thermochimica JSON at timestep {timestep} has an unexpected structure")
        
        logger.info(f"Loaded data for {len(thermochimica_data)} timesteps")
        return thermochimica_data
    
    def _validate_thermochimica_json(self, data: Dict) -> bool:
        """
        Validate the structure of a Thermochimica JSON file.
        
        Args:
            data (Dict): The Thermochimica JSON data to validate
            
        Returns:
            bool: True if the structure is valid, False otherwise
        """
        # Check if the data is a dictionary
        if not isinstance(data, dict):
            return False
        
        # Thermochimica JSON files have numeric keys for each data point
        # Check if at least one key is a numeric string
        has_numeric_key = False
        for key in data.keys():
            if key.isdigit():
                has_numeric_key = True
                
                # Check the structure of this data point
                data_point = data[key]
                if not isinstance(data_point, dict):
                    return False
                
                # Check for required sections in the data point
                required_sections = ["solution phases", "pure condensed phases", "elements"]
                if not all(section in data_point for section in required_sections):
                    return False
                
                # If we found at least one valid data point, break
                break
        
        return has_numeric_key
    
    def _load_json_file(self, file_path: str) -> Optional[Dict]:
        """
        Load and parse a JSON file.
        
        Args:
            file_path (str): Path to the JSON file
            
        Returns:
            Optional[Dict]: Parsed JSON data or None if there was an error
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data
        except FileNotFoundError:
            logger.error(f"JSON file not found: {file_path}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Error parsing JSON file: {file_path}")
            return None
    
    def _load_log_file(self, file_path: str) -> Optional[str]:
        """
        Load a log file.
        
        Args:
            file_path (str): Path to the log file
            
        Returns:
            Optional[str]: Contents of the log file or None if there was an error
        """
        try:
            with open(file_path, 'r') as f:
                data = f.read()
            return data
        except FileNotFoundError:
            logger.error(f"Log file not found: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return None
    
    def verify_data_integrity(self) -> bool:
        """
        Verify that all required data has been loaded.
        
        Returns:
            bool: True if all data is present, False otherwise
        """
        if not self.fuel_salt_data:
            logger.error("Fuel salt data not loaded")
            return False
        
        if not self.surrogate_vector:
            logger.error("Surrogate vector not loaded")
            return False
        
        if not self.thermochimica_data:
            logger.error("Thermochimica data not loaded")
            return False
        
        return True

    def get_timesteps(self) -> List[int]:
        """
        Get a sorted list of all timesteps.
        
        Returns:
            List[int]: Sorted list of timesteps
        """
        if not self.thermochimica_data:
            return []
        
        return sorted(self.thermochimica_data.keys())

    def save_processed_data(self, output_directory: str) -> None:
        """
        Save the processed data to the output directory.
        
        Args:
            output_directory (str): Directory to save the processed data
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Save the loaded data for later use
        if self.fuel_salt_data:
            with open(os.path.join(output_directory, "processed_fuel_salt_data.json"), 'w') as f:
                json.dump(self.fuel_salt_data, f, indent=2)
        
        if self.surrogate_vector:
            with open(os.path.join(output_directory, "processed_surrogate_vector.json"), 'w') as f:
                json.dump(self.surrogate_vector, f, indent=2)
        # Print statistics about loaded data
        if fuel_salt_data:
            print(f"Fuel salt data contains {len(fuel_salt_data.get('surrogate_vector', {}).get('0', {}))} elements")

        if surrogate_vector:
            print(f"Surrogate vector contains {len(surrogate_vector.get('surrogate_vector', {}).get('0', {}))} surrogates")

        if thermochimica_data:
            print(f"Thermochimica data contains {len(thermochimica_data)} timesteps")
        # Save a summary of the thermochimica data
        if self.thermochimica_data:
            thermochimica_summary = {
                timestep: {
                    "has_json": bool(data.get("json_data")),
                    "has_log": bool(data.get("log_data"))
                }
                for timestep, data in self.thermochimica_data.items()
            }
            
            with open(os.path.join(output_directory, "thermochimica_data_summary.json"), 'w') as f:
                json.dump(thermochimica_summary, f, indent=2)


def main():
    """
    Main function to demonstrate the usage of the DataLoaderParser.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Post-Processor Data Loader and Parser')
    parser.add_argument('input_dir', help='Directory containing input files')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
    args = parser.parse_args()
    
    # Create an instance of the DataLoaderParser
    loader = DataLoaderParser(args.input_dir)
    
    # Load all data
    fuel_salt_data, surrogate_vector, thermochimica_data = loader.load_all_data()
    
    # Verify data integrity
    if loader.verify_data_integrity():
        logger.info("All data loaded successfully")
        
        # Get the list of timesteps
        timesteps = loader.get_timesteps()
        logger.info(f"Found {len(timesteps)} timesteps: {timesteps[:5]}...")
        
        # Save the processed data
        loader.save_processed_data(args.output_dir)
        logger.info(f"Processed data saved to {args.output_dir}")
    else:
        logger.error("Data loading failed")


if __name__ == "__main__":
    main()