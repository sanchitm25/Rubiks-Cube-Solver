from itertools import product

class NCGETable:
    def __init__(self, n):
        self.n = n
        self.ID = tuple(range(n))
        self.table = {}

    def compose(self, p, q):
        return tuple(p[q[i]] for i in range(self.n))

    def inverse(self, p):
        inv = [0] * self.n
        for i, j in enumerate(p):
            inv[j] = i
        return tuple(inv)

    def pivot(self, p):
        for i in range(self.n):
            if p[i] != i:
                return i, p[i]
        return None

    def feed(self, p, word):
        while True:
            piv = self.pivot(p)
            if piv is None:
                return
            i, j = piv
            if (i, j) not in self.table:
                self.table[(i, j)] = (p, word)
                return
            q, qword = self.table[(i, j)]
            p = self.compose(self.inverse(q), p)
            word = qword[::-1] + word

    def build(self, generators):
        for name, p in generators.items():
            self.feed(p, [name])
        self._twist()

    def _twist(self):
        changed = True
        while changed:
            changed = False
            items = list(self.table.items())
            for (_, (p1, w1)), (_, (p2, w2)) in product(items, repeat=2):
                before = len(self.table)
                self.feed(self.compose(p1, p2), w1 + w2)
                if len(self.table) > before:
                    changed = True

    def reduce(self, p):
        word = []
        while True:
            piv = self.pivot(p)
            if piv is None:
                break
            i, j = piv

            if (i, j) not in self.table:
                raise ValueError(
                    f"NCGE table cannot reduce this permutation: missing pivot {(i, j)}. "
                    f"This usually means this scramble is not solvable using the regular moves."
                )

            q, qword = self.table[(i, j)]
            p = self.compose(self.inverse(q), p)
            word = qword[::-1] + word
        return word