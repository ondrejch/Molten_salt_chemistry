"""
Integration Component for Thermochimica Post-Processor

This script orchestrates the execution of all post-processing components,
providing a unified interface to run the entire pipeline from data loading
to nuclide distribution calculation.
"""

import os
import argparse
import logging
import time
from datetime import datetime

# Import all component modules
from Data_Load_and_Parse import (
    load_fuel_salt_data,
    load_surrogate_vector,
    load_thermochimica_outputs
)
from Condensed_Report_generator import generate_condensed_report
from Redox_Analyzer import generate_redox_report
from Phase_Analysis_and_Report import (
    generate_phase_plot_all,
    generate_phase_plot_summary
)
from Phase_Specific_Data_Processor import (
    generate_phase_json
)
from Nuclide_Distribution_Calculator import (
    generate_nuclide_json
)


def setup_logging(output_directory):
    """Set up logging to file and console."""
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        
    log_file = os.path.join(output_directory, "post_processor.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def run_post_processor(input_directory, output_directory):
    """
    Run the entire post-processing pipeline.
    
    Parameters:
    -----------
    input_directory : str
        Directory containing all input files
    output_directory : str
        Directory for output files
    
    Returns:
    --------
    bool
        True if the post-processing completed successfully, False otherwise
    """
    # Set up logging
    logger = setup_logging(output_directory)
    
    start_time = time.time()
    logger.info(f"Starting post-processing pipeline at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Input directory: {input_directory}")
    logger.info(f"Output directory: {output_directory}")
    
    try:
        # Make sure output directory exists
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
            logger.info(f"Created output directory: {output_directory}")
        
        # Component 1: Load and parse data
        logger.info("Step 1: Loading and parsing input data...")
        
        fuel_salt_path = os.path.join(input_directory, "ThEIRENE_FuelSalt_processed_elements.json")
        surrogate_vector_path = os.path.join(input_directory, "surrogate_vector.json")
        
        fuel_salt_data = load_fuel_salt_data(fuel_salt_path)
        surrogate_vector_data = load_surrogate_vector(surrogate_vector_path)
        thermochimica_data = load_thermochimica_outputs(input_directory)
        
        logger.info(f"Loaded data for {len(thermochimica_data)} timesteps")
        
        # Component 2: Generate condensed report
        logger.info("Step 2: Generating condensed Thermochimica report...")
        condensed_report = generate_condensed_report(thermochimica_data)
        
        # Save condensed report
        condensed_report_path = os.path.join(output_directory, "Condensed_Thermochimica_Report.json")
        with open(condensed_report_path, 'w') as f:
            import json
            json.dump(condensed_report, f, indent=2)
        logger.info(f"Saved condensed report to {condensed_report_path}")
        
        # Component 3: Redox analysis
        logger.info("Step 3: Performing redox analysis...")
        redox_report_path = os.path.join(output_directory, "Redox_Report")
        generate_redox_report(thermochimica_data, redox_report_path)
        logger.info(f"Completed redox analysis and saved to {redox_report_path}")
        
        # Component 4: Phase analysis and reporting
        logger.info("Step 4: Generating phase analysis plots...")
        phase_plot_all_path = os.path.join(output_directory, "Phase_Plot_All.png")
        phase_plot_summary_path = os.path.join(output_directory, "Phase_Plot_Summary.png")
        
        generate_phase_plot_all(condensed_report, phase_plot_all_path)
        
        # Extract phase data for summary plot
        salt_data = {k: v for k, v in condensed_report.items() if v.get("phase_type") == "salt"}
        gas_data = {k: v for k, v in condensed_report.items() if v.get("phase_type") == "gas"}
        solids_data = {k: v for k, v in condensed_report.items() if v.get("phase_type") == "solid"}
        
        generate_phase_plot_summary(salt_data, gas_data, solids_data, phase_plot_summary_path)
        logger.info(f"Generated phase analysis plots at {output_directory}")
        
        # Component 5: Phase-specific data processor
        logger.info("Step 5: Generating phase-specific JSON files...")
        salt_json_path = os.path.join(output_directory, "Salt.json")
        gas_json_path = os.path.join(output_directory, "Gas.json")
        solids_json_path = os.path.join(output_directory, "Solids.json")
        
        # Process each phase type
        phase_types = ["salt", "gas", "solid"]
        output_paths = [salt_json_path, gas_json_path, solids_json_path]
        
        for phase_type, output_path in zip(phase_types, output_paths):
            phase_data = {k: v for k, v in condensed_report.items() if v.get("phase_type") == phase_type}
            if phase_data:
                generate_phase_json(phase_data, surrogate_vector_data, output_path, phase_type)
                logger.info(f"Generated {phase_type} JSON file at {output_path}")
            else:
                logger.warning(f"No {phase_type} phase data found, skipping JSON generation")
        
        # Component 6: Nuclide distribution calculator
        logger.info("Step 6: Calculating nuclide distributions...")
        salt_nuclides_path = os.path.join(output_directory, "Salt_nuclides.json")
        gas_nuclides_path = os.path.join(output_directory, "Gas_nuclides.json")
        solids_nuclides_path = os.path.join(output_directory, "Solids_nuclides.json")
        
        # Process each phase type for nuclide distributions
        phase_json_paths = [salt_json_path, gas_json_path, solids_json_path]
        nuclide_json_paths = [salt_nuclides_path, gas_nuclides_path, solids_nuclides_path]
        
        for phase_type, phase_path, nuclide_path in zip(phase_types, phase_json_paths, nuclide_json_paths):
            if os.path.exists(phase_path):
                generate_nuclide_json(phase_path, fuel_salt_data, surrogate_vector_data, nuclide_path, phase_type)
                logger.info(f"Generated {phase_type} nuclides JSON file at {nuclide_path}")
            else:
                logger.warning(f"No {phase_type} phase JSON file found, skipping nuclide distribution calculation")
        
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Post-processing pipeline completed successfully in {execution_time:.2f} seconds")
        return True
        
    except Exception as e:
        logger.error(f"Error in post-processing pipeline: {str(e)}", exc_info=True)
        return False


def main():
    """Main function to parse command line arguments and run the post-processor."""
    parser = argparse.ArgumentParser(description="Thermochimica Post-Processor")
    parser.add_argument("--input", "-i", required=True, help="Directory containing all input files")
    parser.add_argument("--output", "-o", required=True, help="Directory for output files")
    
    args = parser.parse_args()
    
    result = run_post_processor(args.input, args.output)
    
    if result:
        print("Post-processing completed successfully!")
    else:
        print("Post-processing failed. Check the log file for details.")
        exit(1)


if __name__ == "__main__":
    main()