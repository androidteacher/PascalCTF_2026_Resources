import os
try:
    print("\n--- EXPLOIT START ---")
    # Try current directory and typical CTF locations
    paths = ["flag.txt", "../flag.txt", "/flag.txt", "./flag.txt"]
    found = False
    for p in paths:
        if os.path.exists(p):
            with open(p, "r") as f:
                print(f"FLAG FOUND at {p}: {f.read().strip()}")
            found = True
    
    if not found:
        # List directory to help debug
        print(f"Flag not found. files in {os.getcwd()}: {os.listdir('.')}")
        
    print("--- EXPLOIT END ---\n")
except Exception as e:
    print(f"Exploit Error: {e}")
