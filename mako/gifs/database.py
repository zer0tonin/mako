import csv
import random


class GifsDatabase:
    def __init__(self):
        self.gifs_map = {}
        with open("gifs.csv") as gifs_file:
            gifs_reader = csv.reader(gifs_file)
            for row in gifs_reader:
                if self.gifs_map.get(row[0]) is None:
                    self.gifs_map[row[0]] = []
                self.gifs_map[row[0]].append(row[1])

    def get_random(self, category):
        available_gifs = self.gifs_map[category]
        return random.choice(available_gifs) # nosec
