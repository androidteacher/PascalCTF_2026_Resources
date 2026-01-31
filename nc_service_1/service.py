#!/usr/bin/env python3
import sys, os

ALPHABET = "abcdefghijklmnop"  # 16 letters
K = len(ALPHABET)
L = 5
N = K ** L


def index_to_word(idx: int) -> str:
    if not (0 <= idx < N):
        raise ValueError("index out of range")
    digits = []
    x = idx
    for _ in range(L):
        digits.append(x % K)
        x //= K
    letters = [ALPHABET[d] for d in reversed(digits)]
    return "".join(letters)


def word_to_index(word: str) -> int:
    if len(word) != L:
        raise ValueError("bad length")
    x = 0
    for ch in word:
        d = ALPHABET.find(ch)
        if d < 0:
            raise ValueError("bad letter")
        x = x * K + d
    return x


def wordle_feedback(guess: str, secret: str) -> str:
    if len(guess) != L or len(secret) != L:
        return "ERR"

    res = [None] * L
    secret_counts = {}
    for i in range(L):
        s = secret[i]
        g = guess[i]
        if g == s:
            res[i] = 'G'
        else:
            secret_counts[s] = secret_counts.get(s, 0) + 1
    for i in range(L):
        if res[i] is not None:
            continue
        g = guess[i]
        if secret_counts.get(g, 0) > 0:
            res[i] = 'Y'
            secret_counts[g] -= 1
        else:
            res[i] = '_'
    return ''.join(res)


class MT19937:
    def __init__(self, seed: int):
        self.N = 624
        self.M = 397
        self.MATRIX_A = 0x9908B0DF
        self.UPPER_MASK = 0x80000000
        self.LOWER_MASK = 0x7FFFFFFF
        self.mt = [0] * self.N
        self.index = self.N
        self.mt[0] = seed & 0xFFFFFFFF
        for i in range(1, self.N):
            self.mt[i] = (1812433253 * (self.mt[i - 1] ^ (self.mt[i - 1] >> 30)) + i) & 0xFFFFFFFF

    def twist(self):
        N = self.N; M = self.M
        a = self.MATRIX_A; U = self.UPPER_MASK; L = self.LOWER_MASK
        old = self.mt[:]
        for i in range(N):
            y = (old[i] & U) | (old[(i + 1) % N] & L)
            self.mt[i] = (old[(i + M) % N] ^ (y >> 1) ^ (a if (y & 1) else 0)) & 0xFFFFFFFF
        self.index = 0

    def next_u32(self) -> int:
        if self.index >= self.N:
            self.twist()
        y = self.mt[self.index]
        self.index += 1
        y ^= (y >> 11)
        y ^= ((y << 7) & 0x9D2C5680)
        y ^= ((y << 15) & 0xEFC60000)
        y ^= (y >> 18)
        return y & 0xFFFFFFFF


def main() -> int:
    rng = MT19937(int.from_bytes(os.urandom(8), 'little'))

    current_secret = None
    round = 0

    def new_secret():
        nonlocal current_secret
        out = rng.next_u32()
        idx = out & ((1 << 20) - 1)
        current_secret = index_to_word(idx)

    successes = 0
    REQUIRED = 5
    print("PascalCTF Wordy", flush=True)
    print("Commands:", flush=True)
    print("  NEW                 -> start a round", flush=True)
    print("  GUESS <word>        -> Wordle feedback (G,Y,_)", flush=True)
    print("  FINAL <word>        -> predict NEXT secret (need 5 correct for flag)", flush=True)
    print("  QUIT                -> exit", flush=True)
    print(f"Alphabet: {ALPHABET}  Length: {L}  Need {REQUIRED} correct predictions", flush=True)
    print("READY", flush=True)

    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        cmd = parts[0].upper()

        if cmd == "NEW":
            if round == 1300:
                print("ERR", flush=True)
                continue
            round += 1
            new_secret()
            print("ROUND STARTED", flush=True)
        elif cmd == "GUESS":
            if len(parts) != 2:
                print("ERR", flush=True)
                continue
            if current_secret is None:
                print("ERR", flush=True)
                continue
            guess = parts[1].strip()
            if len(guess) != L or any(ch not in ALPHABET for ch in guess):
                print("ERR", flush=True)
                continue
            patt = wordle_feedback(guess, current_secret)
            print(f"FEEDBACK {patt}", flush=True)
        elif cmd == "FINAL":
            if len(parts) != 2:
                print("ERR", flush=True)
                continue
            guess = parts[1].strip()
            out = rng.next_u32()
            idx = out & ((1 << 20) - 1)
            next_secret = index_to_word(idx)
            if guess == next_secret:
                successes += 1
                if successes >= REQUIRED:
                    flag = os.getenv("FLAG")
                    print(f"OK {next_secret} {flag}", flush=True)
                else:
                    print(f"OK {next_secret} {successes}/{REQUIRED}", flush=True)
            else:
                print("FAIL", flush=True)
        elif cmd == "QUIT":
            return 0
        else:
            print("ERR", flush=True)

    return 0

if __name__ == "__main__":
    sys.exit(main())