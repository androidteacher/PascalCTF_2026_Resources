# Reverse Engineering 'curly-crab'

## Goal
Recover the flag from the `curly-crab` Rust binary.

## Analysis
- **Binary**: `curly-crab` (ELF 64-bit, unstripped Rust binary).
- **Hint**: "A crab stole my json schema...".
- **Behavior**: Reads JSON from stdin. Prints "😔" on error, "🦀" on success.

## Method: Schema Discovery via GDB
The binary uses `serde_json` for deserialization. When dynamic deserialization fails (e.g., missing field), `serde_json` creates an internal error containing the specific missing field name.

To recover the schema:
1.  Ran the binary with `gdb`.
2.  Disassembled `curly_crab::main` and located the call to `serde_json::de::from_trait`.
3.  Set a breakpoint immediately after the call (`0x55555558274f`).
4.  Provided generic JSON input (e.g., `{}`) and inspected the `Result` return value on the stack.
5.  Extracted the `serde_json::Error` object from the `Err` variant and found the pointer to the error message string (e.g., "missing field `pascal`").
6.  Iteratively updated the input JSON with the discovered fields to reveal the next missing field.

### Reconstructed Schema
```json
{
  "pascal": "test",
  "CTF": 123,
  "crab": {
    "I_": true,
    "crabby": {
      "l0v3_": [],
      "r3vv1ng_": 123
    },
    "cr4bs": 123
  }
}
```

## Flag Construction
The flag is composed of the *leaf* keys of the valid JSON schema (or the specific fields discovered in order).

Schema Keys Order:
1. `pascal` (String) -> `pascal`
2. `CTF` (u64) -> `CTF`
3. `I_` (Boolean) -> `I_`
4. `l0v3_` (Array) -> `l0v3_`
5. `r3vv1ng_` (u64) -> `r3vv1ng_`
6. `cr4bs` (i64) -> `cr4bs`

Concatenating the leaf keys into the flag format:
`pascalCTF{I_l0v3_r3vv1ng_cr4bs}`

## Verification
Providing the constructed JSON to the binary results in the success output:
```bash
$ ./curly/curly-crab < curly/solution.json
Give me a JSONy flag!
🦀
```
