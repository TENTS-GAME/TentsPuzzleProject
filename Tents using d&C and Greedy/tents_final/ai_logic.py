from game_state import *

class AILogic:
    def __init__(self, game_state):
        self.G = game_state
        self.score = 0
        self.line_priority = []
        self.ai_busy = False

    # ================= MERGE SORT =================
    def merge_sort(self, arr, key):
        if len(arr) <= 1: return arr
        mid = len(arr)//2
        L = self.merge_sort(arr[:mid], key)
        R = self.merge_sort(arr[mid:], key)
        return self._merge(L, R, key)

    def _merge(self, L, R, key):
        res = []; i = j = 0
        while i < len(L) and j < len(R):
            if key(L[i]) <= key(R[j]):
                res.append(L[i]); i += 1
            else:
                res.append(R[j]); j += 1
        return res + L[i:] + R[j:]

    # ================= INSERTION SORT =================
    def insertion_sort(self, arr, key):
        A = list(arr)
        for i in range(1, len(A)):
            cur = A[i]; j = i-1
            while j >= 0 and key(A[j]) > key(cur):
                A[j+1] = A[j]; j -= 1
            A[j+1] = cur
        return A

    # ================= LINE PRIORITY =================
    def evaluate_lines_priority(self):
        lines = []
        max_need = 0
        for i in range(self.G.size):
            rn, cn = self.G.row_need(i), self.G.col_need(i)
            lines += [(rn, self.G.free_row_cells(i), i, 'R'),
                      (cn, self.G.free_col_cells(i), i, 'C')]
            max_need = max(max_need, rn, cn)
        if max_need < 0: max_need = 0
        buckets = [[] for _ in range(max_need+2)]
        for l in lines:
            idx = max(0, min(l[0], max_need))
            buckets[idx].append(l)
        self.line_priority = []
        for need in range(max_need, -1, -1):
            buckets[need].sort(key=lambda x:(x[1],x[2]))
            self.line_priority.extend(buckets[need])

    # ================= BIPARTITE GRAPH =================
    def build_bipartite_graph(self):
        graph = {}
        for r in range(self.G.size):
            for c in range(self.G.size):
                if self.G.board[r][c] == TREE and (r,c) not in self.G.tree_used:
                    graph[(r,c)] = []
                    for dr, dc in DIRS:
                        nr, nc = r+dr, c+dc
                        if self.G.valid_tent(nr, nc):
                            graph[(r,c)].append((nr,nc))
        return graph

    # ================= FORCED MOVES (MANDATORY PLACEMENT) =================
    def find_forced_move(self, graph):
        """
        Mandatory Placement Rule:
        1. If a tree has exactly 1 valid tent position -> forced.
        2. If a row needs exactly N tents and has exactly N valid cells -> all forced.
        3. If a col needs exactly N tents and has exactly N valid cells -> all forced.
        Returns (r, c) if a forced move is found, else None.
        """
        # Rule 1: tree with only 1 valid position
        for tree, candidates in graph.items():
            if len(candidates) == 1:
                return candidates[0]

        # Rule 2: row/col forced
        for r in range(self.G.size):
            need = self.G.row_need(r)
            if need <= 0: continue
            row_candidates = [c for c in range(self.G.size) if self.G.valid_tent(r, c)]
            if len(row_candidates) == need:
                return (r, row_candidates[0])

        for c in range(self.G.size):
            need = self.G.col_need(c)
            if need <= 0: continue
            col_candidates = [r for r in range(self.G.size) if self.G.valid_tent(r, c)]
            if len(col_candidates) == need:
                return (col_candidates[0], c)

        return None

    # ================= LOOKAHEAD SCORING =================
    def lookahead_score(self, r, c):
        """
        Score a candidate cell by simulating placement and evaluating
        how many valid moves remain afterwards (higher = better).
        Penalizes moves that block future placements.
        """
        import copy
        # Quick scoring without deep copy for performance
        score = self.G.score_for_placement(r, c)

        # Count how many future valid placements exist after this move
        # Simulate by checking neighbors won't be blocked
        future_blocked = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = r+dr, c+dc
                if not self.G.in_bounds(nr, nc): continue
                if self.G.board[nr][nc] == EMPTY:
                    # This cell would be blocked by our tent
                    if self.G.adjacent_tree(nr, nc):
                        future_blocked += 1

        score -= future_blocked * 0.3
        return score

    # ================= AI MOVE =================
    def ai_move(self):
        if self.ai_busy: return False
        self.ai_busy = True

        graph = self.build_bipartite_graph()
        if not graph:
            self.ai_busy = False
            return False

        # Remove trees with no candidates
        graph = {t: cands for t, cands in graph.items() if cands}
        if not graph:
            self.ai_busy = False
            return False

        # PHASE 1: Forced moves (mandatory placement)
        forced = self.find_forced_move(graph)
        if forced:
            r, c = forced
            if self.G.place_tent(r, c):
                pts = self.G.score_for_placement(r, c) if hasattr(self.G, 'score_for_placement') else 1
                # score already counted post-placement, approximate
                self.score += 7  # forced move bonus
                self.evaluate_lines_priority()
                self.ai_busy = False
                return True

        # PHASE 2: Prioritize most-constrained trees first (merge sort)
        trees = list(graph.keys())
        trees = self.merge_sort(
            trees,
            key=lambda t: (
                len(graph[t]),                                      # fewest options first
                -(self.G.row_need(t[0]) + self.G.col_need(t[1])), # high need first
                t[0]*self.G.size + t[1]
            )
        )

        best_move = None
        best_score = -999

        for t in trees:
            # Sort candidates by lookahead score
            candidates = self.insertion_sort(
                graph[t],
                key=lambda c_pos: (
                    -self.lookahead_score(c_pos[0], c_pos[1]),
                    c_pos[0]*self.G.size + c_pos[1]
                )
            )
            for r, c in candidates:
                s = self.lookahead_score(r, c)
                if s > best_score:
                    best_score = s
                    best_move = (r, c)
                    # Take first best from most-constrained tree
                    break

        if best_move:
            r, c = best_move
            pts = self.G.score_for_placement(r, c)
            if self.G.place_tent(r, c):
                self.score += pts
                self.evaluate_lines_priority()
                self.ai_busy = False
                return True

        # PHASE 3: Fallback - just take any valid move
        for t, cands in graph.items():
            for r, c in cands:
                if self.G.place_tent(r, c):
                    self.score += 1
                    self.ai_busy = False
                    return True

        self.ai_busy = False
        return False
