import csv
import pandas as pd
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

@dataclass
class Element:
    """Class representing a chemical element with all its properties."""
    atomic_number: int
    symbol: str
    name: str
    atomic_mass: float
    cpk_hex_color: str
    electron_configuration: str
    electronegativity: Optional[float]
    atomic_radius: Optional[int]
    ionization_energy: Optional[float]
    electron_affinity: Optional[float]
    oxidation_states: Optional[str]
    standard_state: str
    melting_point: Optional[float]
    boiling_point: Optional[float]
    density: Optional[float]
    group_block: str
    year_discovered: str
    fluorides: Optional[str]
    version_compatibility: Optional[str]
    abundance: Optional[float]
    impact: Optional[str]
    risk: Optional[str]
    surrogate: Optional[str]
    # New fields
    key: Optional[str]  # Single value or list
    half_reaction: Optional[str]  # Single value or list
    standard_potential: Optional[str]  # Single value or list

    def __post_init__(self):
        """Method to handle any post-initialization logic, such as validation."""
        if self.surrogate:
            if not isinstance(self.surrogate, str) or len(self.surrogate) > 2:
                raise ValueError(f"Invalid surrogate value: {self.surrogate}. It should be a valid element symbol.")
        
        # Convert string lists to actual lists if they contain multiple values
        if self.key and ',' in self.key:
            self.key = [k.strip() for k in self.key.split(',')]
        if self.half_reaction and ',' in self.half_reaction:
            self.half_reaction = [r.strip() for r in self.half_reaction.split(',')]
        if self.standard_potential and ',' in self.standard_potential:
            self.standard_potential = [p.strip() for p in self.standard_potential.split(',')]

class PeriodicTable:
    """Class to manage the periodic table and provide easy element lookups."""
    def __init__(self):
        self.elements = {}
        self.atomic_numbers = {}
        self.element_names = {}

    def add_element(self, element: Element):
        """Add an element to the periodic table."""
        self.elements[element.symbol] = element
        self.atomic_numbers[element.atomic_number] = element
        self.element_names[element.name.lower()] = element

    
    @classmethod
    def from_csv_file(cls, file_path: str | Path) -> 'PeriodicTable':
        """Create a PeriodicTable instance from a CSV file."""
        periodic_table = cls()
        file_path = Path(file_path)
    
        try:
            with open(file_path, 'r', encoding='ISO-8859-1') as file:  # Change encoding to ISO-8859-1 or try Windows-1252 if needed
                reader = csv.DictReader(file)
    
                for row in reader:
                    # Clean up row data
                    cleaned_row = {k.strip(): (v.strip() if v else None) for k, v in row.items()}
    
                    try:
                        element = Element(
                            atomic_number=int(cleaned_row['AtomicNumber']),
                            symbol=cleaned_row['Symbol'],
                            name=cleaned_row['Name'],
                            atomic_mass=float(cleaned_row['AtomicMass']) if cleaned_row['AtomicMass'] else None,
                            cpk_hex_color=cleaned_row['CPKHexColor'],
                            electron_configuration=cleaned_row['ElectronConfiguration'],
                            electronegativity=float(cleaned_row['Electronegativity']) if cleaned_row['Electronegativity'] else None,
                            atomic_radius=int(cleaned_row['AtomicRadius']) if cleaned_row['AtomicRadius'] else None,
                            ionization_energy=float(cleaned_row['IonizationEnergy']) if cleaned_row['IonizationEnergy'] else None,
                            electron_affinity=float(cleaned_row['ElectronAffinity']) if cleaned_row['ElectronAffinity'] else None,
                            oxidation_states=cleaned_row['OxidationStates'],
                            standard_state=cleaned_row['StandardState'],
                            melting_point=float(cleaned_row['MeltingPoint']) if cleaned_row['MeltingPoint'] else None,
                            boiling_point=float(cleaned_row['BoilingPoint']) if cleaned_row['BoilingPoint'] else None,
                            density=float(cleaned_row['Density']) if cleaned_row['Density'] else None,
                            group_block=cleaned_row['GroupBlock'],
                            year_discovered=cleaned_row['YearDiscovered'],
                            fluorides=cleaned_row['Florides'],
                            version_compatibility=cleaned_row['Version Compatability'],
                            abundance=float(cleaned_row['Abundance']) if cleaned_row['Abundance'] else None,
                            impact=cleaned_row['Impact'],
                            risk=cleaned_row['Risk'],
                            surrogate=cleaned_row['Surrogate'] if 'Surrogate' in cleaned_row else None,
                            # New fields
                            key=cleaned_row['Key'] if cleaned_row['Key'] else None,
                            half_reaction=cleaned_row['Half-Reaction'] if cleaned_row['Half-Reaction'] else None,
                            standard_potential=cleaned_row['Standard Potential'] if cleaned_row['Standard Potential'] else None
                        )
                        periodic_table.add_element(element)
                    except Exception as e:
                        print(f"Error processing element {cleaned_row.get('Symbol', 'unknown')}: {str(e)}")
                        continue
    
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find file: {file_path}")
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
            raise
    
        return periodic_table


    @classmethod
    def from_excel_file(cls, file_path: str | Path, sheet_name: str = None) -> 'PeriodicTable':
        """Create a PeriodicTable instance from an Excel file."""
        periodic_table = cls()
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                
                # Clean up row data
                cleaned_row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row_dict.items()}
                
                try:
                    element = Element(
                        atomic_number=int(cleaned_row['AtomicNumber']),
                        symbol=cleaned_row['Symbol'],
                        name=cleaned_row['Name'],
                        atomic_mass=float(cleaned_row['AtomicMass']) if pd.notna(cleaned_row['AtomicMass']) else None,
                        cpk_hex_color=cleaned_row['CPKHexColor'],
                        electron_configuration=cleaned_row['ElectronConfiguration'],
                        electronegativity=float(cleaned_row['Electronegativity']) if pd.notna(cleaned_row['Electronegativity']) else None,
                        atomic_radius=int(cleaned_row['AtomicRadius']) if pd.notna(cleaned_row['AtomicRadius']) else None,
                        ionization_energy=float(cleaned_row['IonizationEnergy']) if pd.notna(cleaned_row['IonizationEnergy']) else None,
                        electron_affinity=float(cleaned_row['ElectronAffinity']) if pd.notna(cleaned_row['ElectronAffinity']) else None,
                        oxidation_states=cleaned_row['OxidationStates'],
                        standard_state=cleaned_row['StandardState'],
                        melting_point=float(cleaned_row['MeltingPoint']) if pd.notna(cleaned_row['MeltingPoint']) else None,
                        boiling_point=float(cleaned_row['BoilingPoint']) if pd.notna(cleaned_row['BoilingPoint']) else None,
                        density=float(cleaned_row['Density']) if pd.notna(cleaned_row['Density']) else None,
                        group_block=cleaned_row['GroupBlock'],
                        year_discovered=cleaned_row['YearDiscovered'],
                        fluorides=cleaned_row['Florides'],
                        version_compatibility=cleaned_row['Version Compatability'],
                        abundance=float(cleaned_row['Abundance']) if pd.notna(cleaned_row['Abundance']) else None,
                        impact=cleaned_row['Impact'],
                        risk=cleaned_row['Risk'],
                        surrogate=cleaned_row['Surrogate'] if 'Surrogate' in cleaned_row else None,
                        # New fields
                        key=cleaned_row['Key'] if pd.notna(cleaned_row.get('Key')) else None,
                        half_reaction=cleaned_row['Half-Reaction'] if pd.notna(cleaned_row.get('Half-Reaction')) else None,
                        standard_potential=cleaned_row['Standard Potential'] if pd.notna(cleaned_row.get('Standard Potential')) else None
                    )
                    periodic_table.add_element(element)
                except Exception as e:
                    print(f"Error processing element {cleaned_row.get('Symbol', 'unknown')}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"Error reading Excel file: {str(e)}")
            raise
            
        return periodic_table

    def get_by_symbol(self, symbol: str) -> Optional[Element]:
        """Look up an element by its symbol."""
        return self.elements.get(symbol)

    def get_by_atomic_number(self, atomic_number: int) -> Optional[Element]:
        """Look up an element by its atomic number."""
        return self.atomic_numbers.get(atomic_number)

    def get_by_name(self, name: str) -> Optional[Element]:
        """Look up an element by its name (case insensitive)."""
        return self.element_names.get(name.lower())

    def get_elements_by_group(self, group: str) -> List[Element]:
        """Get all elements in a specific group block."""
        return [elem for elem in self.elements.values() if elem.group_block == group]

    def get_compatible_elements(self, version: str) -> List[Element]:
        """Get all elements compatible with a specific version."""
        compatible_elements = []
        for elem in self.elements.values():
            if elem.version_compatibility and version in elem.version_compatibility:
                compatible_elements.append(elem)
        return compatible_elements
# For CSV file
periodic_table = PeriodicTable.from_csv_file('PubChemElements_all.csv')

# Or for Excel file
#periodic_table = PeriodicTable.from_excel_file('PubChemElements_all.xlsx')

# Example usage:
hydrogen = periodic_table.get_by_symbol('H')
print(f"Hydrogen properties:")
print(f"Atomic Mass: {hydrogen.atomic_mass}")
print(f"Version Compatibility: {hydrogen.version_compatibility}")
print(f"Abundance: {hydrogen.abundance}")
print(f"Impact: {hydrogen.impact}")
print(f"Risk: {hydrogen.risk}")

# Get all V3 compatible elements
v3_elements = periodic_table.get_compatible_elements('V3')
print(f"\nV3 Compatible Elements:")
for element in v3_elements:
    print(f"{element.symbol}: {element.name}")
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple, Set
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class SurrogateMatch:
    """Class to store surrogate matching results"""
    candidate: Element
    surrogate: Element
    score: int  # 1: Good, 2: Decent, 3: Poor
    potential_difference: Optional[float]
    electronegativity_difference: Optional[float]
    electron_affinity_difference: Optional[float]
    melting_point_difference: Optional[float]
    match_reason: str

class SurrogateMapper:
    def __init__(self, periodic_table: PeriodicTable):
        self.periodic_table = periodic_table
        self.surrogate_elements = self._get_surrogate_elements()
    
    def _calculate_property_difference(self, val1: Optional[float], val2: Optional[float]) -> Optional[float]:
        """Calculate difference between two optional property values"""
        if val1 is None or val2 is None:
            return None
        return abs(val1 - val2)
        
    def _get_surrogate_elements(self) -> List[Element]:
        """Get all elements that are marked as surrogates in the database"""
        return [elem for elem in self.periodic_table.elements.values() 
                if elem.surrogate and elem.surrogate.lower() == elem.symbol.lower()]

    def _safe_float_conversion(self, value: Optional[str]) -> Optional[float]:
        """Safely convert string to float, handling None and empty strings"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _get_element_keys(self, element: Element) -> Tuple[List[str], List[float]]:
        """Get sorted keys and their corresponding potentials for an element"""
        if not element.key or not element.standard_potential:
            return [], []
        
        # Convert to lists if they're single values
        keys = element.key if isinstance(element.key, list) else [element.key]
        potentials = element.standard_potential if isinstance(element.standard_potential, list) else [element.standard_potential]
        
        # Create pairs of valid keys and potentials
        valid_pairs = []
        for k, p in zip(keys, potentials):
            potential = self._safe_float_conversion(p)
            if potential is not None and k:
                valid_pairs.append((k, potential))
        
        # Sort pairs by key
        valid_pairs.sort(key=lambda x: x[0])
        return [p[0] for p in valid_pairs], [p[1] for p in valid_pairs]

    def _group_elements_by_keys(self) -> Dict[Tuple[str, ...], List[Element]]:
        """Group elements by their available keys"""
        key_groups = {}
        
        for element in self.periodic_table.elements.values():
            keys, _ = self._get_element_keys(element)
            if keys:  # Only include elements with valid keys
                key_tuple = tuple(sorted(keys))
                if key_tuple not in key_groups:
                    key_groups[key_tuple] = []
                key_groups[key_tuple].append(element)
        
        return key_groups

    def _calculate_potential_differences(self, element1: Element, element2: Element) -> Dict[str, float]:
        """Calculate potential differences for each matching key between two elements"""
        keys1, potentials1 = self._get_element_keys(element1)
        keys2, potentials2 = self._get_element_keys(element2)
        
        differences = {}
        for k1, p1 in zip(keys1, potentials1):
            for k2, p2 in zip(keys2, potentials2):
                if k1 == k2:
                    differences[k1] = abs(p1 - p2)
        
        return differences

    def _find_best_match_in_group(self, candidate: Element, surrogates: List[Element]) -> Optional[Tuple[Element, float, str]]:
        """Find the best matching surrogate within a group of elements with the same keys"""
        best_surrogate = None
        best_diff = float('inf')
        match_type = ""
        
        for surrogate in surrogates:
            differences = self._calculate_potential_differences(candidate, surrogate)
            if not differences:
                continue
                
            # Check if all differences are within the "good" threshold (0.4)
            max_diff = max(differences.values())
            if max_diff <= 0.4:
                if max_diff < best_diff:
                    best_diff = max_diff
                    best_surrogate = surrogate
                    match_type = "good"
            # If not already found a good match, check for decent match (threshold 1.5)
            elif max_diff <= 1.5 and best_diff > 0.4:
                if max_diff < best_diff:
                    best_diff = max_diff
                    best_surrogate = surrogate
                    match_type = "decent"
                    
        return (best_surrogate, best_diff, match_type) if best_surrogate else None

    def _find_poor_match(self, candidate: Element) -> Optional[Tuple[Element, str]]:
        """Find a poor match based on electronegativity or melting point"""
        best_surrogate = None
        match_reason = ""
        min_en_diff = float('inf')
        min_mp_diff = float('inf')
        
        for surrogate in self.surrogate_elements:
            # Check electronegativity
            if candidate.electronegativity and surrogate.electronegativity:
                en_diff = abs(candidate.electronegativity - surrogate.electronegativity)
                if en_diff < min_en_diff and en_diff < 0.5:
                    min_en_diff = en_diff
                    best_surrogate = surrogate
                    match_reason = "electronegativity"
                    
            # Check melting point if no good electronegativity match found
            if min_en_diff == float('inf') and candidate.melting_point and surrogate.melting_point:
                mp_diff = abs(candidate.melting_point - surrogate.melting_point)
                if mp_diff < min_mp_diff and mp_diff < 200:
                    min_mp_diff = mp_diff
                    best_surrogate = surrogate
                    match_reason = "melting point"
                    
        return (best_surrogate, match_reason) if best_surrogate else None

    def find_surrogate(self, candidate: Element) -> Optional[SurrogateMatch]:
        """Find the best surrogate match for a candidate element using the new methodology"""
        if candidate in self.surrogate_elements:
            return None
            
        # Get groups of elements by their keys
        key_groups = self._group_elements_by_keys()
        
        # First try to find match in same key group
        candidate_keys, _ = self._get_element_keys(candidate)
        candidate_key_tuple = tuple(sorted(candidate_keys))
        
        if candidate_key_tuple in key_groups:
            surrogates_in_group = [elem for elem in key_groups[candidate_key_tuple] 
                                 if elem in self.surrogate_elements]
            if surrogates_in_group:
                match_result = self._find_best_match_in_group(candidate, surrogates_in_group)
                if match_result:
                    surrogate, diff, match_type = match_result
                    return SurrogateMatch(
                        candidate=candidate,
                        surrogate=surrogate,
                        score=1 if match_type == "good" else 2,
                        potential_difference=diff,
                        electronegativity_difference=self._calculate_property_difference(
                            candidate.electronegativity, surrogate.electronegativity),
                        electron_affinity_difference=self._calculate_property_difference(
                            candidate.electron_affinity, surrogate.electron_affinity),
                        melting_point_difference=self._calculate_property_difference(
                            candidate.melting_point, surrogate.melting_point),
                        match_reason=f"{match_type.capitalize()} match in valence states"
                    )
        
        # If no match found in same key group, try finding decent match across all groups
        for surrogate in self.surrogate_elements:
            differences = self._calculate_potential_differences(candidate, surrogate)
            if differences and min(differences.values()) <= 1.5:
                return SurrogateMatch(
                    candidate=candidate,
                    surrogate=surrogate,
                    score=2,
                    potential_difference=min(differences.values()),
                    electronegativity_difference=self._calculate_property_difference(
                        candidate.electronegativity, surrogate.electronegativity),
                    electron_affinity_difference=self._calculate_property_difference(
                        candidate.electron_affinity, surrogate.electron_affinity),
                    melting_point_difference=self._calculate_property_difference(
                        candidate.melting_point, surrogate.melting_point),
                    match_reason="Decent match based on closest potential"
                )
        
        # If still no match, try poor matching based on electronegativity or melting point
        poor_match = self._find_poor_match(candidate)
        if poor_match:
            surrogate, reason = poor_match
            return SurrogateMatch(
                candidate=candidate,
                surrogate=surrogate,
                score=3,
                potential_difference=None,
                electronegativity_difference=self._calculate_property_difference(
                    candidate.electronegativity, surrogate.electronegativity),
                electron_affinity_difference=self._calculate_property_difference(
                    candidate.electron_affinity, surrogate.electron_affinity),
                melting_point_difference=self._calculate_property_difference(
                    candidate.melting_point, surrogate.melting_point),
                match_reason=f"Poor match based on similar {reason}"
            )
            
        return None

    def generate_surrogate_mapping(self) -> Dict[str, SurrogateMatch]:
        """Generate surrogate mappings for all suitable elements"""
        mappings = {}
        for element in self.periodic_table.elements.values():
            if element not in self.surrogate_elements:
                match = self.find_surrogate(element)
                if match:
                    mappings[element.symbol] = match
        return mappings
    def print_mapping_report(self, mappings: Dict[str, SurrogateMatch]) -> None:
        """Print a detailed report of the surrogate mappings, grouped by surrogate elements"""
        print("\nSurrogate Mapping Report")
        print("=" * 80)
        
        # Group mappings by surrogate element
        surrogate_groups = {}
        for symbol, match in mappings.items():
            if match.surrogate.symbol not in surrogate_groups:
                surrogate_groups[match.surrogate.symbol] = []
            surrogate_groups[match.surrogate.symbol].append(match)
        
        # Print report for each surrogate
        for surrogate_symbol, candidate_matches in sorted(surrogate_groups.items()):
            print(f"\n{'='*40}")
            print(f"Surrogate Element: {candidate_matches[0].surrogate.symbol} ({candidate_matches[0].surrogate.name})")
            print(f"{'='*40}")
            
            # Print details for each candidate matched to this surrogate
            for match in sorted(candidate_matches, key=lambda x: x.candidate.symbol):
                print(f"\nCandidate: {match.candidate.symbol} ({match.candidate.name})")
                print(f"Match Quality: {'Good' if match.score == 1 else 'Decent' if match.score == 2 else 'Poor'}")
                print(f"Reason: {match.match_reason}")
                
                print("Differences:")
                if match.potential_difference is not None:
                    print(f"  Standard Potential: {match.potential_difference:.3f}")
                if match.electronegativity_difference is not None:
                    print(f"  Electronegativity: {match.electronegativity_difference:.3f}")
                if match.electron_affinity_difference is not None:
                    print(f"  Electron Affinity: {match.electron_affinity_difference:.3f}")
                if match.melting_point_difference is not None:
                    print(f"  Melting Point: {match.melting_point_difference:.1f}K")
                
                # Add keys and standard potentials for comparison
                candidate_keys, candidate_potentials = self._get_element_keys(match.candidate)
                surrogate_keys, surrogate_potentials = self._get_element_keys(match.surrogate)
                
                print("\nCandidate Keys and Standard Potentials:")
                for key, potential in zip(candidate_keys, candidate_potentials):
                    print(f"  {key}: {potential:.3f}")
                
                print("\nSurrogate Keys and Standard Potentials:")
                for key, potential in zip(surrogate_keys, surrogate_potentials):
                    print(f"  {key}: {potential:.3f}")
                
                print("-" * 40)
    # def print_mapping_report(self, mappings: Dict[str, SurrogateMatch]) -> None:
    #     """Print a detailed report of the surrogate mappings, including keys and standard potentials."""
    #     print("\nSurrogate Mapping Report")
    #     print("=" * 80)
        
    #     for symbol, match in sorted(mappings.items()):
    #         print(f"\nCandidate: {match.candidate.symbol} ({match.candidate.name})")
    #         print(f"Surrogate: {match.surrogate.symbol} ({match.surrogate.name})")
    #         print(f"Match Quality: {'Good' if match.score == 1 else 'Decent' if match.score == 2 else 'Poor'}")
    #         print(f"Reason: {match.match_reason}")
    #         print("Differences:")
            
    #         if match.potential_difference is not None:
    #             print(f"  Standard Potential: {match.potential_difference:.3f}")
    #         if match.electronegativity_difference is not None:
    #             print(f"  Electronegativity: {match.electronegativity_difference:.3f}")
    #         if match.electron_affinity_difference is not None:
    #             print(f"  Electron Affinity: {match.electron_affinity_difference:.3f}")
    #         if match.melting_point_difference is not None:
    #             print(f"  Melting Point: {match.melting_point_difference:.1f}K")
            
    #         # Add keys and standard potentials for comparison
    #         candidate_keys, candidate_potentials = self._get_element_keys(match.candidate)
    #         surrogate_keys, surrogate_potentials = self._get_element_keys(match.surrogate)
            
    #         print("\nCandidate Keys and Standard Potentials:")
    #         for key, potential in zip(candidate_keys, candidate_potentials):
    #             print(f"  {key}: {potential:.3f}")
            
    #         print("\nSurrogate Keys and Standard Potentials:")
    #         for key, potential in zip(surrogate_keys, surrogate_potentials):
    #             print(f"  {key}: {potential:.3f}")

# Import necessary classes

# Initialize the periodic table and mapper
periodic_table = PeriodicTable.from_csv_file("PubChemElements_all.csv")  # or from_excel_file()
mapper = SurrogateMapper(periodic_table)

# Generate all mappings
mappings = mapper.generate_surrogate_mapping()

# Print detailed report
mapper.print_mapping_report(mappings)
def update_csv_with_mappings(original_csv_path: str, mappings: Dict[str, SurrogateMatch], periodic_table: PeriodicTable, output_csv_path: str = None) -> None:
    """
    Update CSV file with surrogate mappings and match quality.
    
    Args:
        original_csv_path: Path to the original CSV file
        mappings: Dictionary of surrogate mappings
        periodic_table: PeriodicTable instance to check for surrogate elements
        output_csv_path: Path for the output CSV file. If None, will append '_updated' to original filename
    """
    # Read the original CSV file
    df = pd.read_csv(original_csv_path)
    
    # If no output path specified, create one
    if output_csv_path is None:
        path_obj = Path(original_csv_path)
        output_csv_path = str(path_obj.parent / f"{path_obj.stem}_updated{path_obj.suffix}")
    
    # Create new columns if they don't exist
    if 'Surrogate' not in df.columns:
        df['Surrogate'] = None
    if 'Match_Quality' not in df.columns:
        df['Match_Quality'] = None
    
    # Get list of surrogate elements
    surrogate_elements = [elem for elem in periodic_table.elements.values() 
                           if elem.surrogate and elem.surrogate.lower() == elem.symbol.lower()]
    surrogate_symbols = [elem.symbol for elem in surrogate_elements]
    
    # Update the dataframe with mappings
    for symbol, match in mappings.items():
        # Find the row index for this element
        idx = df[df['Symbol'] == symbol].index
        if len(idx) > 0:
            # Update Surrogate
            df.loc[idx, 'Surrogate'] = match.surrogate.symbol
            
            # Update Match Quality
            quality_map = {1: "Good", 2: "Decent", 3: "Poor"}
            df.loc[idx, 'Match_Quality'] = quality_map[match.score]
    
    # Handle surrogate elements
    for symbol in surrogate_symbols:
        idx = df[df['Symbol'] == symbol].index
        if len(idx) > 0:
            # Keep the original symbol in Surrogate column
            df.loc[idx, 'Match_Quality'] = 'self'
    
    # Save the updated dataframe
    df.to_csv(output_csv_path, index=False)
    print(f"Updated CSV saved to: {output_csv_path}")

# Example usage:
# After generating your mappings, add this code:
update_csv_with_mappings(
    original_csv_path="PubChemElements_all.csv",
    mappings=mappings,
    periodic_table=periodic_table,  # Pass the periodic_table instance
    output_csv_path="PubChemElements_with_surrogates.csv"  # Optional, will create automatically if not specified
)