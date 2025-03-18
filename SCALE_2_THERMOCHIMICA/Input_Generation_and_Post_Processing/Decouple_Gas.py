import json
import os
import re
from pathlib import Path

def parse_molecule(molecule):
    """
    Parse a molecule formula into its constituent elements with counts.
    
    Args:
        molecule: A string representing a molecular formula (e.g., 'BeF2', 'Li2ZrF6')
    
    Returns:
        A dictionary mapping elements to their counts in the molecule
    """
    # Regular expression to match element symbols and their counts
    pattern = r'([A-Z][a-z]*)(\d*)'
    matches = re.findall(pattern, molecule)
    
    elements = {}
    for element, count in matches:
        elements[element] = int(count) if count else 1
    
    return elements

def substitute_element(molecule, original_element, substitute_element):
    """
    Substitute one element for another in a molecule formula.
    
    Args:
        molecule: Original molecule formula
        original_element: Element to be replaced
        substitute_element: Element to replace with
    
    Returns:
        New molecule formula with the substitution
    """
    # Regular expression to match the specific element and its count
    # Fix the escape sequence by using r-string
    pattern = r'(' + re.escape(original_element) + r')(\d*)'
    
    # Function to handle the replacement, preserving the count
    def replace(match):
        element, count = match.groups()
        return f"{substitute_element}{count}"
    
    # Perform the substitution
    return re.sub(pattern, replace, molecule)

def decouple_gas(gas_path, surrogate_vector_path, output_path):
    """
    Decouples species mole percentages in a Gas.json file using surrogate vector data.
    
    Args:
        gas_path: Path to the Gas.json file
        surrogate_vector_path: Path to the surrogate_vector.json file
        output_path: Path to write the decoupled output file
    """
    # Load the input files
    with open(gas_path, 'r') as f:
        gas_data = json.load(f)
    
    with open(surrogate_vector_path, 'r') as f:
        surrogate_data = json.load(f)
        
    surrogate_percentages = surrogate_data.get('surrogate_percentages', {})
    
    # Create a new structure for the decoupled gas
    decoupled_gas = {}
    
    # Process each timestep
    for timestep, timestep_data in gas_data.items():
        decoupled_gas[timestep] = {}
        
        # Skip if this timestep doesn't have surrogate data
        if timestep not in surrogate_percentages:
            print(f"Warning: No surrogate data for timestep {timestep}, copying original data")
            decoupled_gas[timestep] = timestep_data
            continue
        
        surrogate_timestep = surrogate_percentages[timestep]
        
        # Process each phase in the timestep
        for phase_name, phase_data in timestep_data.items():
            # Initialize the new phase data with a copy of the original
            decoupled_phase = phase_data.copy()
            
            # Skip if not a gas type or doesn't have species_mole_percent
            if not isinstance(phase_data, dict) or 'type' not in phase_data or phase_data['type'] != 'gas' or 'species_mole_percent' not in phase_data:
                decoupled_gas[timestep][phase_name] = phase_data
                continue
            
            # Create new species_mole_percent dictionary
            new_species_mole_percent = {}
            
            # Process each species in the phase
            for species, mole_percent in phase_data['species_mole_percent'].items():
                # For simple elements, process them directly
                if len(species) <= 2 and species.isalpha():
                    species_lower = species.lower()
                    
                    # Skip if this species doesn't have surrogate data
                    if species_lower not in surrogate_timestep:
                        print(f"Warning: No surrogate data for species {species} in timestep {timestep}")
                        new_species_mole_percent[species] = mole_percent
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
                            
                            # Add or update the surrogate in the new_species_mole_percent
                            if surrogate_name in new_species_mole_percent:
                                new_species_mole_percent[surrogate_name] += new_mole_percent
                            else:
                                new_species_mole_percent[surrogate_name] = new_mole_percent
                
                # For molecules, need to handle as a complete molecule
                else:
                    parsed_molecule = parse_molecule(species)
                    
                    # Determine which elements need decoupling
                    elements_to_decouple = []
                    for element in parsed_molecule:
                        element_lower = element.lower()
                        if element_lower in surrogate_timestep and len(surrogate_timestep[element_lower]) > 1:
                            elements_to_decouple.append(element)
                    
                    # If no elements need decoupling, keep the original molecule
                    if not elements_to_decouple:
                        new_species_mole_percent[species] = mole_percent
                        continue
                    
                    # For each element that needs decoupling, create new molecules by direct substitution
                    # Start with the original molecule and its percentage
                    molecules_to_process = [(species, mole_percent)]
                    
                    # Process each element that needs decoupling
                    for element in elements_to_decouple:
                        element_lower = element.lower()
                        element_surrogates = surrogate_timestep[element_lower]
                        
                        # Create a new list of molecules with the substituted elements
                        new_molecules = []
                        for molecule, mol_percent in molecules_to_process:
                            for surrogate, surrogate_data in element_surrogates.items():
                                contribution_percentage = surrogate_data.get('contribution_percentage', 0) / 100.0
                                if contribution_percentage <= 0:
                                    continue
                                
                                surrogate_name = surrogate.capitalize() if len(surrogate) <= 2 else surrogate.lower()
                                
                                # Only substitute if the surrogate is different from the original element
                                if element.lower() != surrogate.lower():
                                    new_molecule = substitute_element(molecule, element, surrogate_name)
                                    new_mole_percent = mol_percent * contribution_percentage
                                    new_molecules.append((new_molecule, new_mole_percent))
                                else:
                                    # Keep the original element portion
                                    new_molecules.append((molecule, mol_percent * contribution_percentage))
                        
                        # Replace the list of molecules to process with the new list
                        molecules_to_process = new_molecules
                    
                    # Add all the new molecules to the result
                    for molecule, mol_percent in molecules_to_process:
                        if molecule in new_species_mole_percent:
                            new_species_mole_percent[molecule] += mol_percent
                        else:
                            new_species_mole_percent[molecule] = mol_percent
            
            # Replace species_mole_percent with the new decoupled values
            decoupled_phase['species_mole_percent'] = new_species_mole_percent
            
            # Add the decoupled phase to the result
            decoupled_gas[timestep][phase_name] = decoupled_phase
    
    # Write the decoupled gas to the output file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(decoupled_gas, f, indent=2)
    
    print(f"Decoupled gas written to {output_path}")

if __name__ == "__main__":
    # Default paths
    gas_path = "output/Gas.json"
    surrogate_vector_path = "surrogate_vector.json"
    output_path = "output/Decoupled_Gas.json"
    
    # Check if files exist
    if not Path(gas_path).exists():
        print(f"Error: {gas_path} not found")
        exit(1)
    
    if not Path(surrogate_vector_path).exists():
        print(f"Error: {surrogate_vector_path} not found")
        exit(1)
    
    # Run the decoupling process
    decouple_gas(gas_path, surrogate_vector_path, output_path)