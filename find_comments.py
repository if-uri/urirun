with open('temp_script_0.js') as f:
    code = f.read()

# Let's find occurrences of // not inside quotes
in_string = False
string_char = None
escape = False
idx = 0
while idx < len(code):
    char = code[idx]
    if escape:
        escape = False
        idx += 1
        continue
    if char == '\\':
        escape = True
        idx += 1
        continue
    if char in '"\'`':
        if not in_string:
            in_string = True
            string_char = char
        elif char == string_char:
            in_string = False
            string_char = None
    if not in_string and idx + 1 < len(code) and code[idx:idx+2] == '//':
        print(f'Double slash comment found at index {idx}: {code[idx:idx+150]!r}')
    idx += 1
