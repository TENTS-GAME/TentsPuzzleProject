import random

EMPTY = 0
TREE  = 1
TENT  = 2

DIRS     = [(0, 1), (1, 0), (-1, 0), (0, -1)]
ALL_DIRS = [(dr, dc) for dr in [-1, 0, 1] for dc in [-1, 0, 1] if not (dr == 0 and dc == 0)]


class GameState:

    def __init__(self, size=8):
        self.size = size
        self.board = [[EMPTY] * size for _ in range(size)]
        self.player_score = 0
        self.ai_score = 0
        self.row_targets = [0] * size
        self.col_targets = [0] * size
        self.tree_used = set()
        self.tree_tent_map = {}
        self.generate_solvable_trees_and_targets()

    def in_bounds(self, r, c):
        return 0 <= r < self.size and 0 <= c < self.size

    def adjacent_tree(self, r, c):
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if self.in_bounds(nr, nc) and self.board[nr][nc] == TREE and (nr, nc) not in self.tree_used:
                return (nr, nc)
        return None

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

    def valid_tent(self, r, c):
        if not self.in_bounds(r, c):
            return False
        if self.board[r][c] != EMPTY:
            return False
        for dr, dc in ALL_DIRS:
            nr, nc = r + dr, c + dc
            if self.in_bounds(nr, nc) and self.board[nr][nc] == TENT:
                return False
        if not self.adjacent_tree(r, c):
            return False
        if self.current_row_count(r) + 1 > self.row_targets[r]:
            return False
        if self.current_col_count(c) + 1 > self.col_targets[c]:
            return False
        return True

    def any_valid_tent_exists(self):
        return any(self.valid_tent(r, c) for r in range(self.size) for c in range(self.size))

    def place_tent(self, r, c):
        if self.valid_tent(r, c):
            self.board[r][c] = TENT
            tree = self.adjacent_tree(r, c)
            if tree:
                self.tree_used.add(tree)
            return True
        return False

    def score_for_placement(self, r, c):
        """Score a potential placement WITHOUT modifying state."""
        score = 1
        rn = self.row_need(r)
        cn = self.col_need(c)
        if rn == 1:   score += 3
        elif rn > 0:  score += 2
        if cn == 1:   score += 3
        elif cn > 0:  score += 2
        return score

    def is_game_over(self):
        all_trees = [(r, c) for r in range(self.size) for c in range(self.size) if self.board[r][c] == TREE]
        if len(self.tree_used) >= len(all_trees):
            return True
        empty = sum(1 for r in range(self.size) for c in range(self.size) if self.board[r][c] == EMPTY)
        if empty < 3:
            return True
        if not self.any_valid_tent_exists():
            return True
        return False

    # ================= PUZZLE GENERATION =================

    def generate_solvable_trees_and_targets(self):
        for _ in range(2000):
            self.board = [[EMPTY] * self.size for _ in range(self.size)]
            self.row_targets = [0] * self.size
            self.col_targets = [0] * self.size
            self.tree_used.clear()
            self.tree_tent_map.clear()

            trees = []
            attempts = 0
            while len(trees) < 10 and attempts < 500:
                attempts += 1
                r = random.randint(0, self.size - 1)
                c = random.randint(0, self.size - 1)
                if self.board[r][c] == EMPTY:
                    self.board[r][c] = TREE
                    trees.append((r, c))

            if len(trees) < 10:
                continue

            assigned_tents = set()
            assignment = {}
            if not self._assign_tents(trees, 0, assigned_tents, assignment):
                continue

            self.row_targets = [0] * self.size
            self.col_targets = [0] * self.size
            for tree, (tr, tc) in assignment.items():
                self.row_targets[tr] += 1
                self.col_targets[tc] += 1

            self.tree_tent_map = assignment
            return

        self._simple_generate()

    def _assign_tents(self, trees, idx, assigned_tents, assignment):
        if idx == len(trees):
            return True
        tree = trees[idx]
        r, c = tree
        candidates = []
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if self.in_bounds(nr, nc) and self.board[nr][nc] == EMPTY:
                candidates.append((nr, nc))
        random.shuffle(candidates)
        for nr, nc in candidates:
            conflict = any(abs(nr - tr) <= 1 and abs(nc - tc) <= 1 for tr, tc in assigned_tents)
            if conflict:
                continue
            assigned_tents.add((nr, nc))
            assignment[tree] = (nr, nc)
            if self._assign_tents(trees, idx + 1, assigned_tents, assignment):
                return True
            assigned_tents.remove((nr, nc))
            del assignment[tree]
        return False

    def _simple_generate(self):
        """Fallback generator — now correctly checks tent-to-tent adjacency."""  # FIX
        while True:
            self.board = [[EMPTY] * self.size for _ in range(self.size)]
            self.row_targets = [0] * self.size
            self.col_targets = [0] * self.size
            self.tree_used.clear()
            self.tree_tent_map.clear()

            trees = []
            while len(trees) < 10:
                r = random.randint(0, self.size - 1)   # FIX: was hardcoded 7
                c = random.randint(0, self.size - 1)
                if self.board[r][c] == EMPTY:
                    self.board[r][c] = TREE
                    trees.append((r, c))

            assigned_tents = set()
            assignment = {}
            ok = True

            for r, c in trees:
                spots = []
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if not self.in_bounds(nr, nc) or self.board[nr][nc] != EMPTY:
                        continue
                    # FIX: skip spots adjacent to already-assigned tents
                    if not any(abs(nr - tr) <= 1 and abs(nc - tc) <= 1 for tr, tc in assigned_tents):
                        spots.append((nr, nc))

                if not spots:
                    ok = False
                    break

                tr, tc = random.choice(spots)
                assigned_tents.add((tr, tc))
                assignment[(r, c)] = (tr, tc)
                self.row_targets[tr] += 1
                self.col_targets[tc] += 1

            if ok:
                self.tree_tent_map = assignment
                return
