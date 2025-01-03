from tcflibe.struct_phases import StructPhaseAnalyzer
import numpy as np

redoxes = np.linspace(-0.05, 0.1, 16).round(14)
temps_k = "600:1000:10"
UF4_mol_pct = 5.0

#analyzer = StructPhaseAnalyzer(UF4_mol_pct=UF4_mol_pct, redoxes=redoxes, temps_k=temps_k)
# Optional: Specify salt to steel ratio (defaults to 1:1)
analyzer = StructPhaseAnalyzer(UF4_mol_pct=UF4_mol_pct, redoxes=redoxes, temps_k=temps_k, salt_moles=10.0, steel_moles=1.0)
analyzer.run_redox_cases()
analyzer.analyze_jsons()
analyzer.plot_results()