from collections import namedtuple

from acf_sequences.cooling.doppler import DopplerCool

sequences = [ DopplerCool ]

class Hi:

    def __init__(self):
        self.a = 5

hi = Hi()

"""sequences = {
    "cooling": {
        "doppler": DopplerCool()
    }
}"""

"""Sequences = namedtuple(
    "Sequences",
    "cool notcool")

sequences = Sequences(1, 2)
"""

"""# Create 1 instance of each sequence
cool_doppler = DopplerCool()

# Make a list of all sequences for initialization
sequences_all = [ cool_doppler ]

# Create a structure to hold all the sequences for organization
sequences = SimpleNamespace()
sequences.all = sequences_all

# Cooling sequences
sequences.cooling = SimpleNamespace()
sequences.cooling.doppler = cool_doppler

sequences.hmm = SimpleNamespace()
sequences.hmm.a = "hi"
"""
