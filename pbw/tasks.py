"""Task bank.

Each task has:
  - a short natural-language spec,
  - a correct reference implementation,
  - a few *visible* test inputs (what a typical unit-test file would contain),
  - a random input generator used for *hidden* differential testing,
  - one hand-written "seed" bug that passes the visible tests but is wrong.

Ground truth never depends on a model: a candidate is "buggy" iff its output
differs from the reference on at least one hidden input.
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Task:
    name: str
    func: str
    spec: str
    reference: str
    visible: list[list]
    gen: Callable[[random.Random], list]
    seed_bug: str
    edge: list[list] = field(default_factory=list)

    def hidden_inputs(self, n: int = 300, seed: int = 0) -> list[list]:
        rng = random.Random(f"{self.name}:{seed}")
        return list(self.edge) + [self.gen(rng) for _ in range(n)]


def _ints(rng, lo=-20, hi=20, min_len=0, max_len=10):
    return [rng.randint(lo, hi) for _ in range(rng.randint(min_len, max_len))]


TASKS: list[Task] = []


def task(**kw):
    TASKS.append(Task(**kw))


# 1 ---------------------------------------------------------------------------
task(
    name="binary_search",
    func="binary_search",
    spec="Given a list of integers sorted in ascending order (no duplicates) and a target, "
    "return the index of target, or -1 if it is not present.",
    reference='''
def binary_search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
''',
    seed_bug='''
def binary_search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
''',
    visible=[[[1, 3, 5, 7, 9], 5], [[1, 3, 5, 7, 9], 4], [[2, 4, 6, 8], 4], [[], 1]],
    edge=[[[5], 5], [[1, 2], 2]],
    gen=lambda r: (lambda xs: [xs, r.choice(xs + [r.randint(-50, 50)]) if xs else 0])(
        sorted(r.sample(range(-50, 50), r.randint(0, 12)))
    ),
)

# 2 ---------------------------------------------------------------------------
task(
    name="merge_intervals",
    func="merge_intervals",
    spec="Given a list of closed intervals [start, end] (start <= end), merge all overlapping "
    "intervals and return them sorted by start. Intervals that touch (e.g. [1,2] and [2,3]) overlap.",
    reference='''
def merge_intervals(intervals):
    out = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out
''',
    seed_bug='''
def merge_intervals(intervals):
    out = []
    for s, e in sorted(intervals):
        if out and s < out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out
''',
    visible=[[[[1, 3], [2, 6], [8, 10]]], [[[1, 4], [0, 2]]], [[]]],
    edge=[[[[1, 2], [2, 3]]]],
    gen=lambda r: [[(lambda s: [s, s + r.randint(0, 4)])(r.randint(0, 15)) for _ in range(r.randint(0, 6))]],
)

# 3 ---------------------------------------------------------------------------
task(
    name="max_subarray",
    func="max_subarray",
    spec="Return the largest sum of any non-empty contiguous subarray of a non-empty list of integers.",
    reference='''
def max_subarray(nums):
    best = cur = nums[0]
    for x in nums[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best
''',
    seed_bug='''
def max_subarray(nums):
    best = cur = 0
    for x in nums:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best
''',
    visible=[[[-2, 1, -3, 4, -1, 2, 1, -5, 4]], [[1]], [[5, 4, -1, 7, 8]]],
    edge=[[[-3, -1, -2]]],
    gen=lambda r: [_ints(r, min_len=1)],
)

# 4 ---------------------------------------------------------------------------
task(
    name="is_palindrome",
    func="is_palindrome",
    spec="Return True if the string reads the same forwards and backwards after removing all "
    "non-alphanumeric characters and ignoring letter case.",
    reference='''
def is_palindrome(s):
    t = [c.lower() for c in s if c.isalnum()]
    return t == t[::-1]
''',
    seed_bug='''
def is_palindrome(s):
    t = [c for c in s if c.isalnum()]
    return t == t[::-1]
''',
    visible=[["racecar"], ["hello"], ["a b a"], [""]],
    edge=[["A man, a plan, a canal: Panama"]],
    gen=lambda r: [
        (lambda h: h + r.choice(["", r.choice("aBc")]) + h[::-1].swapcase() if r.random() < 0.5 else h)(
            "".join(r.choice("aAbBc ,") for _ in range(r.randint(0, 6)))
        )
    ],
)

# 5 ---------------------------------------------------------------------------
task(
    name="lis_length",
    func="lis_length",
    spec="Return the length of the longest strictly increasing subsequence of a list of integers.",
    reference='''
from bisect import bisect_left

def lis_length(nums):
    tails = []
    for x in nums:
        i = bisect_left(tails, x)
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)
''',
    seed_bug='''
from bisect import bisect_right

def lis_length(nums):
    tails = []
    for x in nums:
        i = bisect_right(tails, x)
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)
''',
    visible=[[[10, 9, 2, 5, 3, 7, 101, 18]], [[0, 1, 0, 3, 2, 3]], [[]]],
    edge=[[[7, 7, 7, 7]]],
    gen=lambda r: [_ints(r, 0, 6, 0, 10)],
)

# 6 ---------------------------------------------------------------------------
task(
    name="coin_change",
    func="coin_change",
    spec="Given coin denominations (positive integers, unlimited supply) and an amount, return the "
    "minimum number of coins that sum to amount, or -1 if impossible.",
    reference='''
def coin_change(coins, amount):
    INF = float("inf")
    dp = [0] + [INF] * amount
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a and dp[a - c] + 1 < dp[a]:
                dp[a] = dp[a - c] + 1
    return dp[amount] if dp[amount] != INF else -1
''',
    seed_bug='''
def coin_change(coins, amount):
    count = 0
    for c in sorted(coins, reverse=True):
        count += amount // c
        amount %= c
    return count if amount == 0 else -1
''',
    visible=[[[1, 2, 5], 11], [[2], 3], [[1], 0]],
    edge=[[[1, 3, 4], 6]],
    gen=lambda r: [r.sample(range(1, 10), r.randint(1, 3)), r.randint(0, 30)],
)

# 7 ---------------------------------------------------------------------------
task(
    name="edit_distance",
    func="edit_distance",
    spec="Return the Levenshtein distance (insertions, deletions, substitutions, each cost 1) between two strings.",
    reference='''
def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]
''',
    seed_bug='''
def edit_distance(a, b):
    if not a or not b:
        return int(a != b)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]
''',
    visible=[["kitten", "sitting"], ["horse", "ros"], ["", ""], ["abc", "abc"]],
    edge=[["ab", "abcd"]],
    gen=lambda r: ["".join(r.choice("ab") for _ in range(r.randint(0, 5))) for _ in range(2)],
)

# 8 ---------------------------------------------------------------------------
task(
    name="num_islands",
    func="num_islands",
    spec="Given a grid of '1' (land) and '0' (water) as a list of strings, count islands. "
    "Cells are connected horizontally or vertically only (not diagonally).",
    reference='''
def num_islands(grid):
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    seen = set()
    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1" and (r, c) not in seen:
                count += 1
                stack = [(r, c)]
                seen.add((r, c))
                while stack:
                    y, x = stack.pop()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < rows and 0 <= nx < cols and grid[ny][nx] == "1" and (ny, nx) not in seen:
                            seen.add((ny, nx))
                            stack.append((ny, nx))
    return count
''',
    seed_bug='''
def num_islands(grid):
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    seen = set()
    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1" and (r, c) not in seen:
                count += 1
                stack = [(r, c)]
                seen.add((r, c))
                while stack:
                    y, x = stack.pop()
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < rows and 0 <= nx < cols and grid[ny][nx] == "1" and (ny, nx) not in seen:
                                seen.add((ny, nx))
                                stack.append((ny, nx))
    return count
''',
    visible=[[["11000", "11000", "00010", "00011"]], [["111", "010", "111"]], [["1"]], [[]]],
    edge=[[["10", "01"]]],
    gen=lambda r: [
        (lambda h, w: ["".join(r.choice("01") for _ in range(w)) for _ in range(h)])(r.randint(1, 5), r.randint(1, 5))
    ],
)

# 9 ---------------------------------------------------------------------------
task(
    name="valid_brackets",
    func="valid_brackets",
    spec="Return True if the string of brackets ()[]{} is balanced and correctly nested.",
    reference='''
def valid_brackets(s):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
        else:
            stack.append(ch)
    return not stack
''',
    seed_bug='''
def valid_brackets(s):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
        else:
            stack.append(ch)
    return True
''',
    visible=[["()[]{}"], ["(]"], ["([)]"], ["{[]}"]],
    edge=[["(("]],
    gen=lambda r: ["".join(r.choice("()[]{}") for _ in range(r.randint(0, 6)))],
)

# 10 --------------------------------------------------------------------------
task(
    name="kth_largest",
    func="kth_largest",
    spec="Return the k-th largest element of a list of integers (1-indexed, counting duplicates "
    "separately, so [3,3,1] with k=2 is 3). Assume 1 <= k <= len(nums).",
    reference='''
def kth_largest(nums, k):
    return sorted(nums, reverse=True)[k - 1]
''',
    seed_bug='''
def kth_largest(nums, k):
    return sorted(set(nums), reverse=True)[min(k, len(set(nums))) - 1]
''',
    visible=[[[3, 2, 1, 5, 6, 4], 2], [[1], 1], [[7, 10, 4, 20, 15], 3]],
    edge=[[[3, 3, 1], 2]],
    gen=lambda r: (lambda xs: [xs, r.randint(1, len(xs))])(_ints(r, 0, 6, 1, 8)),
)

# 11 --------------------------------------------------------------------------
task(
    name="climb_stairs",
    func="climb_stairs",
    spec="You climb a staircase of n steps (n >= 0) taking 1 or 2 steps at a time. Return the number "
    "of distinct ways to reach the top. There is exactly one way to climb 0 steps.",
    reference='''
def climb_stairs(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a
''',
    seed_bug='''
def climb_stairs(n):
    if n <= 1:
        return n
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a
''',
    visible=[[1], [2], [3], [5]],
    edge=[[0]],
    gen=lambda r: [r.randint(0, 30)],
)

# 12 --------------------------------------------------------------------------
task(
    name="top_k_words",
    func="top_k_words",
    spec="Return the k most frequent words, ordered by frequency (highest first); words with the "
    "same frequency are ordered alphabetically. Assume k <= number of distinct words.",
    reference='''
from collections import Counter

def top_k_words(words, k):
    counts = Counter(words)
    return sorted(counts, key=lambda w: (-counts[w], w))[:k]
''',
    seed_bug='''
from collections import Counter

def top_k_words(words, k):
    return [w for w, _ in Counter(words).most_common(k)]
''',
    visible=[[["a", "b", "a", "c", "b", "a"], 2], [["x"], 1], [["the", "day", "the", "sunny", "the", "is", "is"], 2]],
    edge=[[["b", "a"], 2]],
    gen=lambda r: (lambda ws: [ws, r.randint(1, len(set(ws)))])([r.choice("abcde") for _ in range(r.randint(1, 8))]),
)

# 13 --------------------------------------------------------------------------
task(
    name="roman_to_int",
    func="roman_to_int",
    spec="Convert a valid Roman numeral (1 to 3999, standard subtractive notation) to an integer.",
    reference='''
def roman_to_int(s):
    v = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    for i, ch in enumerate(s):
        if i + 1 < len(s) and v[ch] < v[s[i + 1]]:
            total -= v[ch]
        else:
            total += v[ch]
    return total
''',
    seed_bug='''
def roman_to_int(s):
    v = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    for i, ch in enumerate(s):
        if ch == "I" and i + 1 < len(s) and s[i + 1] in "VX":
            total -= 1
        else:
            total += v[ch]
    return total
''',
    visible=[["III"], ["IV"], ["IX"], ["LVIII"], ["MDCLXVI"]],
    edge=[["XL"]],
    gen=lambda r: [_to_roman(r.randint(1, 3999))],
)


def _to_roman(n: int) -> str:
    table = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
             (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = []
    for val, sym in table:
        while n >= val:
            out.append(sym)
            n -= val
    return "".join(out)


# 14 --------------------------------------------------------------------------
task(
    name="flatten",
    func="flatten",
    spec="Flatten an arbitrarily nested list of integers into a flat list, preserving order.",
    reference='''
def flatten(xs):
    out = []
    for x in xs:
        if isinstance(x, list):
            out.extend(flatten(x))
        else:
            out.append(x)
    return out
''',
    seed_bug='''
def flatten(xs):
    out = []
    for x in xs:
        if isinstance(x, list):
            out.extend(x)
        else:
            out.append(x)
    return out
''',
    visible=[[[1, [2, 3], 4]], [[]], [[[1], [2], [3]]]],
    edge=[[[1, [2, [3]]]]],
    gen=lambda r: [_nested(r, 3)],
)


def _nested(r, depth):
    out = []
    for _ in range(r.randint(0, 4)):
        if depth and r.random() < 0.35:
            out.append(_nested(r, depth - 1))
        else:
            out.append(r.randint(0, 9))
    return out


# 15 --------------------------------------------------------------------------
task(
    name="lcm_list",
    func="lcm_list",
    spec="Return the least common multiple of a non-empty list of positive integers.",
    reference='''
from math import gcd

def lcm_list(nums):
    result = 1
    for x in nums:
        result = result * x // gcd(result, x)
    return result
''',
    seed_bug='''
from math import gcd
from functools import reduce

def lcm_list(nums):
    product = 1
    for x in nums:
        product *= x
    return product // reduce(gcd, nums)
''',
    visible=[[[2, 3]], [[4, 6]], [[6, 8]], [[3, 9]]],
    edge=[[[2, 3, 4]]],
    gen=lambda r: [[r.randint(1, 12) for _ in range(r.randint(1, 4))]],
)

# 16 --------------------------------------------------------------------------
task(
    name="rle_encode",
    func="rle_encode",
    spec="Run-length encode a string of lowercase letters: each maximal run becomes the letter followed "
    "by the run length in decimal, e.g. 'aaab' -> 'a3b1'. Empty string -> ''.",
    reference='''
def rle_encode(s):
    out = []
    i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        out.append(f"{s[i]}{j - i}")
        i = j
    return "".join(out)
''',
    seed_bug='''
def rle_encode(s):
    out = []
    i = 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i] and j - i < 9:
            j += 1
        out.append(f"{s[i]}{j - i}")
        i = j
    return "".join(out)
''',
    visible=[["aaab"], ["abc"], [""], ["zzzzzz"]],
    edge=[["a" * 12]],
    gen=lambda r: ["".join(r.choice("ab") * r.randint(1, 13) for _ in range(r.randint(0, 3)))],
)

# 17 --------------------------------------------------------------------------
task(
    name="longest_common_prefix",
    func="longest_common_prefix",
    spec="Return the longest common prefix of a list of strings ('' if the list is empty).",
    reference='''
def longest_common_prefix(strs):
    if not strs:
        return ""
    prefix = strs[0]
    for s in strs[1:]:
        while not s.startswith(prefix):
            prefix = prefix[:-1]
    return prefix
''',
    seed_bug='''
def longest_common_prefix(strs):
    if not strs:
        return ""
    first, last = strs[0], strs[-1]
    i = 0
    while i < min(len(first), len(last)) and first[i] == last[i]:
        i += 1
    return first[:i]
''',
    visible=[[["flower", "flow", "flight"]], [["dog", "racecar", "car"]], [[]], [["same", "same"]]],
    edge=[[["abc", "x", "abd"]]],
    gen=lambda r: [["".join(r.choice("ab") for _ in range(r.randint(0, 4))) for _ in range(r.randint(0, 4))]],
)

# 18 --------------------------------------------------------------------------
task(
    name="median",
    func="median",
    spec="Return the median of a non-empty unsorted list of integers. For even length, return the "
    "mean of the two middle values as a float (e.g. [1,2] -> 1.5).",
    reference='''
def median(nums):
    s = sorted(nums)
    n = len(s)
    if n % 2:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2
''',
    seed_bug='''
def median(nums):
    s = sorted(nums)
    n = len(s)
    if n % 2:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) // 2
''',
    visible=[[[3, 1, 2]], [[4, 1, 3, 2, 5]], [[1, 3]], [[7]]],
    edge=[[[1, 2]]],
    gen=lambda r: [_ints(r, -10, 10, 1, 8)],
)

# 19 --------------------------------------------------------------------------
task(
    name="to_base",
    func="to_base",
    spec="Convert an integer n (may be zero or negative) to a string in the given base (2..16), "
    "using digits 0-9a-f and a leading '-' for negatives. to_base(0, b) == '0'.",
    reference='''
def to_base(n, base):
    digits = "0123456789abcdef"
    if n == 0:
        return "0"
    sign = "-" if n < 0 else ""
    n = abs(n)
    out = []
    while n:
        n, d = divmod(n, base)
        out.append(digits[d])
    return sign + "".join(reversed(out))
''',
    seed_bug='''
def to_base(n, base):
    digits = "0123456789abcdef"
    sign = "-" if n < 0 else ""
    n = abs(n)
    out = []
    while n:
        n, d = divmod(n, base)
        out.append(digits[d])
    return sign + "".join(reversed(out))
''',
    visible=[[10, 2], [255, 16], [-5, 2], [7, 8]],
    edge=[[0, 10]],
    gen=lambda r: [r.choice([0, r.randint(-300, 300), r.randint(-300, 300)]), r.randint(2, 16)],
)

# 20 --------------------------------------------------------------------------
task(
    name="second_largest",
    func="second_largest",
    spec="Return the second largest *distinct* value in a list of integers, or None if there are "
    "fewer than two distinct values.",
    reference='''
def second_largest(nums):
    distinct = sorted(set(nums))
    return distinct[-2] if len(distinct) >= 2 else None
''',
    seed_bug='''
def second_largest(nums):
    if len(nums) < 2:
        return None
    return sorted(nums)[-2]
''',
    visible=[[[1, 5, 3]], [[4]], [[10, 20]], [[-1, -5, -3]]],
    edge=[[[5, 5, 1]]],
    gen=lambda r: [_ints(r, 0, 5, 0, 6)],
)

TASK_BY_NAME = {t.name: t for t in TASKS}
