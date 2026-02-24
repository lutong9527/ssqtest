import random
import math
from collections import Counter


class MaxEntropyModel:

    def __init__(self, history):
        self.history = history
        self.freq = self.calculate_frequency()

    def calculate_frequency(self):
        counter = Counter()
        total = 0
        for draw in self.history:
            for num in draw["red"]:
                counter[num] += 1
                total += 1

        freq = {}
        for i in range(1, 34):
            freq[i] = counter[i] / total if total else 1/33

        return freq

    def entropy_score(self, numbers):
        score = 0
        for n in numbers:
            p = self.freq.get(n, 1/33)
            score += -p * math.log(p + 1e-9)
        return score

    def generate(self, trials=2000):

        best = None
        best_score = -1

        for _ in range(trials):
            nums = sorted(random.sample(range(1, 34), 6))

            if not self.structure_ok(nums):
                continue

            score = self.entropy_score(nums)

            if score > best_score:
                best_score = score
                best = nums

        blue = random.randint(1, 16)

        return {
            "red": best,
            "blue": blue,
            "score": best_score
        }

    def structure_ok(self, nums):

        odd = sum(1 for x in nums if x % 2 == 1)
        if odd not in [2, 3, 4]:
            return False

        consecutive = 0
        for i in range(len(nums) - 1):
            if nums[i+1] - nums[i] == 1:
                consecutive += 1
        if consecutive > 2:
            return False

        return True
