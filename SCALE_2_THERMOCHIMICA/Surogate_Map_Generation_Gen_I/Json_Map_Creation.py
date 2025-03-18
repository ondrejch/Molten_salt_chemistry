import csv
import json
from collections import defaultdict

def csv_to_json(csv_file_path, json_file_path):
    """
    Convert CSV data to JSON format where surrogates are keys with candidates and match quality.
    
    Args:
        csv_file_path (str): Path to the input CSV file
        json_file_path (str): Path to output the JSON file
    """
    # Dictionary to store surrogates and their candidates
    surrogate_data = defaultdict(list)
    
    # Read CSV file
    with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        for row in csv_reader:
            # Check if this element has a surrogate defined
            if 'Surrogate' in row and row['Surrogate'] and row['Surrogate'].strip():
                surrogate = row['Surrogate'].strip()
                match_quality = row['Match_Quality'] if 'Match_Quality' in row else 'Unknown'
                
                # Add this element as a candidate to its surrogate
                surrogate_data[surrogate].append({
                    'Symbol': row['Symbol'],
                    'Name': row['Name'],
                    'AtomicNumber': row['AtomicNumber'],
                    'Match_Quality': match_quality
                })
    
    # Handle self-representing elements (where element is its own surrogate)
    for row in surrogate_data.values():
        for candidate in row:
            if candidate['Symbol'] not in surrogate_data and candidate['Match_Quality'].lower() == 'self':
                surrogate_data[candidate['Symbol']] = []
    
    # Write to JSON file
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(surrogate_data, json_file, indent=4)
    
    print(f"Successfully converted CSV to JSON. Output saved to {json_file_path}")

if __name__ == "__main__":
    # Update these paths to match your file locations
    input_csv = "PubChemElements_with_surrogates_updated3.csv"
    output_json = "surrogates_and_candidates.json"
    
    csv_to_json(input_csv, output_json)