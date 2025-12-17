from game_state import *

class PlayerLogic:
    def __init__(self, game_state):
        self.G = game_state

    def player_move(self, r, c):
        return self.G.place_tent(r, c)
    