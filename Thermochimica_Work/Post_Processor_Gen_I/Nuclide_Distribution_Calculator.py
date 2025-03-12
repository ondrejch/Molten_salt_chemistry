import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Set

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Nuclide-Distribution-Calculator')

class NuclideDistributionCalculator:
    """
    Component 6: Nuclide Distribution Calculator
    Back-calculates nuclide distributions in each phase using surrogate data.
    
    Main functions:
    - calculate_surrogate_sum: Calculates surrogate sum per formula
    - calculate_total_moles_surrogate: Calculates total moles of surrogate
    - calculate_surrogate_phase_percent: Calculates surrogate phase percentages
    - calculate_element_mole_percent: Calculates element mole percentages 
    - calculate_element_atom_density: Calculates element atom densities
    - calculate_nuclide_atom_density: Calculates nuclide atom densities
    - generate_nuclide_json: Creates phase-specific nuclide JSON file
    """
    
    def __init__(
        self, 
        phase_specific_data: Dict[str, Dict[str, Any]], 
        fuel_salt_data: Dict[str, Any], 
        surrogate_vector: Dict[str, Any],
        phase_type: str
    ):
        """
        Initialize the Nuclide Distribution Calculator.
        
        Args:
            phase_specific_data (Dict[str, Dict[str, Any]]): Phase-specific data from Component 5
            fuel_salt_data (Dict[str, Any]): Fuel salt data from Component 1
            surrogate_vector (Dict[str, Any]): Surrogate vector data from Component 1
            phase_type (str): Type of phase (salt, gas, solid)
        """
        self.phase_specific_data = phase_specific_data
        self.fuel_salt_data = fuel_salt_data
        self.surrogate_vector = surrogate_vector
        self.phase_type = phase_type
        self.nuclide_data = {}
    
    def calculate_surrogate_sum(self, timestep: str) -> Dict[str, float]:
        """
        Calculate the sum of surrogate mole percentages across all phases for a timestep.
        
        Args:
            timestep (str): The timestep to process
            
        Returns:
            Dict[str, float]: Dictionary mapping surrogate names to their sums
        """
        surrogate_sums = {}
        
        # Get all phases for this timestep
        timestep_data = self.phase_specific_data.get(timestep, {})
        
        # Calculate sum of surrogate mole percentages across all phases
        for phase_name, phase_data in timestep_data.items():
            # Get surrogate mole percentages
            surrogate_mole_percents = phase_data.get("surrogate_mole_percent", {})
            
            # Get the phase percentage
            phase_percent = phase_data.get("phase_percent", 0)
            
            # For each surrogate, add its contribution to the sum
            for surrogate_name, mole_percent in surrogate_mole_percents.items():
                # Calculate the weighted contribution of this surrogate in this phase
                contribution = mole_percent * phase_percent / 100.0
                
                if surrogate_name in surrogate_sums:
                    surrogate_sums[surrogate_name] += contribution
                else:
                    surrogate_sums[surrogate_name] = contribution
        
        return surrogate_sums
    
    def calculate_total_moles_surrogate(self, surrogate_sums: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate total moles of each surrogate.
        
        Args:
            surrogate_sums (Dict[str, float]): Dictionary mapping surrogate names to their sums
            
        Returns:
            Dict[str, float]: Dictionary mapping surrogate names to their total moles
        """
        total_moles = {}
        
        # Get surrogate information from the surrogate_vector
        surrogate_info = self.surrogate_vector.get("surrogate_vector", {}).get("0", {})
        
        # For each surrogate, calculate total moles
        for surrogate_name, sum_value in surrogate_sums.items():
            # Get surrogate atom density from surrogate_vector
            surrogate_data = surrogate_info.get(surrogate_name, {})
            atom_density = surrogate_data.get("atom_density", 0)
            
            # Calculate total moles
            total_moles[surrogate_name] = sum_value * atom_density / 100.0
        
        return total_moles
    
    def calculate_surrogate_phase_percent(
        self, 
        timestep: str, 
        surrogate_sums: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate surrogate phase percentages.
        
        Args:
            timestep (str): The timestep to process
            surrogate_sums (Dict[str, float]): Dictionary mapping surrogate names to their sums
            
        Returns:
            Dict[str, Dict[str, float]]: Dictionary mapping phase names to surrogate percentages
        """
        surrogate_phase_percents = {}
        
        # Get all phases for this timestep
        timestep_data = self.phase_specific_data.get(timestep, {})
        
        # Calculate surrogate phase percentages for each phase
        for phase_name, phase_data in timestep_data.items():
            # Get surrogate mole percentages
            surrogate_mole_percents = phase_data.get("surrogate_mole_percent", {})
            
            # Get the phase percentage
            phase_percent = phase_data.get("phase_percent", 0)
            
            # Calculate surrogate phase percentages
            surrogate_phase_percents[phase_name] = {}
            
            for surrogate_name, mole_percent in surrogate_mole_percents.items():
                # Calculate the percentage of this surrogate that is in this phase
                if surrogate_name in surrogate_sums and surrogate_sums[surrogate_name] > 0:
                    contribution = mole_percent * phase_percent / 100.0
                    phase_percent_of_surrogate = (contribution / surrogate_sums[surrogate_name]) * 100.0
                    surrogate_phase_percents[phase_name][surrogate_name] = phase_percent_of_surrogate
        
        return surrogate_phase_percents
    
    def calculate_element_mole_percent(
        self, 
        surrogate_phase_percents: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate element mole percentages.
        
        Args:
            surrogate_phase_percents (Dict[str, Dict[str, float]]): Dictionary mapping phase names to surrogate percentages
            
        Returns:
            Dict[str, Dict[str, float]]: Dictionary mapping phase names to element mole percentages
        """
        element_mole_percents = {}
        
        # Get surrogate-to-element mapping from surrogate_vector
        surrogate_percentages = self.surrogate_vector.get("surrogate_percentages", {}).get("0", {})
        
        # Calculate element mole percentages for each phase
        for phase_name, surrogate_percents in surrogate_phase_percents.items():
            element_mole_percents[phase_name] = {}
            
            for surrogate_name, phase_percent in surrogate_percents.items():
                # Get element contributions for this surrogate
                surrogate_data = surrogate_percentages.get(surrogate_name, {})
                
                for element_name, element_data in surrogate_data.items():
                    # Get contribution percentage
                    contribution_percentage = element_data.get("contribution_percentage", 0)
                    
                    # Calculate element mole percentage
                    element_mole_percent = phase_percent * contribution_percentage / 100.0
                    
                    # Add to the element mole percent
                    if element_name in element_mole_percents[phase_name]:
                        element_mole_percents[phase_name][element_name] += element_mole_percent
                    else:
                        element_mole_percents[phase_name][element_name] = element_mole_percent
        
        return element_mole_percents
    
    def calculate_element_atom_density(
        self, 
        element_mole_percents: Dict[str, Dict[str, float]],
        total_moles_surrogate: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate element atom densities.
        
        Args:
            element_mole_percents (Dict[str, Dict[str, float]]): Dictionary mapping phase names to element mole percentages
            total_moles_surrogate (Dict[str, float]): Dictionary mapping surrogate names to their total moles
            
        Returns:
            Dict[str, Dict[str, float]]: Dictionary mapping phase names to element atom densities
        """
        element_atom_densities = {}
        
        # Get surrogate-to-element mapping from surrogate_vector
        surrogate_percentages = self.surrogate_vector.get("surrogate_percentages", {}).get("0", {})
        
        # Get element atom densities from fuel_salt_data
        fuel_salt_elements = self.fuel_salt_data.get("surrogate_vector", {}).get("0", {})
        
        # Calculate element atom densities for each phase
        for phase_name, element_percents in element_mole_percents.items():
            element_atom_densities[phase_name] = {}
            
            for element_name, mole_percent in element_percents.items():
                # Get element atom density from fuel_salt_data
                element_data = fuel_salt_elements.get(element_name, {})
                atom_density = element_data.get("atom_density", 0)
                
                # Calculate element atom density in this phase
                phase_atom_density = atom_density * mole_percent / 100.0
                
                element_atom_densities[phase_name][element_name] = phase_atom_density
        
        return element_atom_densities
    
    def calculate_nuclide_atom_density(
        self, 
        element_atom_densities: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, Dict[str, float]]]:
        """
        Calculate nuclide atom densities.
        
        Args:
            element_atom_densities (Dict[str, Dict[str, float]]): Dictionary mapping phase names to element atom densities
            
        Returns:
            Dict[str, Dict[str, Dict[str, float]]]: Dictionary mapping phase names to element and nuclide atom densities
        """
        nuclide_atom_densities = {}
        
        # Get element-to-nuclide mapping from fuel_salt_data
        element_percentages = self.fuel_salt_data.get("surrogate_percentages", {}).get("0", {})
        
        # Calculate nuclide atom densities for each phase
        for phase_name, element_densities in element_atom_densities.items():
            nuclide_atom_densities[phase_name] = {}
            
            for element_name, atom_density in element_densities.items():
                # Get nuclide contributions for this element
                element_data = element_percentages.get(element_name, {})
                
                # Initialize the element entry
                nuclide_atom_densities[phase_name][element_name] = {
                    "atom_density": atom_density,
                    "nuclides": {}
                }
                
                # Calculate nuclide atom densities
                for nuclide_name, nuclide_data in element_data.items():
                    # Get contribution percentage
                    contribution_percentage = nuclide_data.get("contribution_percentage", 0)
                    
                    # Calculate nuclide atom density
                    nuclide_atom_density = atom_density * contribution_percentage / 100.0
                    
                    # Add to the nuclide atom densities
                    nuclide_atom_densities[phase_name][element_name]["nuclides"][nuclide_name] = {
                        "atom_density": nuclide_atom_density,
                        "contribution_percentage": contribution_percentage
                    }
        
        return nuclide_atom_densities
    
    def generate_nuclide_json(self, timestep: str) -> Dict[str, Any]:
        """
        Create a phase-specific nuclide JSON structure for a timestep.
        
        Args:
            timestep (str): The timestep to process
            
        Returns:
            Dict[str, Any]: Phase-specific nuclide JSON structure
        """
        # Calculate surrogate sums
        surrogate_sums = self.calculate_surrogate_sum(timestep)
        
        # Calculate total moles of each surrogate
        total_moles_surrogate = self.calculate_total_moles_surrogate(surrogate_sums)
        
        # Calculate surrogate phase percentages
        surrogate_phase_percents = self.calculate_surrogate_phase_percent(timestep, surrogate_sums)
        
        # Calculate element mole percentages
        element_mole_percents = self.calculate_element_mole_percent(surrogate_phase_percents)
        
        # Calculate element atom densities
        element_atom_densities = self.calculate_element_atom_density(element_mole_percents, total_moles_surrogate)
        
        # Calculate nuclide atom densities
        nuclide_atom_densities = self.calculate_nuclide_atom_density(element_atom_densities)
        
        # Build the JSON structure
        nuclide_json = {
            "timestep": timestep,
            "phase_type": self.phase_type,
            "elements": nuclide_atom_densities
        }
        
        return nuclide_json
    
    def process_all_timesteps(self) -> Dict[str, Dict[str, Any]]:
        """
        Process all timesteps and generate nuclide JSON structures.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping timesteps to their nuclide JSON structures
        """
        logger.info(f"Processing all timesteps for {self.phase_type} phase")
        
        nuclide_data = {}
        
        # Process each timestep
        for timestep in sorted(self.phase_specific_data.keys(), key=int):
            logger.info(f"Processing timestep {timestep}")
            
            try:
                # Generate nuclide JSON for this timestep
                timestep_data = self.generate_nuclide_json(timestep)
                
                # Add to the nuclide data
                nuclide_data[timestep] = timestep_data
            except Exception as e:
                logger.error(f"Error processing timestep {timestep}: {str(e)}")
        
        logger.info(f"Processed {len(nuclide_data)} timesteps for {self.phase_type} phase")
        self.nuclide_data = nuclide_data
        return nuclide_data
    
    def save_nuclide_json(self, output_directory: str) -> str:
        """
        Save phase-specific nuclide JSON file.
        
        Args:
            output_directory (str): Directory to save the JSON file
            
        Returns:
            str: Path to the saved file
        """
        logger.info(f"Saving {self.phase_type} nuclide JSON file")
        
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        
        # Process all timesteps if not already processed
        if not self.nuclide_data:
            self.process_all_timesteps()
        
        # Construct the output file path
        output_filename = f"{self.phase_type.capitalize()}_nuclides.json"
        output_path = os.path.join(output_directory, output_filename)
        
        # Save the JSON file
        with open(output_path, 'w') as f:
            json.dump(self.nuclide_data, f, indent=2)
        
        logger.info(f"Saved {self.phase_type} nuclide JSON file to {output_path}")
        return output_path


def process_all_phase_types(
    phase_data_paths: Dict[str, str],
    fuel_salt_data: Dict[str, Any],
    surrogate_vector: Dict[str, Any],
    output_directory: str
) -> Dict[str, str]:
    """
    Process all phase types and generate their respective nuclide JSON files.
    
    Args:
        phase_data_paths (Dict[str, str]): Dictionary mapping phase types to their data file paths
        fuel_salt_data (Dict[str, Any]): Fuel salt data from Component 1
        surrogate_vector (Dict[str, Any]): Surrogate vector data from Component 1
        output_directory (str): Directory to save the nuclide JSON files
        
    Returns:
        Dict[str, str]: Dictionary mapping phase types to their nuclide JSON file paths
    """
    logger.info("Processing all phase types")
    
    output_paths = {}
    
    # Process each phase type
    for phase_type, data_path in phase_data_paths.items():
        try:
            # Load the phase-specific data
            with open(data_path, 'r') as f:
                phase_data = json.load(f)
                
                # Create a NuclideDistributionCalculator for this phase type
                calculator = NuclideDistributionCalculator(
                    phase_data, fuel_salt_data, surrogate_vector, phase_type
                )
                
                # Process all timesteps and save the nuclide JSON file
                output_path = calculator.save_nuclide_json(output_directory)
                
                # Add to the output paths
                output_paths[phase_type] = output_path
        except Exception as e:
                logger.error(f"Error processing phase type {phase_type}: {str(e)}")
    
    logger.info(f"Processed all phase types, generated output files: {list(output_paths.values())}")
    return output_paths


def main():
    """
    Main function to demonstrate the usage of the Nuclide Distribution Calculator.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Nuclide Distribution Calculator')
    parser.add_argument('input_dir', help='Directory containing input files')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
    args = parser.parse_args()
    
    # Initialize output directory
    output_dir = args.output_dir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Load the fuel salt data and surrogate vector
    from Data_Load_and_Parse import DataLoaderParser
    
    loader = DataLoaderParser(args.input_dir)
    fuel_salt_data, surrogate_vector, _ = loader.load_all_data()
    
    # Define paths to phase data files
    # Assuming they were created by Component 5 and stored in the output directory
    phase_data_paths = {
        "salt": os.path.join(output_dir, "Salt.json"),
        "gas": os.path.join(output_dir, "Gas.json"),
        "solid": os.path.join(output_dir, "Solids.json")
    }
    
    # Process all phase types
    output_paths = process_all_phase_types(
        phase_data_paths, fuel_salt_data, surrogate_vector, output_dir
    )
    
    # Log the output paths
    for phase_type, path in output_paths.items():
        logger.info(f"{phase_type.capitalize()} nuclide data saved to {path}")


if __name__ == "__main__":
    main()