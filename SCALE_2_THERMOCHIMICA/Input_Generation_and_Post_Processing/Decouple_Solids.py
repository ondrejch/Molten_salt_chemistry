import json
import os
from pathlib import Path

def decouple_solids(solids_path, surrogate_vector_path, output_path):
    """
    Decouples species mole percentages in a solids.json file using surrogate vector data.
    
    Args:
        solids_path: Path to the Solids.json file
        surrogate_vector_path: Path to the surrogate_vector.json file
        output_path: Path to write the decoupled output file
    """
    # Load the input files
    with open(solids_path, 'r') as f:
        solids_data = json.load(f)
    
    with open(surrogate_vector_path, 'r') as f:
        surrogate_data = json.load(f)
        
    surrogate_percentages = surrogate_data.get('surrogate_percentages', {})
    
    # Create a new structure for the decoupled solids
    decoupled_solids = {}
    
    # Process each timestep
    for timestep, timestep_data in solids_data.items():
        decoupled_solids[timestep] = {}
        
        # Skip if this timestep doesn't have surrogate data
        if timestep not in surrogate_percentages:
            print(f"Warning: No surrogate data for timestep {timestep}, copying original data")
            decoupled_solids[timestep] = timestep_data
            continue
        
        surrogate_timestep = surrogate_percentages[timestep]
        
        # Process each phase in the timestep
        for phase_name, phase_data in timestep_data.items():
            # Initialize the new phase data with a copy of the original
            decoupled_phase = phase_data.copy()
            
            # Skip if not a solid type or doesn't have species_mole_percent
            if not isinstance(phase_data, dict) or 'type' not in phase_data or phase_data['type'] != 'solid' or 'species_mole_percent' not in phase_data:
                decoupled_solids[timestep][phase_name] = phase_data
                continue
            
            # Create new element_mole_percent dictionary
            element_mole_percent = {}
            
            # Process each species in the phase
            for species, mole_percent in phase_data['species_mole_percent'].items():
                species_lower = species.lower()
                
                # Skip if this species doesn't have surrogate data
                if species_lower not in surrogate_timestep:
                    print(f"Warning: No surrogate data for species {species} in timestep {timestep}")
                    element_mole_percent[species] = mole_percent
                    continue
                
                # Get the surrogate contributions for this species
                species_surrogates = surrogate_timestep[species_lower]
                
                # Calculate the decoupled mole percentages
                for surrogate, surrogate_data in species_surrogates.items():
                    contribution_percentage = surrogate_data.get('contribution_percentage', 0) / 100.0
                    new_mole_percent = mole_percent * contribution_percentage
                    
                    # Only add non-zero contributions
                    if new_mole_percent > 0:
                        surrogate_name = surrogate.capitalize() if len(surrogate) <= 2 else surrogate.lower()
                        
                        # Add or update the surrogate in the element_mole_percent
                        if surrogate_name in element_mole_percent:
                            element_mole_percent[surrogate_name] += new_mole_percent
                        else:
                            element_mole_percent[surrogate_name] = new_mole_percent
            
            # Replace species_mole_percent with element_mole_percent
            decoupled_phase.pop('species_mole_percent')
            decoupled_phase['element_mole_percent'] = element_mole_percent
            
            # Add the decoupled phase to the result
            decoupled_solids[timestep][phase_name] = decoupled_phase
    
    # Write the decoupled solids to the output file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(decoupled_solids, f, indent=2)
    
    print(f"Decoupled solids written to {output_path}")

if __name__ == "__main__":
    # Default paths
    solids_path = "output/Solids.json"
    surrogate_vector_path = "surrogate_vector.json"
    output_path = "output/Decoupled_Solids.json"
    
    # Check if files exist
    if not Path(solids_path).exists():
        print(f"Error: {solids_path} not found")
        exit(1)
    
    if not Path(surrogate_vector_path).exists():
        print(f"Error: {surrogate_vector_path} not found")
        exit(1)
    
    # Run the decoupling process
    decouple_solids(solids_path, surrogate_vector_path, output_path)