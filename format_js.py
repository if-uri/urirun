import subprocess

with open('temp_script_0.js') as f:
    code = f.read()

# Very basic formatter to introduce newlines safely
formatted = ''
in_string = False
string_char = None
escape = False

for char in code:
    if escape:
        formatted += char
        escape = False
        continue
    if char == '\\':
        formatted += char
        escape = True
        continue
    if char in '"\'`':
        if not in_string:
            in_string = True
            string_char = char
        elif char == string_char:
            in_string = False
            string_char = None
    formatted += char
    if not in_string:
        if char in ';{}':
            formatted += '\n'

with open('temp_script_formatted.js', 'w') as f:
    f.write(formatted)

res = subprocess.run(['node', '--check', 'temp_script_formatted.js'], capture_output=True, text=True)
print("NODE CHECK RESULT:")
print(res.stderr)
