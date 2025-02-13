# Periodic Table Surrogate Element Mapper

A Python-based toolkit for analyzing and mapping surrogate elements in the periodic table. This project provides tools to identify and visualize suitable surrogate elements based on chemical properties and redox potentials.

## Overview

The toolkit consists of two main components:
1. A periodic table data manager (`periodic_table.py`) that handles element data and properties
2. A surrogate mapping system (`surrogate_mapper.py`) that identifies suitable surrogate elements based on various chemical properties
3. A visualization tool (`plot_surrogate_periodic_table.py`) that generates a color-coded periodic table showing surrogate relationships

## Files in Repository

- `periodic_table.py` & `surrogate_mapper.py`: Main Python source code files
- `PubChemElements_all.csv`: Source data file containing periodic table elements and their properties
- `PubChemElements_with_surrogates.csv`: Updated dataset including surrogate mappings
- `output.txt`: Example output of the surrogate mapping report
- `Surrogate_periodic_table.png`: Visualization of the surrogate element mappings

## Requirements 

```bash
# Install required packages
pip install pandas numpy matplotlib bokeh
```

## Usage

### 1. Loading and Managing Periodic Table Data

```python
from periodic_table import PeriodicTable

# Load data from CSV
periodic_table = PeriodicTable.from_csv_file('PubChemElements_all.csv')

# Access element properties
hydrogen = periodic_table.get_by_symbol('H')
print(f"Hydrogen properties:")
print(f"Atomic Mass: {hydrogen.atomic_mass}")
print(f"Electronegativity: {hydrogen.electronegativity}")
```

### 2. Generating Surrogate Mappings

```python
from surrogate_mapper import SurrogateMapper

# Initialize mapper
mapper = SurrogateMapper(periodic_table)

# Generate mappings
mappings = mapper.generate_surrogate_mapping()

# Print detailed report
mapper.print_mapping_report(mappings)

# Update CSV with mappings
mapper.update_csv_with_mappings(
    original_csv_path="PubChemElements_all.csv",
    mappings=mappings,
    periodic_table=periodic_table,
    output_csv_path="PubChemElements_with_surrogates.csv"
)
```

### 3. Visualizing Results

```python
from plot_surrogate_periodic_table import plot_surrogate_periodic_table

# Generate visualization
plot_surrogate_periodic_table(
    csv_file='PubChemElements_with_surrogates.csv',
    output_filename='Surrogate_periodic_table.png',
    figsize=(20, 12)
)
```

## Data Format

### Required CSV Columns

The input CSV file (`PubChemElements_all.csv`) should contain the following essential columns:

- `AtomicNumber`: Integer
- `Symbol`: Element symbol (e.g., 'H', 'He')
- `Name`: Element name
- `AtomicMass`: Float
- `ElectronConfiguration`: String
- `Electronegativity`: Float
- `AtomicRadius`: Integer
- `IonizationEnergy`: Float
- `ElectronAffinity`: Float
- `OxidationStates`: String
- `StandardState`: String
- `MeltingPoint`: Float
- `BoilingPoint`: Float
- `Density`: Float
- `GroupBlock`: String
- `Key`: String (redox states)
- `Half-Reaction`: String
- `Standard Potential`: Float

## Matching Criteria

The surrogate mapping algorithm uses the following criteria to match elements:

1. **Good Match** (Score 1):
   - Elements share the same redox states
   - Standard potential difference ≤ 0.4V

2. **Decent Match** (Score 2):
   - Elements share some redox states
   - Standard potential difference ≤ 1.5V

3. **Poor Match** (Score 3):
   - Similar electronegativity (difference < 0.5) or
   - Similar melting point (difference < 200K)

## Output Files

1. **PubChemElements_with_surrogates.csv**: Original data plus:
   - `Surrogate`: Symbol of matched surrogate element
   - `Match_Quality`: 'Good', 'Decent', 'Poor', or 'self'

2. **Surrogate_periodic_table.png**: Visual representation showing:
   - Color-coded surrogate groups
   - Match quality indicators
   - Self-representing elements

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

TBD

## Acknowledgments

- Data sourced from PubChem
- Visualization based on Bokeh's periodic table sample data

## Contact

For questions and feedback, please open an issue in the GitHub repository.
