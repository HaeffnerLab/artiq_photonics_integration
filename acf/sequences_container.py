# This is a class to hold all the user defined sequences and pass them to the experiment.

class SequencesContainer:

    def __init__(self):
        self.all_sequences = []

    def add_sequence(self, name, seq):
        """Add a sequence.

        Args:
            name (str): The name of the attribute that the sequence will be set to.
            seq (Sequence): The sequence.
        """
        self.all_sequences.append(seq)
        setattr(self, name, seq)
