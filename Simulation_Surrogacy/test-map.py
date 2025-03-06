"""
An example structure of classes to implement chemical element reduction mapper.

Problem: depletion calculations return the entire periodic table, but modeling tools and
chemical experiments can only use a subset of elements. This requires appropriate surrogacy
mapping from dict{ 'ele_all' : float_value} to dict{ 'ele_surrogate' : sum_float_value}, where
ele_all are possibly all periodic table elements, and
ele_surrogate are the ones available for surrogacy. The values are summed over all elements being surrogate.

The class structure here shows hot to implement such mapping. The base class ElementMapper implements
the core functionality. Derived classes implement problem-specific mapping. Once the mapping is implemented,
get_surrogates(input_elements: dict) returns the mapped dict, and get_missing_elements the elements not mapped.

Ondrej Chvala <ochvala@utexas.edu>
"""
import json


class ElementMapper:
    """ Reducing element data for surrogacy, ochvala@utexas.edu
    Methods with dictionaries {'element': value}
    """
    def __init__(self):
        self.PERIOD_TABLE_ELEMENTS: list = [
    'neutron', 'h',                                                                                       'he',
    'li', 'be',                                                              'b',  'c',  'n',  'o',  'f', 'ne',
    'na', 'mg',                                                             'al', 'si',  'p',  's', 'cl', 'ar',
    'k',  'ca', 'sc', 'ti',  'v', 'cr', 'mn', 'fe', 'co', 'ni', 'cu', 'zn', 'ga', 'ge', 'as', 'se', 'br', 'kr',
    'rb', 'sr',  'y', 'zr', 'nb', 'mo', 'tc', 'ru', 'rh', 'pd', 'ag', 'cd', 'in', 'sn', 'sb', 'te',  'i', 'xe',
    'cs', 'ba',
          'la', 'ce', 'pr', 'nd', 'pm', 'sm', 'eu', 'gd', 'tb', 'dy', 'ho', 'er', 'tm', 'yb', 'lu',
                      'hf', 'ta',  'w', 're', 'os', 'ir', 'pt', 'au', 'hg', 'tl', 'pb', 'bi', 'po', 'at', 'rn',
    'fr', 'ra',
          'ac', 'th', 'pa',  'u', 'np', 'pu', 'am', 'cm', 'bk', 'cf', 'es', 'fm', 'md', 'no', 'lr',
          'rf', 'db', 'sg', 'bh', 'hs', 'mt', 'ds', 'rg', 'cn', 'nh', 'fl', 'mc', 'lv', 'ts', 'og'
        ]
        self.element_surrogacy_map: (None, dict) = None
        self.missing_elements: (None, list) = None

    def get_missing_elements(self) -> list:
        """ Virtual method for missing elements, also check mapping does not overlap """
        known_mapping_elements: list = []
        for te, me_list in self.element_surrogacy_map.items():
            for me in me_list:
                if me in known_mapping_elements:
                    assert ValueError(f'Mapping element {me} in target element {te} is already mapped!')
                    known_mapping_elements.append(me)
        self.missing_elements = list(set(self.PERIOD_TABLE_ELEMENTS).difference(known_mapping_elements))
        return self.missing_elements

    def get_missing_values(self, input_all_element_dict: dict) -> dict:
        """ Returns value for missing elements """
        return {e: v for e, v in input_all_element_dict.items() if e not in self.element_surrogacy_map.keys()}

    def get_surrogates(self, input_all_element_dict: dict) -> dict:
        """" Sums over the surrogacy mapping """
        surrogate_elements: dict = {}
        for target_ele, me_list in self.element_surrogacy_map.items():
            surrogate_elements[target_ele] = 0.0
            for e, v in input_all_element_dict.items():
                if e in me_list:
                    surrogate_elements[target_ele] += v
        return surrogate_elements


class MSTDB_31_mapper(ElementMapper):
    """ Maps periodic table into MSTDB version 3.1 elements"""
    def __init__(self):
        super().__init__()
        self.element_map: dict = {
            #  TODO CURRENTLY INCOMPLETE AND FAKE
            'li' : ['li'],
            'f'  : ['f'],
            'be' : ['be', 'mg', 'ca']
        }


class PhysicalChemistryMapper(ElementMapper):
    """ Maps periodic table into chemically available elements"""
    def __init__(self):
        super().__init__()
        self.element_map: dict = {
            #  TODO CURRENTLY INCOMPLETE AND FAKE
            'li' : ['li'],
            'f'  : ['f'],
            'be' : ['be', 'mg', 'ca']
        }
