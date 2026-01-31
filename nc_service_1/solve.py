
import sys
import subprocess
import time
import os

# --- Copy of Service Code Logic for Prediction ---
ALPHABET = "abcdefghijklmnop"
K = len(ALPHABET)
L = 5
N_WORDS = K ** L

def index_to_word(idx: int) -> str:
    digits = []
    x = idx
    for _ in range(L):
        digits.append(x % K)
        x //= K
    letters = [ALPHABET[d] for d in reversed(digits)]
    return "".join(letters)

def word_to_index(word: str) -> int:
    x = 0
    for ch in word:
        d = ALPHABET.find(ch)
        x = x * K + d
    return x

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

# --- Solver ---

class Solver:
    def __init__(self):
        import socket
        self.host = "wordy.ctf.pascalctf.it"
        self.port = 5005
        print(f"[*] Connecting to {self.host}:{self.port}...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.buffer = ""
        self.read_until("READY")

    def read_until(self, substring):
        while substring not in self.buffer:
            data = self.sock.recv(1024).decode()
            if not data:
                break
            self.buffer += data
        
        # Determine where the substring ends to keep the rest in buffer
        # But for this simple protocol, we just rely on the buffer accumulating
        return self.buffer

    def send(self, line):
        self.sock.sendall((line + "\n").encode())

    def get_feedback(self):
        # The buffer might already have the feedback line if we read too much
        # But usually we read until "FEEDBACK"
        if "FEEDBACK" not in self.buffer:
             self.read_until("FEEDBACK")
        
        # Now parse it out.
        # Format might be "... FEEDBACK GGGGG\n"
        # We need to be careful with the buffer management.
        
        # Simpler approach: read line by line from buffer
        # But let's just do a specialized read.
        
        # Ensure we have the full line after FEEDBACK
        while True:
             if "FEEDBACK " in self.buffer:
                 parts = self.buffer.split("FEEDBACK ")
                 if '\n' in parts[1]:
                     feedback = parts[1].split('\n')[0].strip()
                     # Clear buffer up to that point to avoid re-reading
                     # (Not strictly necessary for this linear flow but good practice)
                     self.buffer = parts[1].split('\n', 1)[1] if '\n' in parts[1] else ""
                     return feedback
             
             data = self.sock.recv(1024).decode()
             if not data:
                 break
             self.buffer += data
        return ""

    def recover_round_secret(self):
        # 16-guess strategy to recover secret perfectly
        # For each char in 'abc...p', send "aaaaa", "bbbbb" etc.
        # The feedback tells us exactly where that char appears.
        
        final_word_list = [None] * L
        
        for char_code in range(K): # 0 to 15
            char = ALPHABET[char_code]
            guess = char * L
            self.send(f"GUESS {guess}")
            feedback = self.get_feedback() # e.g. "G_G__"
            
            for i, f in enumerate(feedback):
                if f == 'G':
                    final_word_list[i] = char
            
            # Optimization: check if full
            if all(final_word_list):
                break
                
        return "".join(final_word_list)

    def solve(self):
        print("[*] Starting Solver...")
        
        # 1. Recover first two secrets (2 rounds)
        print("[*] Recovering Round 1 Secret...")
        self.send("NEW")
        self.read_until("ROUND STARTED")
        word1 = self.recover_round_secret()
        idx1 = word_to_index(word1)
        print(f"    Secret 1: {word1} (Index: {idx1})")

        print("[*] Recovering Round 2 Secret...")
        self.send("NEW")
        self.read_until("ROUND STARTED")
        word2 = self.recover_round_secret()
        idx2 = word_to_index(word2)
        print(f"    Secret 2: {word2} (Index: {idx2})")
        
        # 2. Crack Seed
        print("[*] Cracking Seed (this may take 1-2 minutes)...")
        # Ensure compiled
        if not os.path.exists("./crack_seed"):
            print("[-] crack_seed binary not found!")
            sys.exit(1)
            
        t0 = time.time()
        res = subprocess.run(
            ["./crack_seed", str(idx1), str(idx2)], 
            capture_output=True, 
            text=True
        )
        t1 = time.time()
        
        if res.returncode != 0 or not res.stdout.strip():
            print("[-] Failed to find seed.")
            print(res.stderr)
            sys.exit(1)
            
        seed = int(res.stdout.strip())
        print(f"[+] Found Seed: {seed} (Time: {t1-t0:.2f}s)")
        
        # 3. Predict Future
        print("[*] Simulating PRNG state...")
        rng = MT19937(seed)
        
        # Step through the 2 rounds we already saw
        # Round 1
        rng.next_u32() 
        # Round 2
        rng.next_u32()
        
        # Now we are synced.
        # We need 5 consecutive correct predictions.
        print("[*] Sending 5 FINAL predictions...")
        
        for i in range(5):
            # Predict
            out = rng.next_u32()
            idx = out & ((1 << 20) - 1)
            next_secret = index_to_word(idx)
            
            print(f"    Round {i+1} Prediction: {next_secret}")
            self.send(f"FINAL {next_secret}")
            
            # Check response
            # We expect "OK" or "FAIL"
            while "OK" not in self.buffer and "FAIL" not in self.buffer and "ERR" not in self.buffer:
                 data = self.sock.recv(1024).decode()
                 if not data: break
                 self.buffer += data
            
            # Extract line
            if "OK " in self.buffer:
                resp = "OK " + self.buffer.split("OK ")[1].split("\n")[0]
                # clear buffer
                if "\n" in self.buffer.split("OK ")[1]:
                    self.buffer = self.buffer.split("OK ")[1].split("\n", 1)[1]
            else:
                 resp = self.buffer.split("\n")[0] # Fallback
            
            print(f"    Server: {resp}")
            if "OK" in resp and "{" in resp:
                print(f"\n[!!!] FLAG CAPTURED: {resp.split()[-1]}")
                break
        
        self.send("QUIT")

if __name__ == "__main__":
    if not os.path.exists("./crack_seed"):
        print("Compiling crack_seed.c...")
        subprocess.run(["gcc", "-O3", "-fopenmp", "-o", "crack_seed", "crack_seed.c"])
        
    s = Solver()
    s.solve()
