import random

class UniqueRandomGenerator:
    def __init__(self, start, end):
        self.numbers = list(range(start, end + 1))
        random.shuffle(self.numbers)

    def get_number(self):
        if not self.numbers:
            raise Exception("No more unique numbers available")

        return self.numbers.pop()


