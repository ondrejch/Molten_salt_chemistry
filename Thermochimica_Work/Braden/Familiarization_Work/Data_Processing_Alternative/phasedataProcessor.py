import json
import matplotlib.pyplot as plt
import numpy as np
import os

def readDatabase(datafile):
    """
    Reads and parses a JSON file containing thermodynamic data.
    
    Args:
        datafile (str): Path to the JSON file
        
    Returns:
        dict: Parsed JSON data
    """
    with open(datafile) as f:  # Using 'with' ensures the file is properly closed
        data = json.load(f)
    return data

def find_Species_of_Interest(Non_Zero_Species):    
    """
    Finds unique species from a list of lists containing species names.
    
    Args:
        Non_Zero_Species (list): List of lists containing species names and their phase types
        
    Returns:
        set: Set of unique species tuples (name, phase_type)
    """
    unique_strings = set()
    for sublist in Non_Zero_Species:
        for item in sublist:
            unique_strings.add(item)
    return unique_strings

def get_species_data(data, species_name, is_solution_phase):
    """
    Extracts moles data for a specific species across all temperature points.
    
    Args:
        data (dict): The complete dataset
        species_name (str): Name of the species to extract data for
        is_solution_phase (bool): Whether the species is a solution phase (True) or condensed phase (False)
        
    Returns:
        list: Moles values for the species across all temperature points
    """
    moles = []
    for k1 in data.keys():
        if is_solution_phase:
            moles.append(data[k1]['solution phases'][species_name]['moles'])
        else:
            moles.append(data[k1]['pure condensed phases'][species_name]['moles'])
    return moles

def process_json_file(filepath):
    """
    Processes a single JSON file to create plots and analysis of species data.
    
    Args:
        filepath (str): Path to the JSON file to process
    """
    # Extract base filename for output files
    base_filename = os.path.splitext(os.path.basename(filepath))[0]
    
    # Create output text file
    output_txt = f"{base_filename}_print.txt"
    with open(output_txt, 'w') as f_out:
        # Create a custom print function that writes to both console and file
        def custom_print(*args, **kwargs):
            print(*args, **kwargs)
            print(*args, **kwargs, file=f_out)
        
        # Read the JSON data
        data = readDatabase(filepath)
        
        # Initialize lists to store temperature and species data
        temperatures = []
        Non_Zero_Species = []
        
        # First pass: collect all species and temperatures
        for k1 in data.keys():
            temperatures.append(data[k1]['temperature'])
            temp_it = []
            
            # Check solution phases for non-zero moles
            for k2 in data[k1]['solution phases'].keys():
                if data[k1]['solution phases'][k2]['moles'] != 0:
                    temp_it.append((k2, True))  # True flags it as a solution phase
            
            # Check pure condensed phases for non-zero moles
            for k3 in data[k1]['pure condensed phases'].keys():
                if data[k1]['pure condensed phases'][k3]['moles'] != 0:
                    temp_it.append((k3, False))  # False flags it as a condensed phase
                    
            Non_Zero_Species.append(temp_it)
        
        # Get unique species with their phase type using set operations
        all_species = set()
        for sublist in Non_Zero_Species:
            for item in sublist:
                all_species.add(item)
        
        # Print information about species found
        custom_print('Species of Interest:')
        for species, is_solution in all_species:
            custom_print(f"{species} ({'solution' if is_solution else 'condensed'} phase)")
        custom_print('!!! Remember to Check that Nonzero Species Match the Variables used in Phase Plots !!!')
        
        # Extract moles data for all species
        moles_data = {}
        for species, is_solution in all_species:
            # Clean up species names by removing phase indicators
            species_key = species.replace('(s)', '').replace('(s2)', '').replace('(s3)', '')
            moles_data[species_key] = get_species_data(data, species, is_solution)
        
        # Create moles plot
        plt.figure(figsize=(10, 8))
        # Generate colors and markers for plotting
        colors = plt.cm.tab20(np.linspace(0, 1, len(moles_data)))
        markers = ['o', 's', '^', 'x', 'd', '*', 'v', '<', '>', 'p', 'h', '8', 'D', 'P']
        
        # Plot each species
        for (species, moles), color, marker in zip(moles_data.items(), colors, markers * 2):
            plt.plot(temperatures, moles, label=species, color=color, marker=marker, markersize=6)
        
        # Add plot formatting
        plt.grid(True, linestyle='--', which='both', color='grey', alpha=0.5)
        plt.xlabel('Temperature (°C)')
        plt.ylabel('Moles')
        plt.title('Moles of Different Compounds vs Temperature')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(f"{base_filename}_moles.png", bbox_inches='tight', dpi=300)
        plt.close()
        
        # Calculate total moles at each temperature point
        total_mol = []
        for k1 in data.keys():
            mol_it = 0
            for k2 in data[k1]['solution phases'].keys():
                mol_it += data[k1]['solution phases'][k2]['moles']
            for k3 in data[k1]['pure condensed phases'].keys():
                mol_it += data[k1]['pure condensed phases'][k3]['moles']
            total_mol.append(mol_it)
        
        # Convert data to numpy arrays for calculations
        moles_arrays = {k: np.array(v) for k, v in moles_data.items()}
        total_mol = np.array(total_mol)
        
        # Verify all species are accounted for
        species_check = sum(moles_arrays.values())
        dsc_check = species_check - total_mol
        
        # Check for discrepancies, allowing for small floating point errors
        if np.abs(dsc_check).max() > 1e-10:
            custom_print('WARNING: Numerical discrepancy detected')
            custom_print(f"Maximum discrepancy: {np.abs(dsc_check).max()}")
        else:
            custom_print("All Species Accounted")
        
        # Create mole fractions plot
        plt.figure(figsize=(10, 8))
        
        # Plot mole fractions for each species
        for (species, moles), color, marker in zip(moles_arrays.items(), colors, markers * 2):
            mol_frac = moles / total_mol
            plt.plot(temperatures, mol_frac, label=species, color=color, marker=marker, markersize=6)
        
        # Add plot formatting
        plt.grid(True, linestyle='--', which='both', color='grey', alpha=0.5)
        plt.xlabel('Temperature (°C)')
        plt.ylabel('Mole Fraction')
        plt.title('Mole Fractions of Different Compounds vs Temperature')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(f"{base_filename}_molfrac.png", bbox_inches='tight', dpi=300)
        plt.close()

def main():
    """
    Main function that processes all JSON files in the current directory.
    """
    for filename in os.listdir('.'):
        if filename.endswith('.json'):
            print(f"\nProcessing {filename}...")
            process_json_file(filename)
            print(f"Completed processing {filename}")

if __name__ == "__main__":
    main()