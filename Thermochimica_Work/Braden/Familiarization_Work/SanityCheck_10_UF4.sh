#!/bin/bash

# Specify the target directory name here (replace 'FileName' with the file you are looking for)
target_file="SanityCheck_10_UF4"

# Find the directory with the same name as the file (without extension)
target_dir="${target_file%.*}"

# Check if the directory exists
if [ -d "$target_dir" ]; then
    # Enter the directory
    cd "$target_dir" || exit

    # Create an output file for the entire directory's output
    

    # Loop through all files in the directory
    for file in *; do
        # Check if it's a regular file
        if [ -f "$file" ]; then
            output_file="Script_out_${target_dir}_${file%.*}.out"
            # Run the InputScriptMode command and save output to the directory-specific output file
            /home/bclayto4/thermochimica/bin/InputScriptMode "$file" >> "$output_file"

            # Copy the saved data file to a new file named after the current file being processed
            cp ../../outputs/thermoout.json "${file%.*}_thermout.json"
            echo "Processing complete. Output saved to $output_file"
            echo "file ${file%.*} completed, proceeding to the next."
        fi
        
    done


else
    echo "Directory $target_dir not found."
fi
