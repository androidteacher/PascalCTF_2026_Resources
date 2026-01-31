# Scripting Challenge: Bombare Defusal

## Goal
Solve the "Bombare" (Minesweeper/KTANE clone) challenge by automating the defusal of 100 modules within 60 seconds.

## Challenge Analysis
- **Service**: `scripting.ctf.pascalctf.it:6004`
- **Protocol**: TCP Text-based interaction.
- **Modules**: 
  - `Wires`: Standard Keep Talking and Nobody Explodes (KTANE) logic (3-6 wires).
  - `Keypads`: Orders symbols based on standard columns.
  - `Button`: Press or Hold logic with Color Strip release digits.
  - `Complicated Wires`: Venn diagram logic with cut instructions.
  - `Simon` (Implemented but not seen in final run).
- **Time Limit**: Very strict (<60s for 100 modules). Requires ~0.6s per module.

## Solution Strategy
1. **Automation**: Python script using `socket`.
2. **Logic Implementation**:
   - Implemented standard KTANE rules for all observed modules.
   - **Keypads**: Handled Unicode normalization (e.g., `ƀ` -> `Ѣ`, `Ͼ` -> `C`, `ψ` -> `Ψ`).
   - **Wires**: Fixed logic for 4-wire "More than 1 yellow" rule.
   - **Button**: Handled non-interactive "Hold" by calculating the release digit based on `color_strip` data provided in the prompt.
3. **Optimization**:
   - **Pipelining**: Removed all `read_until(prompt)` waits. The script sends the newline to trigger the next module *immediately* after sending the previous answer, complying with the TCP stream but eliminating Round-Trip-Time (RTT) latency.
   - **Buffer Consumption**: Aggressively consumed processed buffer data to prevent memory growth and search overhead.

## Flag
`pascalCTF{H0w_4r3_Y0u_s0_g0Od_4t_BOMBARE?}`

## Code
The solver script is located at `/home/josh/shared/pdfile/scripting/solve_scripting.py`.

```python
# Key optimization snippet: Pipelining
for i in range(100):
    self.sock.sendall(b"\n") # Trigger next module blind
    if not self.read_until("Module:"): break # Wait for Data
    # ... logic ...
    self.sock.sendall((answer + "\n").encode()) # Send answer blind
```
