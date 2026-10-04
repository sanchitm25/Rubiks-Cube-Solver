from itertools import product
from math import lcm

class NCGETable:
    def __init__(self, n):
        self.n = n
        self.ID = tuple(range(n))
        self.table = {}
        self.generator_orders = {}

    def compose(self, p, q):
        return tuple(p[q[i]] for i in range(self.n))

    def inverse(self, p):
        inv = [0] * self.n
        for i, j in enumerate(p):
            inv[j] = i
        return tuple(inv)

    def inverse_word(self, word):
        inverted_word = []
        for move in reversed(word):
            if move.endswith("'"):
                inverted_move = move[:-1]
            else:
                inverted_move = move + "'"
            inverted_word.append(inverted_move)
        return inverted_word

    def permutation_order(self, permutation):
        visited = set()
        order = 1
        for start in range(self.n):
            if start in visited:
                continue
            position = start
            cycle_length = 0
            while position not in visited:
                visited.add(position)
                position = permutation[position]
                cycle_length += 1
            order = lcm(order, cycle_length)
        return order

    def simplify_word(self, word):
        stack = []
        for move in word:
            if move.endswith("'"):
                generator = move[:-1]
                count = -1
            else:
                generator = move
                count = 1

            if stack and stack[-1][0] == generator:
                previous_count = stack.pop()[1]
                count += previous_count

            order = self.generator_orders.get(generator)
            if order is not None:
                count %= order
                if count > order // 2:
                    count -= order

            if count != 0:
                stack.append((generator, count))

        simplified_word = []
        for generator, count in stack:
            if count < 0:
                move = generator + "'"
            else:
                move = generator
            simplified_word.extend([move] * abs(count))
        return simplified_word

    def pivot(self, p):
        for i in range(self.n):
            if p[i] != i:
                return i, p[i]
        return None

    def reduce(self, p):
        word = []
        while True:
            piv = self.pivot(p)
            if piv is None:
                break
            i, j = piv

            if (i, j) not in self.table:
                raise ValueError(
                    f"NCGE table cannot reduce this permutation: missing pivot {(i, j)}."
                )

            q, qword = self.table[(i, j)]
            p = self.compose(self.inverse(q), p)
            word = self.inverse_word(qword) + word
        return self.simplify_word(word)

    def feed(self, p, word):
        while True:
            piv = self.pivot(p)
            if piv is None:
                return
            i, j = piv
            if (i, j) not in self.table:
                self.table[(i, j)] = (p, self.simplify_word(word))
                return
            q, qword = self.table[(i, j)]
            p = self.compose(self.inverse(q), p)
            word = self.inverse_word(qword) + word

    def twist(self):
        changed = True
        while changed:
            changed = False
            items = list(self.table.items())
            for (_, (p1, w1)), (_, (p2, w2)) in product(items, repeat=2):
                before = len(self.table)
                self.feed(self.compose(p1, p2), w1 + w2)
                if len(self.table) > before:
                    changed = True

    def build(self, generators):
        for name, permutation in generators.items():
            if name.endswith("'"):
                generator = name[:-1]
            else:
                generator = name
            self.generator_orders[generator] = self.permutation_order(permutation)

        for name, p in generators.items():
            self.feed(p, [name])
        self.twist()
