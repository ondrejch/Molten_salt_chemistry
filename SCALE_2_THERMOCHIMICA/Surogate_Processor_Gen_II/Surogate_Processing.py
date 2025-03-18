import json
from typing import Dict, List, Any, Tuple


class SurrogateProcessor:
    """
    Process element data and map to surrogates based on provided mapping configuration.
    
    This class takes a surrogate configuration file and a ThEIRENE element data file,
    and produces a new file with condensed surrogate values and calculated surrogate percentages.
    """
    
    def __init__(self, surrogate_file: str, element_data_file: str):
        """
        Initialize the SurrogateProcessor with input file paths.
        
        Args:
            surrogate_file: Path to the surrogate_and_candidates.json file
            element_data_file: Path to the ThEIRENE_FuelSalt_processed_elements.json file
        """
        self.surrogate_file = surrogate_file
        self.element_data_file = element_data_file
        self.surrogate_config = {}
        self.element_data = {}
        self.surrogate_vector = {}
        self.surrogate_percentages = {}
        
        # Load the surrogate configuration and element data
        self._load_surrogate_config()
        self._load_element_data()
        
    def _load_surrogate_config(self):
        """Load and parse the surrogate configuration file."""
        with open(self.surrogate_file, 'r') as f:
            self.surrogate_config = json.load(f)
        
        # Convert the surrogate mapping to lowercase for consistent comparison
        self.surrogate_mapping = {}
        for surrogate, candidates in self.surrogate_config.items():
            surrogate_lower = surrogate.lower()
            self.surrogate_mapping[surrogate_lower] = [candidate["Symbol"].lower() for candidate in candidates]
            
    def _load_element_data(self):
        """Load and parse the element data file."""
        with open(self.element_data_file, 'r') as f:
            data = json.load(f)
            
            # Handle the new data structure
            if "surrogate_vector" in data:
                # New format - extract the element data from surrogate_vector
                self.element_data = data["surrogate_vector"]
            else:
                # Old format - data is already in the expected structure
                self.element_data = data
            
    def process_surrogates(self):
        """
        Process the element data to create surrogate vectors and calculate percentages.
        
        This method iterates through each timestep in the element data, maps elements to their
        surrogates, and calculates the corresponding surrogate percentages.
        
        Returns:
            Tuple containing the surrogate vector and surrogate percentages
        """
        self.surrogate_vector = {}
        self.surrogate_percentages = {}
        
        # Process each timestep
        for timestep, elements in self.element_data.items():
            self.surrogate_vector[timestep] = {}
            self.surrogate_percentages[timestep] = {}
            
            # Initialize the surrogates for this timestep
            for surrogate in self.surrogate_mapping.keys():
                self.surrogate_vector[timestep][surrogate] = {
                    "atom_density": 0.0,
                    "mole_percent": 0.0
                }
                self.surrogate_percentages[timestep][surrogate] = {}
            
            # Map elements to surrogates
            for element, values in elements.items():
                element_lower = element.lower()
                
                # Find which surrogate(s) this element maps to
                for surrogate, candidates in self.surrogate_mapping.items():
                    if element_lower in candidates:
                        # Add element values to the surrogate totals
                        self.surrogate_vector[timestep][surrogate]["atom_density"] += values["atom_density"]
                        self.surrogate_vector[timestep][surrogate]["mole_percent"] += values["mole_percent"]
                        
                        # Record the element's contribution to the surrogate
                        self.surrogate_percentages[timestep][surrogate][element_lower] = {
                            "atom_density": values["atom_density"],
                            "contribution_percentage": 0.0  # Will calculate after summing
                        }
            
            # Calculate the contribution percentages for each surrogate
            for surrogate in self.surrogate_mapping.keys():
                surrogate_atom_density = self.surrogate_vector[timestep][surrogate]["atom_density"]
                
                # Only calculate percentages if there's a non-zero denominator
                if surrogate_atom_density > 0:
                    for element in self.surrogate_percentages[timestep][surrogate].keys():
                        element_atom_density = self.surrogate_percentages[timestep][surrogate][element]["atom_density"]
                        contribution = element_atom_density / surrogate_atom_density * 100.0
                        self.surrogate_percentages[timestep][surrogate][element]["contribution_percentage"] = contribution
        
        return self.surrogate_vector, self.surrogate_percentages
    
    def save_results(self, output_file: str = "surrogate_vector.json"):
        """
        Save the processed results to a JSON file.
        
        Args:
            output_file: Path to the output JSON file
        """
        # Create the final output structure
        output_data = {
            "surrogate_vector": self.surrogate_vector,
            "surrogate_percentages": self.surrogate_percentages
        }
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=4)
            
        print(f"Results saved to {output_file}")


def main():
    """Main function to run the surrogate processing."""
    # File paths
    surrogate_file = "surrogates_and_candidates.json"
    element_data_file = "ThEIRENE_FuelSalt_processed_elements.json"
    output_file = "surrogate_vector.json"
    
    # Create and run the processor
    processor = SurrogateProcessor(surrogate_file, element_data_file)
    processor.process_surrogates()
    processor.save_results(output_file)
    
    print("Surrogate processing completed successfully!")


if __name__ == "__main__":
    main()