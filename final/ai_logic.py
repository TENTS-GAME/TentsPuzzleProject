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
        res = []
        i = j = 0
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
            cur = A[i]
            j = i-1
            while j >= 0 and key(A[j]) > key(cur):
                A[j+1] = A[j]
                j -= 1
            A[j+1] = cur
        return A

    # ================= COUNTING SORT =================
    def evaluate_lines_priority(self):
        lines = []
        max_need = 0
        for i in range(self.G.size):
            rn, cn = self.G.row_need(i), self.G.col_need(i)
            lines += [(rn, self.G.free_row_cells(i), i, 'R'),
                      (cn, self.G.free_col_cells(i), i, 'C')]
            max_need = max(max_need, rn, cn)

        buckets = [[] for _ in range(max_need+1)]
        for l in lines:
            buckets[l[0]].append(l)

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

    # ================= AI MOVE =================
    def ai_move(self):
        if self.ai_busy: return False
        self.ai_busy = True

        graph = self.build_bipartite_graph()
        trees = list(graph.keys())
        if not trees:
            self.ai_busy = False
            return False

        trees = self.merge_sort(
            trees,
            key=lambda t:(len(graph[t]),
                          -(self.G.row_need(t[0])+self.G.col_need(t[1])),
                          t[0]*self.G.size+t[1])
        )

        for t in trees:
            candidates = self.insertion_sort(
                graph[t],
                key=lambda c:(-(self.G.row_need(c[0])+self.G.col_need(c[1])),
                              c[0]*self.G.size+c[1])
            )
            for r, c in candidates:
                if self.G.place_tent(r, c):
                    self.evaluate_lines_priority()
                    self.ai_busy = False
                    return True

        self.ai_busy = False
        return False