import json
import os
import re
from pathlib import Path

def substitute_ion(ion, original_element, substitute_element):
    """
    Substitute one element for another in an ion formula.
    
    Args:
        ion: Original ion formula
        original_element: Element to be replaced
        substitute_element: Element to replace with
    
    Returns:
        New ion formula with the substitution
    """
    # Regular expression to match the specific element in the ion, handling malformed brackets
    pattern = r'(' + re.escape(original_element) + r')(\[[^\]]*\]?|$)'
    
    # Function to handle the replacement, preserving the charge/coordination info
    def replace(match):
        element, charge_info = match.groups()
        return f"{substitute_element}{charge_info}"
    
    # Perform the substitution
    return re.sub(pattern, replace, ion)

def decouple_salt(salt_path, surrogate_vector_path, output_path):
    """
    Decouples ion mole percentages in a Salt.json file using surrogate vector data.
    
    Args:
        salt_path: Path to the Salt.json file
        surrogate_vector_path: Path to the surrogate_vector.json file
        output_path: Path to write the decoupled output file
    """
    # Load the input files
    with open(salt_path, 'r') as f:
        salt_data = json.load(f)
    
    with open(surrogate_vector_path, 'r') as f:
        surrogate_data = json.load(f)
        
    surrogate_percentages = surrogate_data.get('surrogate_percentages', {})
    
    # Create a new structure for the decoupled salt
    decoupled_salt = {}
    
    # Track statistics for debugging
    decoupling_stats = {
        "processed_ions": 0,
        "decoupled_ions": 0,
        "skipped_ions": 0,
        "elements_not_found": set(),
        "elements_decoupled": set(),
        "elements_not_decoupled": set()
    }
    
    # Process each timestep
    for timestep, timestep_data in salt_data.items():
        decoupled_salt[timestep] = {}
        
        # Skip if this timestep doesn't have surrogate data
        if timestep not in surrogate_percentages:
            print(f"Warning: No surrogate data for timestep {timestep}, copying original data")
            decoupled_salt[timestep] = timestep_data
            continue
        
        surrogate_timestep = surrogate_percentages[timestep]
        
        # Process each phase in the timestep
        for phase_name, phase_data in timestep_data.items():
            # Initialize the new phase data with a copy of the original
            decoupled_phase = phase_data.copy()
            
            # Skip if not a salt type or doesn't have cation/anion_mole_percent
            if not isinstance(phase_data, dict) or 'type' not in phase_data or phase_data['type'] != 'salt':
                decoupled_salt[timestep][phase_name] = phase_data
                continue
            
            # Process cation_mole_percent if present
            if 'cation_mole_percent' in phase_data:
                new_cation_mole_percent = {}
                
                # Process each cation in the phase
                for ion, mole_percent in phase_data['cation_mole_percent'].items():
                    decoupling_stats["processed_ions"] += 1
                    
                    # Extract the element from the ion (element is everything before the first '[' or other non-letter)
                    match = re.match(r'([A-Za-z]+)', ion)
                    if not match:
                        # If we can't extract an element, keep the original ion
                        new_cation_mole_percent[ion] = mole_percent
                        decoupling_stats["skipped_ions"] += 1
                        continue
                        
                    element = match.group(1)
                    element_lower = element.lower()
                    
                    # Debug print for Be ions
                    if element_lower == 'be':
                        print(f"Found Be ion: {ion}, checking surrogate data...")
                        if element_lower in surrogate_timestep:
                            print(f"Surrogate data found for Be with {len(surrogate_timestep[element_lower])} surrogates")
                        else:
                            print("No surrogate data found for Be")
                    
                    # Skip if this element doesn't have surrogate data
                    if element_lower not in surrogate_timestep:
                        new_cation_mole_percent[ion] = mole_percent
                        decoupling_stats["elements_not_found"].add(element_lower)
                        continue
                    
                    # Get the surrogate contributions for this element
                    element_surrogates = surrogate_timestep[element_lower]
                    
                    # Skip if there's only one surrogate (no decoupling needed)
                    if len(element_surrogates) <= 1:
                        new_cation_mole_percent[ion] = mole_percent
                        decoupling_stats["elements_not_decoupled"].add(element_lower)
                        continue
                    
                    # Flag to track if we actually decoupled this ion
                    decoupled = False
                    
                    # Calculate the decoupled mole percentages
                    for surrogate, surrogate_data in element_surrogates.items():
                        contribution_percentage = surrogate_data.get('contribution_percentage', 0) / 100.0
                        new_mole_percent = mole_percent * contribution_percentage
                        
                        # Only add non-zero contributions
                        if new_mole_percent > 0:
                            surrogate_name = surrogate.capitalize() if len(surrogate) <= 2 else surrogate.lower()
                            
                            # If the surrogate is the same as the original element, keep the original ion
                            if surrogate_name.lower() == element_lower:
                                new_ion = ion
                            else:
                                # Create a new ion by substituting the element
                                new_ion = substitute_ion(ion, element, surrogate_name)
                                decoupled = True
                            
                            # Add or update the surrogate in the new_cation_mole_percent
                            if new_ion in new_cation_mole_percent:
                                new_cation_mole_percent[new_ion] += new_mole_percent
                            else:
                                new_cation_mole_percent[new_ion] = new_mole_percent
                    
                    if decoupled:
                        decoupling_stats["decoupled_ions"] += 1
                        decoupling_stats["elements_decoupled"].add(element_lower)
                    else:
                        decoupling_stats["elements_not_decoupled"].add(element_lower)
                
                # Replace cation_mole_percent with the new decoupled values
                decoupled_phase['cation_mole_percent'] = new_cation_mole_percent
            
            # Process anion_mole_percent if present
            if 'anion_mole_percent' in phase_data:
                new_anion_mole_percent = {}
                
                # Process each anion in the phase
                for ion, mole_percent in phase_data['anion_mole_percent'].items():
                    decoupling_stats["processed_ions"] += 1
                    
                    # Extract the element from the ion (element is everything before the first '[' if present)
                    match = re.match(r'([A-Za-z]+)', ion)
                    if not match:
                        # If we can't extract an element, keep the original ion
                        new_anion_mole_percent[ion] = mole_percent
                        decoupling_stats["skipped_ions"] += 1
                        continue
                        
                    element = match.group(1)
                    element_lower = element.lower()
                    
                    # Skip if this element doesn't have surrogate data
                    if element_lower not in surrogate_timestep:
                        new_anion_mole_percent[ion] = mole_percent
                        decoupling_stats["elements_not_found"].add(element_lower)
                        continue
                    
                    # Get the surrogate contributions for this element
                    element_surrogates = surrogate_timestep[element_lower]
                    
                    # Skip if there's only one surrogate (no decoupling needed)
                    if len(element_surrogates) <= 1:
                        new_anion_mole_percent[ion] = mole_percent
                        decoupling_stats["elements_not_decoupled"].add(element_lower)
                        continue
                    
                    # Flag to track if we actually decoupled this ion
                    decoupled = False
                    
                    # Calculate the decoupled mole percentages
                    for surrogate, surrogate_data in element_surrogates.items():
                        contribution_percentage = surrogate_data.get('contribution_percentage', 0) / 100.0
                        new_mole_percent = mole_percent * contribution_percentage
                        
                        # Only add non-zero contributions
                        if new_mole_percent > 0:
                            surrogate_name = surrogate.capitalize() if len(surrogate) <= 2 else surrogate.lower()
                            
                            # If the surrogate is the same as the original element, keep the original ion
                            if surrogate_name.lower() == element_lower:
                                new_ion = ion
                            else:
                                # Create a new ion by substituting the element
                                new_ion = substitute_ion(ion, element, surrogate_name)
                                decoupled = True
                            
                            # Add or update the surrogate in the new_anion_mole_percent
                            if new_ion in new_anion_mole_percent:
                                new_anion_mole_percent[new_ion] += new_mole_percent
                            else:
                                new_anion_mole_percent[new_ion] = new_mole_percent
                    
                    if decoupled:
                        decoupling_stats["decoupled_ions"] += 1
                        decoupling_stats["elements_decoupled"].add(element_lower)
                    else:
                        decoupling_stats["elements_not_decoupled"].add(element_lower)
                
                # Replace anion_mole_percent with the new decoupled values
                decoupled_phase['anion_mole_percent'] = new_anion_mole_percent
            
            # Add the decoupled phase to the result
            decoupled_salt[timestep][phase_name] = decoupled_phase
    
    # Write the decoupled salt to the output file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(decoupled_salt, f, indent=2)
    
    # Print statistics
    print(f"Decoupled salt written to {output_path}")
    print(f"Processed {decoupling_stats['processed_ions']} ions")
    print(f"Decoupled {decoupling_stats['decoupled_ions']} ions")
    print(f"Skipped {decoupling_stats['skipped_ions']} ions (no element found)")
    print(f"Elements not found in surrogate data: {', '.join(decoupling_stats['elements_not_found'])}")
    print(f"Elements decoupled: {', '.join(decoupling_stats['elements_decoupled'])}")
    print(f"Elements not decoupled (only one surrogate): {', '.join(decoupling_stats['elements_not_decoupled'])}")

if __name__ == "__main__":
    # Default paths
    salt_path = "output/Salt.json"
    surrogate_vector_path = "surrogate_vector.json"
    output_path = "output/Decoupled_Salt.json"
    
    # Check if files exist
    if not Path(salt_path).exists():
        print(f"Error: {salt_path} not found")
        exit(1)
    
    if not Path(surrogate_vector_path).exists():
        print(f"Error: {surrogate_vector_path} not found")
        exit(1)
    
    # Run the decoupling process
    decouple_salt(salt_path, surrogate_vector_path, output_path)