import socket
import re
import ast
import time
import sys

HOST = "scripting.ctf.pascalctf.it"
PORT = 6004

class BombSolver:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serial = ""
        self.serial_odd = False
        self.serial_vowel = False
        self.batteries = 0
        self.has_car = False
        self.has_frk = False
        self.has_parallel = False
        self.buffer = ""

    def connect(self):
        print(f"[*] Connecting to {HOST}:{PORT}...")
        self.sock.connect((HOST, PORT))
        if not self.read_until("Select Module 1"):
            print("[-] Failed to verify start.")
            sys.exit(1)
            
        m_serial = re.search(r"Serial Number: (\w+)", self.buffer)
        if m_serial:
            self.serial = m_serial.group(1)
            digits = [c for c in self.serial if c.isdigit()]
            if digits:
                self.serial_odd = int(digits[-1]) % 2 != 0
            if any(c.lower() in 'aeiou' for c in self.serial):
                self.serial_vowel = True
            print(f"[*] Serial: {self.serial} (Odd: {self.serial_odd}, Vowel: {self.serial_vowel})")
            
        m_bat = re.search(r"Batteries: (\d+)", self.buffer)
        if m_bat:
            self.batteries = int(m_bat.group(1))
            print(f"[*] Batteries: {self.batteries}")
            
        if "CAR" in self.buffer: self.has_car = True
        if "FRK" in self.buffer: self.has_frk = True
        if "parallel" in self.buffer.lower(): self.has_parallel = True
        print(f"[*] Indicators: CAR={self.has_car}, FRK={self.has_frk}, Parallel={self.has_parallel}")

    def read_until(self, target):
        start = time.time()
        while target not in self.buffer:
            if time.time() - start > 10: return False
            try:
                self.sock.settimeout(5.0)
                data = self.sock.recv(4096).decode()
                if not data: return False
                self.buffer += data
            except socket.timeout: return False
        return True
        
    def consume_until(self, target):
        if target in self.buffer:
            _, remaining = self.buffer.split(target, 1)
            self.buffer = remaining
            return True
        return False

    def get_module_data(self):
        if "Module: " not in self.buffer: self.read_until("Module: ")
        m_name = re.search(r"Module: (\w+)", self.buffer)
        module_name = m_name.group(1) if m_name else "Unknown"
        if "Data: {" not in self.buffer:
            self.read_until("Data: {")
            self.read_until("}")
        m_data = re.search(r"Data: ({.*?})", self.buffer)
        data_dict = {}
        if m_data:
            try:
                data_dict = ast.literal_eval(m_data.group(1))
            except:
                print(f"[-] Failed to parse data: {m_data.group(1)}")
        return module_name, data_dict

    def solve_wires(self, data):
        wires = data.get('colors', [])
        n = len(wires)
        wires = [w.lower() for w in wires]
        cut_position = 0 
        if n == 3:
            if 'red' not in wires: cut_position = 2
            elif wires[-1] == 'white': cut_position = 3
            elif wires.count('blue') > 1: cut_position = [i for i, x in enumerate(wires) if x == 'blue'][-1] + 1
            else: cut_position = 3
        elif n == 4:
            if wires.count('red') > 1 and self.serial_odd: 
                cut_position = [i for i, x in enumerate(wires) if x == 'red'][-1] + 1
            elif wires[-1] == 'yellow' and 'red' not in wires: 
                cut_position = 1
            elif wires.count('blue') == 1: 
                cut_position = 1
            elif wires.count('yellow') > 1: 
                cut_position = 4
            else: 
                cut_position = 2
        elif n == 5:
            if wires[-1] == 'black' and self.serial_odd: cut_position = 4
            elif wires.count('red') == 1 and wires.count('yellow') > 1: cut_position = 1
            elif 'black' not in wires: cut_position = 2
            else: cut_position = 1
        elif n == 6:
            if 'yellow' not in wires and self.serial_odd: cut_position = 3
            elif wires.count('yellow') == 1 and wires.count('white') > 1: cut_position = 4
            elif 'red' not in wires: cut_position = 6
            else: cut_position = 4
        return str(cut_position)

    def solve_keypad(self, data):
        symbols = data.get('symbols', [])
        norm_map = {'ƀ': 'Ѣ', 'ټ': '☺', '≠': '҂', 'Ͼ': 'C', 'ψ': 'Ψ'}
        norm_symbols = []
        for s in symbols:
            norm_symbols.append(norm_map.get(s, s))
        columns = [
            ['Ϙ', 'Ѧ', 'ƛ', 'Ϟ', 'Ѭ', 'ϗ', 'Ͽ'],
            ['Ӭ', 'Ϙ', 'Ͽ', 'Ҩ', '☆', 'ϗ', '¿'],
            ['©', 'Ѽ', 'Ҩ', 'Җ', 'Ԇ', 'ƛ', '☆'],
            ['б', '¶', 'Ѣ', 'Ѭ', 'Җ', '¿', '☺'],
            ['Ψ', '☺', 'Ѣ', 'C', '¶', 'Ѯ', '★'],
            ['б', 'Ӭ', '҂', 'æ', 'Ψ', 'Ҋ', 'Ω']
        ]
        correct_col = None
        for col in columns:
            if all(s in col for s in norm_symbols):
                correct_col = col
                break
        if not correct_col:
            return "1 2 3 4"
        keyed_symbols = []
        for i, ns in enumerate(norm_symbols):
            keyed_symbols.append( (ns, i+1) )
        keyed_symbols.sort(key=lambda x: correct_col.index(x[0]))
        result = [str(x[1]) for x in keyed_symbols]
        return " ".join(result)

    def solve_button(self, data):
        color = data.get('color', '').lower()
        text = data.get('text', '').lower()
        strip_color = data.get('color_strip', '').lower()
        action = "Hold"
        if color == 'blue' and text == 'abort': action = "Hold"
        elif self.batteries > 1 and text == 'detonate': action = "Press"
        elif color == 'white' and self.has_car: action = "Hold"
        elif self.batteries > 2 and self.has_frk: action = "Press"
        elif color == 'yellow': action = "Hold"
        elif color == 'red' and text == 'hold': action = "Press"
        else: action = "Hold"
        return action

    def solve_complicated(self, data):
        colors = data.get('colors', [])
        leds = data.get('leds', [])
        stars = data.get('stars', [])
        answers = []
        for i in range(len(colors)):
            c_str = colors[i]
            r = 'red' in c_str.lower()
            b = 'blue' in c_str.lower()
            s = stars[i]
            l = leds[i]
            act = 'D'
            if not r and not b:
                 if not s and not l: act = 'C'
                 elif not s and l: act = 'D'
                 elif s and not l: act = 'C'
                 elif s and l: act = 'B'
            elif not r and b:
                 if not s and not l: act = 'S'
                 elif not s and l: act = 'P'
                 elif s and not l: act = 'D'
                 elif s and l: act = 'P'
            elif r and not b:
                 if not s and not l: act = 'S'
                 elif not s and l: act = 'B'
                 elif s and not l: act = 'C'
                 elif s and l: act = 'B'
            elif r and b:
                 if not s and not l: act = 'S'
                 elif not s and l: act = 'S'
                 elif s and not l: act = 'P'
                 elif s and l: act = 'D'
            cut = False
            if act == 'C': cut = True
            elif act == 'D': cut = False
            elif act == 'S': cut = not self.serial_odd
            elif act == 'P': cut = self.has_parallel
            elif act == 'B': cut = self.batteries >= 2
            answers.append("cut" if cut else "skip")
        return "\n".join(answers)

    def solve_simon(self, data):
        flashes = data.get('colors', [])
        flashes = [c.lower() for c in flashes]
        mapping = {}
        if self.serial_vowel:
            mapping = {'red': 'blue', 'blue': 'red', 'green': 'yellow', 'yellow': 'green'}
        else:
            mapping = {'red': 'blue', 'blue': 'yellow', 'green': 'green', 'yellow': 'red'}
        result = []
        for f in flashes:
            result.append(mapping.get(f, f).title())
        return " ".join(result)

    def run(self):
        self.connect()
        # Aggressive Loop: Blindly Trigger -> Parse -> Solve -> Send
        for i in range(100):
            self.sock.sendall(b"\n") # Trigger prompt for module i+1
            
            if not self.read_until("Module:"):
                if "Flag" in self.buffer:
                     print("[*] FLAG FOUND in buffer!")
                     print(self.buffer)
                     break
                print("[-] Stream ended or timeout waiting for Module.")
                print(f"Tail: {self.buffer[-200:]}")
                break
            
            module_name, data = self.get_module_data()
            if (i+1) % 10 == 0:
                print(f"[{i+1}/100] Module: {module_name}")
            
            # Optimization: Consume buffer to keep it small
            if "Data: {" in self.buffer:
                 self.consume_until("Data: {")
                 self.consume_until("}")

            answer = ""
            if module_name == "Wires": answer = self.solve_wires(data)
            elif module_name == "Keypads": answer = self.solve_keypad(data)
            elif module_name == "Button": 
                act = self.solve_button(data)
                answer = "1" if act == "Press" else "2"
            elif "Complicated" in module_name: answer = self.solve_complicated(data)
            elif "Simon" in module_name: answer = self.solve_simon(data)
            else:
                print(f"[-] Unimplemented module: {module_name}")
                break
                
            self.sock.sendall((answer + "\n").encode())
            
            if module_name == "Button" and answer == "2":
                strip = data.get('color_strip', 'blue').lower()
                d = "1"
                if strip == 'blue': d = '4'
                elif strip == 'yellow': d = '5'
                self.sock.sendall((d + "\n").encode())
            
            # WE DO NOT WAIT for confirmation. We assume correct.
            # Next loop sends \n to trigger next module.

        print("[*] Loop finished. Reading remaining...")
        self.sock.settimeout(2.0)
        while True:
            try:
                data = self.sock.recv(4096).decode()
                if not data: break
                print(data, end="")
            except: break

if __name__ == "__main__":
    solver = BombSolver()
    solver.run()
