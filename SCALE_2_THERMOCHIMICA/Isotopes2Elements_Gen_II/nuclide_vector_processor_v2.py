import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import argparse
import os

def process_nuclide_data(input_file, output_file, elements_to_include=None, plot_type='stackplot', 
                         include_isotopes=True):
    """
    Process nuclide data from a JSON file to calculate element atom densities and mole percentages.
    Can optionally include isotopic contribution percentages.
    
    Args:
        input_file (str): Path to input JSON file
        output_file (str): Path to output JSON file
        elements_to_include (list, optional): List of element symbols to include. Defaults to None (all elements).
        plot_type (str, optional): Type of plot to generate ('stackplot', 'semilog', 'combined'). Defaults to 'stackplot'.
        include_isotopes (bool, optional): Whether to include isotopic contributions. Defaults to True.
    
    Returns:
        dict: Processed nuclide data
    """
    print(f"Processing file: {input_file}")
    
    # Read the input JSON file
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Create a dictionary to store processed data with structure similar to surrogate_vector.json
    processed_data = {
        "surrogate_vector": {},
        "surrogate_percentages": {}
    }
    
    # Process each time step in the data
    for time_step, time_data in data.items():
        # Skip empty time steps or those without nuclide data
        if not time_data or 'nuclide' not in time_data:
            print(f"Warning: Skipping time step {time_step} - no nuclide data found")
            continue
        
        # Initialize dictionaries for total element atom densities and isotopic contributions
        total_element_atom_densities = defaultdict(float)
        isotope_contributions = defaultdict(dict)
        
        try:
            # First, calculate total atom densities for ALL elements and track isotope contributions
            for nuclide, atom_density in time_data['nuclide'].items():
                # Handle nuclides in format "element-isotope"
                parts = nuclide.split('-')
                element = parts[0]
                
                # Add to total element atom density
                total_element_atom_densities[element] += atom_density
                
                # Track isotope contribution if we're including isotopes
                if include_isotopes:
                    isotope_contributions[element][nuclide] = atom_density
            
            # Skip time steps where no elements were found
            if not total_element_atom_densities:
                print(f"Warning: Skipping time step {time_step} - no valid element data found")
                continue
                
            # Calculate total atom density for mole percent
            total_atom_density = sum(total_element_atom_densities.values())
            
            # Skip if total atom density is zero to avoid division by zero
            if total_atom_density <= 0:
                print(f"Warning: Skipping time step {time_step} - total atom density is zero or negative: {total_atom_density}")
                continue
            
            # Prepare processed data for this time step
            processed_step_vector = {}
            processed_step_percentages = {}
            
            for element, total_density in total_element_atom_densities.items():
                # Calculate mole percent using TOTAL atom density
                mole_percent = (total_density / total_atom_density) * 100
                
                # Only include in output if no filter is set, or if element is in the filter
                if elements_to_include is None or element in elements_to_include:
                    # Add element to surrogate_vector
                    processed_step_vector[element] = {
                        'atom_density': total_density,
                        'mole_percent': mole_percent
                    }
                    
                    # Add isotopic contributions if requested
                    if include_isotopes:
                        isotope_data = {}
                        # Check if total_density is zero to avoid division by zero
                        if total_density > 0:
                            for nuclide, density in isotope_contributions[element].items():
                                # Calculate contribution percentage
                                contribution_percentage = (density / total_density) * 100
                                isotope_data[nuclide] = {
                                    'atom_density': density,
                                    'contribution_percentage': contribution_percentage
                                }
                        else:
                            # Handle case where total_density is zero
                            for nuclide, density in isotope_contributions[element].items():
                                isotope_data[nuclide] = {
                                    'atom_density': density,
                                    'contribution_percentage': 0.0  # Set to zero if total density is zero
                                }
                        processed_step_percentages[element] = isotope_data
            
            # Add processed data to output structure
            processed_data["surrogate_vector"][time_step] = processed_step_vector
            if include_isotopes:
                processed_data["surrogate_percentages"][time_step] = processed_step_percentages
            
        except Exception as e:
            print(f"Error processing time step {time_step}: {str(e)}")
            import traceback
            traceback.print_exc()  # Print detailed error information
            continue
    
    # Check if we have any processed data
    if not processed_data["surrogate_vector"]:
        raise ValueError("No valid data was processed. Check input file format and content.")
    
    # Save processed data to a new JSON file
    with open(output_file, 'w') as f:
        json.dump(processed_data, f, indent=4)
    
    return processed_data

def generate_plots(processed_data, plot_type='stackplot', output_prefix='elemental_abundance'):
    """
    Generate plots based on the processed data.
    
    Args:
        processed_data (dict): Processed nuclide data
        plot_type (str): Type of plot to generate ('stackplot', 'semilog', 'combined')
        output_prefix (str): Prefix for output plot filenames
    """
    # Prepare data for plotting
    days = []
    # Extract just the surrogate_vector part for plotting
    vector_data = processed_data["surrogate_vector"]
    
    # Exit if no data to plot
    if not vector_data:
        print("No data available for plotting.")
        return
    
    # Get list of elements from first time step
    first_time_step = list(vector_data.keys())[0]
    elements = sorted(list(vector_data[first_time_step].keys()))
    
    # Collect plot data
    mole_percentages = defaultdict(list)
    for time_step, step_data in vector_data.items():
        try:
            days.append(int(time_step))
        except ValueError:
            days.append(len(days))
            
        for element in elements:
            if element in step_data:
                mole_percentages[element].append(step_data[element]['mole_percent'])
            else:
                mole_percentages[element].append(0)  # Handle missing elements
    
    # Sort days to ensure proper plotting
    sorted_indices = np.argsort(days)
    days = [days[i] for i in sorted_indices]
    for element in elements:
        mole_percentages[element] = [mole_percentages[element][i] for i in sorted_indices]
    
    # Create plots based on specified type
    plt.figure(figsize=(15, 10))
    
    if plot_type == 'stackplot':
        plt.stackplot(days, [mole_percentages[elem] for elem in elements], 
                      labels=[elem for elem in elements])
        plt.title('Elemental Abundance Over Time (Stacked)')
        plt.ylabel('Mole Percent')
        plt.savefig(f'{output_prefix}_stackplot.png', bbox_inches='tight')
        
    elif plot_type == 'semilog':
        # Find and plot only elements with very low concentrations
        has_data = False
        for element in elements:
            # Only plot elements with max concentration below 1%
            if max(mole_percentages[element]) < 1 and max(mole_percentages[element]) > 0:
                has_data = True
                plt.semilogy(days, mole_percentages[element], label=element, marker='o')
        
        if has_data:
            plt.title('Low Concentration Elements (Semi-log)')
            plt.ylabel('Mole Percent (log scale)')
            plt.savefig(f'{output_prefix}_semilog.png', bbox_inches='tight')
        else:
            print("No low concentration elements found for semilog plot.")
            
    elif plot_type == 'combined':
        # Subplot for main elements
        plt.subplot(2, 1, 1)
        main_elements = [elem for elem in elements if max(mole_percentages[elem]) >= 1]
        if main_elements:
            plt.stackplot(days, [mole_percentages[elem] for elem in main_elements], 
                          labels=[elem for elem in main_elements])
            plt.title('Main Elemental Abundance')
            plt.ylabel('Mole Percent')
        else:
            plt.text(0.5, 0.5, 'No main elements found', ha='center', va='center')
        
        # Subplot for trace elements
        plt.subplot(2, 1, 2)
        trace_elements = [elem for elem in elements if 0 < max(mole_percentages[elem]) < 1]
        if trace_elements:
            for element in trace_elements:
                plt.semilogy(days, mole_percentages[element], label=element, marker='o')
            plt.title('Trace Elements (Semi-log)')
        else:
            plt.text(0.5, 0.5, 'No trace elements found', ha='center', va='center')
            
        plt.xlabel('Time Step')
        plt.ylabel('Mole Percent (log scale)')
        plt.savefig(f'{output_prefix}_combined.png', bbox_inches='tight')
    
    elif plot_type == 'all':
        # Create all plot types
        # Stackplot
        plt.figure(figsize=(15, 10))
        plt.stackplot(days, [mole_percentages[elem] for elem in elements], 
                      labels=[elem for elem in elements])
        plt.title('Elemental Abundance Over Time (Stacked)')
        plt.ylabel('Mole Percent')
        plt.xlabel('Time Step')
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.tight_layout()
        plt.savefig(f'{output_prefix}_stackplot.png', bbox_inches='tight')
        plt.close()
        
        # Semilog plot
        plt.figure(figsize=(15, 10))
        has_data = False
        for element in elements:
            if max(mole_percentages[element]) < 1 and max(mole_percentages[element]) > 0:
                has_data = True
                plt.semilogy(days, mole_percentages[element], label=element, marker='o')
        
        if has_data:
            plt.title('Low Concentration Elements (Semi-log)')
            plt.ylabel('Mole Percent (log scale)')
            plt.xlabel('Time Step')
            plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
            plt.tight_layout()
            plt.savefig(f'{output_prefix}_semilog.png', bbox_inches='tight')
        plt.close()
        
        # Combined plot
        plt.figure(figsize=(15, 10))
        main_elements = [elem for elem in elements if max(mole_percentages[elem]) >= 1]
        trace_elements = [elem for elem in elements if 0 < max(mole_percentages[elem]) < 1]
        
        plt.subplot(2, 1, 1)
        if main_elements:
            plt.stackplot(days, [mole_percentages[elem] for elem in main_elements], 
                          labels=[elem for elem in main_elements])
            plt.title('Main Elemental Abundance')
            plt.ylabel('Mole Percent')
            plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        
        plt.subplot(2, 1, 2)
        if trace_elements:
            for element in trace_elements:
                plt.semilogy(days, mole_percentages[element], label=element, marker='o')
            plt.title('Trace Elements (Semi-log)')
            plt.xlabel('Time Step')
            plt.ylabel('Mole Percent (log scale)')
            plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        
        plt.tight_layout()
        plt.savefig(f'{output_prefix}_combined.png', bbox_inches='tight')
        plt.close()
    
    else:
        print(f"Unknown plot type: {plot_type}")
        return
    
    plt.close()
    print(f"Plots saved with prefix: {output_prefix}")

def verify_total_mole_percent(data):
    """
    Verify that the total mole percent for each time step sums to 100%.
    
    Args:
        data (dict): Processed data
    """
    for time_step, step_data in data["surrogate_vector"].items():
        total = sum(details['mole_percent'] for element, details in step_data.items())
        print(f"Time Step {time_step}: Total Mole Percent = {total:.4f}%")

def print_processed_data(data, verbose=False):
    """
    Print details of processed data.
    
    Args:
        data (dict): Processed data
        verbose (bool): Whether to print isotope details
    """
    vector_data = data["surrogate_vector"]
    percentage_data = data.get("surrogate_percentages", {})
    
    for time_step, step_data in vector_data.items():
        print(f"\nTime Step {time_step}:")
        
        for element, details in sorted(step_data.items(), 
                                       key=lambda x: x[1]['mole_percent'], 
                                       reverse=True):
            print(f"{element}: Atom Density = {details['atom_density']:.6f}, "
                  f"Mole Percent = {details['mole_percent']:.4f}%")
            
            # Print isotope details if verbose and available
            if verbose and percentage_data and time_step in percentage_data and element in percentage_data[time_step]:
                isotopes = percentage_data[time_step][element]
                for isotope, iso_details in isotopes.items():
                    print(f"  └─ {isotope}: Atom Density = {iso_details['atom_density']:.6e}, "
                          f"Contribution = {iso_details['contribution_percentage']:.4f}%")

def debug_input_file(input_file):
    """
    Print debug information about the input file to identify potential issues.
    
    Args:
        input_file (str): Path to input JSON file
    """
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        print(f"\nInput file structure:")
        print(f"Number of time steps: {len(data)}")
        
        # Check a few time steps
        for time_step in list(data.keys())[:3]:  # First three time steps
            print(f"\nTime step {time_step}:")
            if not data[time_step]:
                print("  - Empty time step data")
                continue
                
            print(f"  - Keys: {', '.join(data[time_step].keys())}")
            
            if 'nuclide' in data[time_step]:
                nuclide_data = data[time_step]['nuclide']
                print(f"  - Number of nuclides: {len(nuclide_data)}")
                
                # Show a sample of nuclides
                sample_nuclides = list(nuclide_data.keys())[:5]
                print(f"  - Sample nuclides: {', '.join(sample_nuclides)}")
                
                # Check for zero or negative values
                zero_or_negative = [nuc for nuc, val in nuclide_data.items() if val <= 0]
                if zero_or_negative:
                    print(f"  - WARNING: Found {len(zero_or_negative)} nuclides with zero or negative values")
                    print(f"    Examples: {', '.join(zero_or_negative[:5])}")
                
                # Calculate total atom density
                total_density = sum(nuclide_data.values())
                print(f"  - Total atom density: {total_density}")
                if total_density <= 0:
                    print(f"  - WARNING: Total atom density is zero or negative!")
            else:
                print("  - No 'nuclide' key found in time step data")
    
    except Exception as e:
        print(f"Error analyzing input file: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """
    Main function to process nuclide data and generate plots.
    """
    parser = argparse.ArgumentParser(
        description='Process nuclide data and calculate elemental abundances.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Process all elements in a file
  python iso2element.py -i ThEIRENE_FuelSalt_NuclideDensities.json -o processed_elements.json
  
  # Process specific elements
  python iso2element.py -i ThEIRENE_FuelSalt_NuclideDensities.json -o processed_elements.json -e li f be
  
  # Create a semi-log plot
  python iso2element.py -i ThEIRENE_FuelSalt_NuclideDensities.json -o processed_elements.json -p semilog
  
  # Print detailed output
  python iso2element.py -i ThEIRENE_FuelSalt_NuclideDensities.json -o processed_elements.json -v
        ''')
    
    parser.add_argument('-i', '--input', required=True, help='Input JSON file')
    parser.add_argument('-o', '--output', required=True, help='Output JSON file')
    parser.add_argument('-e', '--elements', nargs='+', help='Elements to include (space-separated)')
    parser.add_argument('-p', '--plot', choices=['stackplot', 'semilog', 'combined', 'all', 'none'], 
                        default='stackplot', help='Plot type')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print detailed output')
    parser.add_argument('--no-isotopes', action='store_true', help='Exclude isotopic contributions')
    parser.add_argument('--verify', action='store_true', help='Verify total mole percent')
    parser.add_argument('--plot-prefix', default='elemental_abundance', 
                        help='Prefix for plot filenames')
    parser.add_argument('--debug', action='store_true', help='Print debug information about the input file')
    
    args = parser.parse_args()
    
    try:
        # Debug input file if requested
        if args.debug:
            print("\nRunning input file debug analysis:")
            debug_input_file(args.input)
            
        # Process data
        processed_data = process_nuclide_data(
            args.input, 
            args.output, 
            elements_to_include=args.elements,
            plot_type=args.plot,
            include_isotopes=not args.no_isotopes
        )
        
        print(f"\nProcessing complete. Results saved to {args.output}")
        
        # Optional: Verify total mole percent
        if args.verify:
            print("\nVerifying Total Mole Percent:")
            verify_total_mole_percent(processed_data)
        
        # Optional: Print detailed information
        if args.verbose:
            print("\nDetailed Element Composition:")
            print_processed_data(processed_data, verbose=True)
        
        # Generate plots if requested
        if args.plot != 'none':
            generate_plots(processed_data, args.plot, args.plot_prefix)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # If run as a script, parse command line arguments
    main()
else:
    # Example usage when imported as a module
    print("Nuclide Vector Processor module loaded. Use process_nuclide_data() to process data.")