import random

EMPTY = 0
TREE = 1
TENT = 2

DIRS = [(0,1),(1,0),(-1,0),(0,-1)]
ALL_DIRS = [(dr,dc) for dr in [-1,0,1] for dc in [-1,0,1]]

class GameState:
    def __init__(self, size=8):
        self.size = size
        self.board = [[EMPTY]*size for _ in range(size)]

        self.player_score = 0
        self.ai_score = 0

        self.row_targets = [0]*size
        self.col_targets = [0]*size

        self.tree_used = set()
        self.generate_solvable_trees_and_targets()

    def in_bounds(self, r, c):
        return 0 <= r < self.size and 0 <= c < self.size

    # ===============================
    # TREE ↔ TENT LINK
    # ===============================
    def adjacent_tree(self, r, c):
        for dr, dc in DIRS:
            nr, nc = r+dr, c+dc
            if self.in_bounds(nr, nc) and self.board[nr][nc] == TREE:
                return (nr, nc)
        return None

    # ===============================
    # COUNTS
    # ===============================
    def current_row_count(self, r):
        return sum(1 for c in range(self.size) if self.board[r][c] == TENT)

    def current_col_count(self, c):
        return sum(1 for r in range(self.size) if self.board[r][c] == TENT)

    def row_need(self, r):
        return self.row_targets[r] - self.current_row_count(r)

    def col_need(self, c):
        return self.col_targets[c] - self.current_col_count(c)

    def free_row_cells(self, r):
        return sum(1 for c in range(self.size) if self.valid_tent(r, c))

    def free_col_cells(self, c):
        return sum(1 for r in range(self.size) if self.valid_tent(r, c))

    # ===============================
    # RULE VALIDATION
    # ===============================
    def valid_tent(self, r, c):
        if not self.in_bounds(r, c): return False
        if self.board[r][c] != EMPTY: return False

        for dr, dc in ALL_DIRS:
            nr, nc = r+dr, c+dc
            if self.in_bounds(nr, nc) and self.board[nr][nc] == TENT:
                return False

        tree = self.adjacent_tree(r, c)
        if not tree: return False
        if tree in self.tree_used: return False

        if self.current_row_count(r) + 1 > self.row_targets[r]: return False
        if self.current_col_count(c) + 1 > self.col_targets[c]: return False

        return True

    # ===============================
    # PLACE TENT
    # ===============================
    def place_tent(self, r, c):
        if self.valid_tent(r, c):
            self.board[r][c] = TENT
            tree = self.adjacent_tree(r, c)
            if tree:
                self.tree_used.add(tree)
            return True
        return False

    # ===============================
    # SOLVABLE BOARD GENERATION
    # ===============================
    def generate_solvable_trees_and_targets(self):
        while True:
            self.board = [[EMPTY]*self.size for _ in range(self.size)]
            self.row_targets = [0]*self.size
            self.col_targets = [0]*self.size
            self.tree_used.clear()

            trees = []
            while len(trees) < 10:
                r, c = random.randint(0,7), random.randint(0,7)
                if self.board[r][c] == EMPTY:
                    self.board[r][c] = TREE
                    trees.append((r,c))

            ok = True
            for r, c in trees:
                spots = []
                for dr, dc in DIRS:
                    nr, nc = r+dr, c+dc
                    if self.in_bounds(nr, nc) and self.board[nr][nc] == EMPTY:
                        spots.append((nr, nc))
                if not spots:
                    ok = False
                    break
                tr, tc = random.choice(spots)
                self.row_targets[tr] += 1
                self.col_targets[tc] += 1

            if ok:
                return
