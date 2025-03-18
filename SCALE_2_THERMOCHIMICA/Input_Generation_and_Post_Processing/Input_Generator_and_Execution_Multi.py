#!/usr/bin/env python3
"""
Thermochimica input file generator from surrogate vector JSON.
This module generates Thermochimica input files for each time step in a surrogate vector JSON file.
"""

import os
import json
import argparse
import subprocess
from typing import Dict, Any, Optional
import sys
import shutil
import multiprocessing

# Import ELEMENTS from tcflibe
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tcflibe import ELEMENTS

class ThermochimicaWrapper:
    """Simplified wrapper for Thermochimica that doesn't require file assertions"""

    def __init__(self, datafile_path=None, binary_path=None):
        """Initialize with optional paths that can be set later"""
        self.datafile_path = datafile_path or os.path.expanduser('~/thermochimica/data/MSTDB-TC_V3.1_Fluorides_No_Func.dat')
        self.binary_path = binary_path or os.path.expanduser('~/thermochimica/bin/InputScriptMode')
        self.deck_name = 'my_tc.ti'  # Thermochimica input file name
        self.thermo_output_name = self.deck_name.replace('.ti', '.json')
        self.header = ''  # Run header
        self.temps_k = '900'  # Default temperature
        self.elements = {}  # Molar amounts of elements

    def run_tc(self):
        """Run a Thermochimica deck"""
        # Check if binary exists
        if not os.path.isfile(self.binary_path):
            print(f"WARNING: Thermochimica binary not found at {self.binary_path}")
            print("Input file was generated but calculations cannot be run.")
            return False

        # Thermochimica writes output to a specific location
        expected_output = "/home/bclayto4/thermochimica/outputs/thermoout.json"
        log_file = self.deck_name.replace('.ti', '.log')
        
        try:
            # Run Thermochimica in the current directory
            tchem_process = subprocess.run([self.binary_path, self.deck_name], 
                                        capture_output=True, text=True, check=False)
            
            # Always save the stdout/stderr to a log file
            with open(log_file, 'w') as f:
                f.write("STDOUT:\n")
                f.write(tchem_process.stdout)
                f.write("\nSTDERR:\n")
                f.write(tchem_process.stderr)
            
            # Check if thermoout.json was created at the expected location
            if os.path.exists(expected_output):
                # Move it to the desired output filename
                shutil.move(expected_output, self.thermo_output_name)
                print(f"Successfully created output file: {self.thermo_output_name}")
                return True
            else:
                print(f"Thermochimica execution finished but no output file was created.")
                print(f"Command output: {tchem_process.stdout}")
                if tchem_process.stderr:
                    print(f"Command errors: {tchem_process.stderr}")
                return False
        except Exception as e:
            print(f"Error running Thermochimica: {e}")
            return False

    def tc_input(self):
        """Makes Thermochimica input file based on fuel salt object"""
        output = f'''! {self.header}

! Initialize variables:
pressure          = 1
temperature       = {self.temps_k}
'''
        for e, v in self.elements.items():
            if e.lower() in ELEMENTS:
                z = ELEMENTS.index(e.lower())
                output += f'mass({z})           = {v}     !{e}\n'
            else:
                print(f"WARNING: Element {e} not found in ELEMENTS list, skipping")
        
        output += f'''temperature unit  = K
pressure unit     = atm
mass unit         = moles
data file         = {self.datafile_path}
step together     = .FALSE.

! Specify output and debug modes:
print mode        = 1
debug mode        = .FALSE.
reinit            = .TRUE.

! Additional Settings: 
heat capacity     = .FALSE.
write json        = .TRUE.
reinitialization  = .FALSE.
fuzzy             = .FALSE.
gibbs min         = .FALSE.
'''
        return output


class ThermochimicaInputGenerator:
    """Generator for Thermochimica input files from surrogate vector data"""
    
    def __init__(self, 
                json_file_path: str, 
                output_dir: str = "tc_inputs", 
                main_file_name: str = "ThEIRNE_Cycle",
                temperature: str = "900",
                pressure: str = "1",
                datafile_path: str = None,
                binary_path: str = None,
                scale_factor: float = 1.0,
                time_step_dir_template: str = "timestep_{time_step}"):
        """
        Initialize the Thermochimica input generator.
        
        Args:
            json_file_path: Path to the surrogate_vector.json file
            output_dir: Directory to store the generated input files
            main_file_name: Base name for the input files
            temperature: Temperature for the Thermochimica calculation (K)
            pressure: Pressure for the Thermochimica calculation (atm)
            datafile_path: Path to Thermochimica data file (optional)
            binary_path: Path to Thermochimica binary (optional)
            scale_factor: Factor to multiply mole percentages by
            time_step_dir_template: Template for time step directory naming
        """
        self.json_file_path = json_file_path
        self.output_dir = output_dir
        self.main_file_name = main_file_name
        self.temperature = temperature
        self.pressure = pressure
        self.scale_factor = scale_factor
        self.time_step_dir_template = time_step_dir_template
        
        # Initialize wrapper with optional custom paths
        self.tc = ThermochimicaWrapper(
            datafile_path=datafile_path,
            binary_path=binary_path
        )
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Check if json file exists
        if not os.path.isfile(json_file_path):
            raise FileNotFoundError(f"Surrogate vector JSON file not found: {json_file_path}")
            
        # Load the surrogate vector data
        try:
            with open(json_file_path, 'r') as f:
                self.surrogate_data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in file: {json_file_path}")

    def get_time_step_dir(self, time_step: str) -> str:
        """Get the directory name for a specific time step based on the template."""
        return os.path.join(self.output_dir, self.time_step_dir_template.format(time_step=time_step))
            
    def generate_input_files(self) -> None:
        """Generate Thermochimica input files for each time step"""
        if "surrogate_vector" not in self.surrogate_data:
            raise ValueError("Invalid surrogate vector JSON format. Expected 'surrogate_vector' key.")
        
        time_steps = self.surrogate_data["surrogate_vector"]
        for time_step, composition in time_steps.items():
            # Create directory for this time step
            time_step_dir = self.get_time_step_dir(time_step)
            if not os.path.exists(time_step_dir):
                os.makedirs(time_step_dir)
            
            # Generate input file name
            input_file_name = f"{self.main_file_name}_t{time_step}.ti"
            input_file_path = os.path.join(time_step_dir, input_file_name)
            
            # Extract elements and mole percentages
            elements_dict = self._extract_elements_mole_percent(composition)
            
            # Generate and write the input file
            self._generate_input_file(input_file_path, elements_dict, time_step)
            
            print(f"Generated input file for time step {time_step}: {input_file_path}")
    
    def _extract_elements_mole_percent(self, composition: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """
        Extract element mole percentages from the composition data.
        
        Args:
            composition: Dictionary containing element data for a time step
            
        Returns:
            Dictionary mapping element symbols to mole percentages, scaled by scale_factor
        """
        elements_dict = {}
        
        for element, data in composition.items():
            if "mole_percent" in data:
                # Apply scale factor to the mole percentage value
                elements_dict[element.lower()] = data["mole_percent"] * self.scale_factor / 100.0
        
        return elements_dict
    
    def _generate_input_file(self, file_path: str, elements: Dict[str, float], time_step: str) -> None:
        """
        Generate a Thermochimica input file for a specific time step.
        
        Args:
            file_path: Path to write the input file
            elements: Dictionary mapping element symbols to mole percentages
            time_step: Time step identifier
        """
        # Set up Thermochimica object
        self.tc.header = f"Surrogate Vector Calculation for Time Step {time_step} (Scale Factor: {self.scale_factor})"
        self.tc.temps_k = self.temperature
        self.tc.elements = elements
        self.tc.deck_name = os.path.basename(file_path)
        self.tc.thermo_output_name = os.path.join(os.path.dirname(file_path), 
                                               os.path.basename(file_path).replace('.ti', '.json'))
        
        # Write the input file
        with open(file_path, 'w') as f:
            f.write(self.tc.tc_input())

    def _run_tc_for_time_step(self, time_step: str) -> None:
        """Helper function to run Thermochimica for a single time step."""
        time_step_dir = self.get_time_step_dir(time_step)
        input_file_name = f"{self.main_file_name}_t{time_step}.ti"
        
        # Save current directory to return to it later
        current_dir = os.getcwd()

        # Change to the time step directory
        os.chdir(time_step_dir)

        # Set the deck name and output name
        self.tc.deck_name = input_file_name
        self.tc.thermo_output_name = input_file_name.replace('.ti', '.json')

        print(f"Running Thermochimica for time step {time_step}...")

        success = self.tc.run_tc()

        if success:
            print(f"Successfully ran Thermochimica for time step {time_step}")
        else:
            print(f"Failed to run Thermochimica for time step {time_step}")

        # Return to original directory
        os.chdir(current_dir)

    def run_calculations(self) -> None:
        """Run Thermochimica calculations in parallel."""
        time_steps = list(self.surrogate_data["surrogate_vector"].keys())

        # Use multiprocessing to run calculations in parallel
        with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
            pool.map(self._run_tc_for_time_step, time_steps)


def main():
    """Main function to parse command line arguments and run the generator"""
    parser = argparse.ArgumentParser(description="Generate Thermochimica input files from surrogate vector JSON")
    parser.add_argument("json_file", help="Path to the surrogate_vector.json file")
    parser.add_argument("-o", "--output-dir", default="tc_inputs", 
                        help="Directory to store the generated input files")
    parser.add_argument("-n", "--name", default="ThEIRNE_Cycle", 
                        help="Base name for the input files")
    parser.add_argument("-t", "--temperature", default="900", 
                        help="Temperature for the Thermochimica calculation (K)")
    parser.add_argument("-p", "--pressure", default="1", 
                        help="Pressure for the Thermochimica calculation (atm)")
    parser.add_argument("-r", "--run", action="store_true", 
                        help="Run Thermochimica calculations after generating input files")
    parser.add_argument("--datafile", 
                        help="Path to Thermochimica data file")
    parser.add_argument("--binary", 
                        help="Path to Thermochimica binary")
    parser.add_argument("-s", "--scale", type=float, default=1.0,
                        help="Scale factor to multiply mole percentages (default: 1.0)")
    parser.add_argument("-d", "--dir-template", default="timestep_{time_step}",
                        help="Template for time step directory naming (use {time_step} as placeholder)")
    
    args = parser.parse_args()
    
    try:
        generator = ThermochimicaInputGenerator(
            json_file_path=args.json_file,
            output_dir=args.output_dir,
            main_file_name=args.name,
            temperature=args.temperature,
            pressure=args.pressure,
            datafile_path=args.datafile,
            binary_path=args.binary,
            scale_factor=args.scale,
            time_step_dir_template=args.dir_template
        )
        
        generator.generate_input_files()
        
        if args.run:
            generator.run_calculations()
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())