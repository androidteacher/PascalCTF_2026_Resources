import socket

HOST = "scripting.ctf.pascalctf.it"
PORT = 6004

def interact():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # s.settimeout(2.0) # Remove timeout to avoid early exit if server is slow
        print(f"[*] Connecting to {HOST}:{PORT}...")
        s.connect((HOST, PORT))
        
        # Read until prompt
        buffer = ""
        while True:
            data = s.recv(1024).decode()
            buffer += data
            print(data, end="")
            if "(press Enter):" in buffer:
                break
        
        # Press Enter to start
        print("\n[*] Sending Enter to start...")
        s.sendall(b"\n")
        
        # Read the Module description
        buffer = ""
        while True:
            data = s.recv(1024).decode()
            if not data: break
            buffer += data
            print(data, end="")
            # Check if it asks for input (usually ends in ": ")
            if "Answer:" in buffer or ">" in buffer.split('\n')[-1]: 
                break
        
        s.close()
    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    interact()
