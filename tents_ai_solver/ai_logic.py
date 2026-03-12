from game_state import *
import copy


class AILogic:

    def __init__(self, game_state):
        self.G = game_state
        self.score = 0
        self.memo = set()
        self.ai_busy = False
        # Each entry: (row, col, description_string)
        self.solution_moves = []
        self.last_step = "Waiting to start..."
        self.last_cell = None          # (r, c) of most recently placed tent

    # ================= RESET =================
    def reset(self):
        self.memo = set()
        self.ai_busy = False
        self.solution_moves = []
        self.score = 0
        self.last_step = "Waiting to start..."
        self.last_cell = None

    # ================= TREE → TENT CANDIDATE GRAPH =================
    def build_tree_candidate_graph(self):
        graph = {}
        for r in range(self.G.size):
            for c in range(self.G.size):
                if self.G.board[r][c] == TREE and (r, c) not in self.G.tree_used:
                    candidates = [
                        (r + dr, c + dc)
                        for dr, dc in DIRS
                        if self.G.valid_tent(r + dr, c + dc)
                    ]
                    if candidates:
                        graph[(r, c)] = candidates
        return graph

    # ================= MCV HEURISTIC =================
    def choose_tree(self, graph):
        return min(graph, key=lambda t: len(graph[t]), default=None)

    # ================= LCV HEURISTIC =================
    def _lcv_score(self, pos, graph):
        r, c = pos
        eliminated = 0
        for candidates in graph.values():
            for cr, cc in candidates:
                if abs(cr - r) <= 1 and abs(cc - c) <= 1:
                    eliminated += 1
        return eliminated

    # ================= STATE HASH (DP memoization) =================
    def state_key(self):
        tents = tuple(sorted(
            (r, c)
            for r in range(self.G.size)
            for c in range(self.G.size)
            if self.G.board[r][c] == TENT
        ))
        used = tuple(sorted(self.G.tree_used))
        return (tents, used)

    # ================= FORCED MOVES =================
    def forced_moves(self, graph):
        for tree, candidates in graph.items():
            if len(candidates) == 1:
                return tree, candidates[0]
        return None, None

    # ================= FORWARD CHECKING =================
    def forward_check(self):
        for r in range(self.G.size):
            for c in range(self.G.size):
                if self.G.board[r][c] == TREE and (r, c) not in self.G.tree_used:
                    if not any(self.G.valid_tent(r + dr, c + dc) for dr, dc in DIRS):
                        return False
        return True

    # ================= BACKTRACK SOLVER =================
    def solve_recursive(self, moves, depth=0):
        """
        Backtracking solver with DP + MCV + LCV + forward check + constraint propagation.
        Each move appended as (row, col, description).
        """
        key = self.state_key()
        if key in self.memo:
            return False

        if self.G.is_game_over():
            return True

        graph = self.build_tree_candidate_graph()
        if not graph:
            self.memo.add(key)
            return False

        # --- Constraint Propagation: chain all forced moves first ---
        snapshot_before_prop = copy.deepcopy(self.G)
        forced_log = []
        prop_ok = True

        while True:
            g = self.build_tree_candidate_graph()
            if not g:
                break
            forced_tree, forced_pos = self.forced_moves(g)
            if forced_pos is None:
                break
            r, c = forced_pos
            tr, tc = forced_tree
            if self.G.place_tent(r, c):
                desc = (f"⚡ Forced move — Tree ({tr},{tc}) has only 1 option "
                        f"→ Tent at ({r},{c})")
                forced_log.append((r, c, desc))
            else:
                prop_ok = False
                break

        if not prop_ok:
            self.G = snapshot_before_prop
            self.memo.add(key)
            return False

        moves.extend(forced_log)

        if self.G.is_game_over():
            return True

        # --- Branch: MCV picks tree, LCV orders candidates ---
        graph = self.build_tree_candidate_graph()
        if not graph:
            self.G = snapshot_before_prop
            if forced_log:
                del moves[-len(forced_log):]
            self.memo.add(key)
            return False

        tree = self.choose_tree(graph)
        tr, tc = tree
        all_opts = len(graph[tree])
        candidates = sorted(graph[tree], key=lambda p: self._lcv_score(p, graph))

        for idx, (r, c) in enumerate(candidates):
            saved = copy.deepcopy(self.G)
            if self.G.place_tent(r, c):
                if self.forward_check():
                    lcv = self._lcv_score((r, c), graph)
                    desc = (f"🎯 MCV — Tree ({tr},{tc}) had {all_opts} options. "
                            f"LCV chose ({r},{c}) [eliminates {lcv}]. "
                            f"Depth {depth}, try {idx+1}/{all_opts}.")
                    moves.append((r, c, desc))
                    if self.solve_recursive(moves, depth + 1):
                        return True
                    moves.pop()
                else:
                    bt_desc = (f"✂️  Forward-check pruned ({r},{c}) — "
                               f"a tree would lose all options.")
                    moves.append((-1, -1, bt_desc))   # sentinel: log only, no placement
            self.G = saved

        # All branches failed — undo propagation, memoize
        self.G = snapshot_before_prop
        if forced_log:
            del moves[-len(forced_log):]
        self.memo.add(key)
        return False

    # ================= COMPUTE SOLUTION =================
    def compute_solution(self):
        """
        Run the full solver once on a snapshot and store the move sequence.
        Returns True if a solution was found.
        """
        snapshot = copy.deepcopy(self.G)
        self.memo = set()
        moves = []

        found = self.solve_recursive(moves)

        # Always restore board — ai_move will replay step by step
        self.G.__dict__.update(snapshot.__dict__)

        if found:
            self.solution_moves = moves
            total = sum(1 for r, c, _ in moves if r >= 0)
            # Prepend a summary header
            self.solution_moves.insert(0, (-2, -2,
                f"🔍 Solver found solution: {total} tent placements planned."))
        return found

    # ================= AI MOVE (called each timer tick) =================
    def ai_move(self):
        """
        Pops one entry from solution_moves and executes it.
        Log-only entries (r == -1) advance the log without placing.
        Returns (placed: bool, description: str).
        """
        if self.ai_busy:
            return False, ""

        self.ai_busy = True

        # First call — run solver
        if not self.solution_moves:
            self.last_step = "🧠 Thinking... running backtracking solver."
            found = self.compute_solution()
            if not found:
                # Fallback greedy
                graph = self.build_tree_candidate_graph()
                if graph:
                    tree = self.choose_tree(graph)
                    if tree:
                        best = max(graph[tree], key=lambda p: self.G.score_for_placement(*p))
                        r, c = best
                        s = self.G.score_for_placement(r, c)
                        if self.G.place_tent(r, c):
                            self.score += s
                            self.last_cell = (r, c)
                            self.last_step = f"⚠️  Greedy fallback → Tent at ({r},{c}), score +{s}"
                            self.ai_busy = False
                            return True, self.last_step
                self.ai_busy = False
                return False, "❌ No valid move found."

        if not self.solution_moves:
            self.ai_busy = False
            return False, "✅ All moves replayed."

        r, c, desc = self.solution_moves.pop(0)
        self.last_step = desc

        # Header/log-only sentinel
        if r == -2:
            self.ai_busy = False
            return False, desc     # show in log, don't tick board

        # Prune/forward-check log sentinel
        if r == -1:
            self.ai_busy = False
            return False, desc

        # Real placement
        s = self.G.score_for_placement(r, c)
        if self.G.place_tent(r, c):
            self.score += s
            self.last_cell = (r, c)
            self.ai_busy = False
            return True, desc

        # Move invalidated (shouldn't happen with deepcopy replay)
        self.ai_busy = False
        return False, f"⚠️ Move ({r},{c}) became invalid — skipping."
