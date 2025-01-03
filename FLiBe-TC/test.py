# Import and set up
from tcflibe.flibe_phases import PhaseAnalyzer
import numpy as np

redoxes = np.linspace(-0.05, 0.1, 16).round(14)
temps_k = "600:1000:10"
UF4_mol_pct = 5.0

analyzer = PhaseAnalyzer(UF4_mol_pct=UF4_mol_pct, redoxes=redoxes, temps_k=temps_k)
analyzer.run_redox_cases()
analyzer.analyze_jsons()
analyzer.plot_results()