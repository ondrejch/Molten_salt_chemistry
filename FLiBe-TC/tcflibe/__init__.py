import os

ELEMENTS: list = ['neutron', 'h', 'he',
                  'li', 'be', 'b', 'c', 'n', 'o', 'f', 'ne',
                  'na', 'mg', 'al', 'si', 'p', 's', 'cl', 'ar',
                  'k', 'ca', 'sc', 'ti', 'v', 'cr', 'mn', 'fe', 'co', 'ni', 'cu', 'zn', 'ga', 'ge', 'as', 'se', 'br',
                  'kr',
                  'rb', 'sr', 'y', 'zr', 'nb', 'mo', 'tc', 'ru', 'rh', 'pd', 'ag', 'cd', 'in', 'sn', 'sb', 'te', 'i',
                  'xe',
                  'cs', 'ba',
                  'la', 'ce', 'pr', 'nd', 'pm', 'sm', 'eu', 'gd', 'tb', 'dy', 'ho', 'er', 'tm', 'yb', 'lu',
                  'hf', 'ta', 'w', 're', 'os', 'ir', 'pt', 'au', 'hg', 'tl', 'pb', 'bi', 'po', 'at', 'rn',
                  'fr', 'ra',
                  'ac', 'th', 'pa', 'u', 'np', 'pu', 'am', 'cm', 'bk', 'cf', 'es', 'fm', 'md', 'no', 'lr',
                  'rf', 'db', 'sg', 'bh', 'hs', 'mt', 'ds', 'rg', 'cn', 'nh', 'fl', 'mc', 'lv', 'ts', 'og']


def FLiBeU(uf4_mol_pct: float, uf3_to_uf4: float) -> dict[str, float]:
    """ FLiBe-U salt defined using UF4 mol% and UF3/UF4 ratio. """
    if uf3_to_uf4 == 0.0:  # If the fluorine potential is exactly zero, TC goes nuts. TODO Investigate for a paper?
        uf3_to_uf4 = 1e-6
    mU: float = uf4_mol_pct
    mLi: float = 2.0 / 3.0 * (100.0 - mU)  # 2 mol of Li : 1 mol of Be
    mBe: float = 2.0 / 3.0 * (100.0 - mU)  # 1 mol of Be
    mF: float = mLi + 2.0 * mBe  # LiF-BeF2
    # mU = mUF3 + mUF4
    mUF3: float = (uf3_to_uf4 * mU) / (1.0 + uf3_to_uf4)
    mUF4: float = mU / (1.0 + uf3_to_uf4)
    mF += 3.0 * mUF3 + 4.0 * mUF4
    elements: dict[str, float] = {'li': mLi, 'be': mBe, 'f': mF, 'u': mU}
    s = sum(elements.values())
    return {e: v / s for e, v in elements.items()}  # normalize to 1


def ss316() -> dict[str, float]:
    """ Elemental composition of stainles steel 316H """
    return {
        'c': 0.0033694978880478618,
        'mn': 0.018416674099286608,
        'p': 0.0007349756065312752,
        's': 0.00047323478874348524,
        'si': 0.018012746632251584,
        'cr': 0.1653991810107577,
        'ni': 0.10343066242995637,
        'mo': 0.0131810315051273,
        'fe': 0.5919994744287896,
        'co': 0.08498252161050811
    }


class Thermochimica:
    """ Python wrapper around the Thermochimica's InputScriptMode"""

    def __init__(self):
        """ Thermochimica installation paths, modify according to your installation! """
        self.datafile_path: str = os.path.expanduser(
            '~/thermochimica/data/MSTDB-TC_V3.1_Fluorides_No_Func.dat')
        self.binary_path: str = os.path.expanduser(
            '~/thermochimica/bin/InputScriptMode')
        self.output_path: str = os.path.expanduser(
            '~/thermochimica/outputs/thermoout.json')
        assert os.path.isfile(self.datafile_path)
        assert os.path.isfile(self.binary_path)
        self.deck_name: str = 'my_tc.ti'  # Thermochimica input file name
        self.thermo_output_name: str = self.deck_name.replace('.ti', '.json')
        self.header: str = ''  # Run header
        self.temps_k: str = '600:1000:10'  # 'from : to : stride'
        self.elements: dict[str, float] = {}  # Molar amounts of elements

    def run_tc(self) -> bool:
        """ Run a Thermochimica deck """
        import subprocess
        tchem_out = subprocess.run([f"{self.binary_path}", self.deck_name], capture_output=True)
        tchem_out = tchem_out.stdout.decode().split("\n")
        if tchem_out.count('Error') == 0 and os.path.exists(self.output_path):
            os.replace(self.output_path, self.thermo_output_name)  # Move output from work directory
            return True
        else:
            return False

    def tc_input(self) -> str:
        """ Makes Thermochimica input file based on fuel salt object """
        output: str = f'''! {self.header}

! Initialize variables:
pressure          = 1
temperature       = {self.temps_k}
'''
        for e, v in self.elements.items():
            z: int = ELEMENTS.index(e)
            output += f'mass({z})           = {v}     !{e}\n'
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
