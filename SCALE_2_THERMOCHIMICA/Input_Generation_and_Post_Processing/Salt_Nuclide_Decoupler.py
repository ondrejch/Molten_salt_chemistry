import json
from decimal import Decimal, getcontext

# Set a very high precision for Decimal operations
getcontext().prec = 50

def process_salt_data():
    # Load the JSON files
    with open('output/Decoupled_Salt.json', 'r') as f:
        decoupled_salt = json.load(f)
    
    with open('processed_fuel_salt_data.json', 'r') as f:
        processed_fuel_data = json.load(f)
    
    # Initialize the output dictionary
    salt_nuclides = {}
    
    # Process each timestep in decoupled_salt
    for timestep, timestep_data in decoupled_salt.items():
        # Make sure we have the corresponding timestep in processed_fuel_data
        if timestep not in processed_fuel_data["surrogate_percentages"]:
            print(f"Warning: Timestep {timestep} not found in processed_fuel_data. Skipping.")
            continue
        
        salt_nuclides[timestep] = {}
        surrogate_data = processed_fuel_data["surrogate_percentages"][timestep]
        
        # Process each phase in the timestep
        for phase_name, phase_data in timestep_data.items():
            salt_nuclides[timestep][phase_name] = {
                "phase_percent": phase_data["phase_percent"],
                "moles": phase_data["moles"],
                "type": phase_data["type"],
                "cation_nuclide_mole_percent": {},  # Separate dictionary for cations
                "anion_nuclide_mole_percent": {}    # Separate dictionary for anions
            }
            
            # Process cations
            for cation, cation_mole_percent in phase_data.get("cation_mole_percent", {}).items():
                # Extract the element from the cation name
                element = cation.split('[')[0].lower()
                
                # Skip processing if the element doesn't exist in the surrogate percentages
                if element not in surrogate_data:
                    continue
                
                # Special handling for dimers - they contribute twice the amount
                multiplier = 2 if "Dimer" in cation else 1
                
                # Convert to Decimal for high precision
                cation_mole_percent_dec = Decimal(str(cation_mole_percent))
                multiplier_dec = Decimal(multiplier)
                
                # Calculate the nuclide contributions
                for nuclide, nuclide_data in surrogate_data[element].items():
                    contribution_percentage = Decimal(str(nuclide_data["contribution_percentage"]))
                    
                    # Calculate the nuclide mole percent with high precision
                    nuclide_mole_percent = cation_mole_percent_dec * multiplier_dec * contribution_percentage / Decimal('100')
                    
                    # Add to the cation total, preserving full precision
                    if nuclide in salt_nuclides[timestep][phase_name]["cation_nuclide_mole_percent"]:
                        salt_nuclides[timestep][phase_name]["cation_nuclide_mole_percent"][nuclide] += nuclide_mole_percent
                    else:
                        salt_nuclides[timestep][phase_name]["cation_nuclide_mole_percent"][nuclide] = nuclide_mole_percent
            
            # Process anions
            for anion, anion_mole_percent in phase_data.get("anion_mole_percent", {}).items():
                element = anion.lower()
                
                # Skip processing if the element doesn't exist in the surrogate percentages
                if element not in surrogate_data:
                    continue
                
                # Convert to Decimal for high precision
                anion_mole_percent_dec = Decimal(str(anion_mole_percent))
                
                # Calculate the nuclide contributions
                for nuclide, nuclide_data in surrogate_data[element].items():
                    contribution_percentage = Decimal(str(nuclide_data["contribution_percentage"]))
                    
                    # Calculate the nuclide mole percent with high precision
                    nuclide_mole_percent = anion_mole_percent_dec * contribution_percentage / Decimal('100')
                    
                    # Add to the anion total, preserving full precision
                    if nuclide in salt_nuclides[timestep][phase_name]["anion_nuclide_mole_percent"]:
                        salt_nuclides[timestep][phase_name]["anion_nuclide_mole_percent"][nuclide] += nuclide_mole_percent
                    else:
                        salt_nuclides[timestep][phase_name]["anion_nuclide_mole_percent"][nuclide] = nuclide_mole_percent

    # Custom encoder to handle Decimal objects
    class DecimalEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Decimal):
                return str(obj)  # Convert Decimal to string to preserve precision
            return super(DecimalEncoder, self).default(obj)
    
    # Write the output to a new JSON file with full precision
    with open('Salt_Nuclides.json', 'w') as f:
        json.dump(salt_nuclides, f, indent=2, ensure_ascii=False, cls=DecimalEncoder)
    
    print("Processing complete. Output written to Salt_Nuclides.json")

if __name__ == "__main__":
    process_salt_data()