blacklist = [
    "flag", "etc", "sh", "bash", 
    "proc", "pascal", "tmp", "env", 
    "bash", "exec", "file", "pascalctf is not fun"
]

with open('/home/josh/shared/pdfile/exploit.pasx', 'r') as f:
    content = f.read().lower()

found = []
for word in blacklist:
    if word in content:
        found.append(word)

if found:
    print(f"FAILED: Found banned words: {found}")
else:
    print("SUCCESS: No banned words found.")
