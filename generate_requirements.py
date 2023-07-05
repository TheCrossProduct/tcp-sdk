packages_map = {"nats_py": "nats-py"}

with open("setup.py") as f:
    text = f.read ()
    requires = text.split('[')[1].split(']')[0]
    requires = requires.split(',')

    packages = []
    for r in requires:
        r = r.replace ('\n', '').replace (' ', '').replace ('"','').replace('-', '_').lower()
        if r in packages_map:
            r = packages_map[r]
        packages.append (r)

cmd = 'nix-shell -p python3Packages.'
output = cmd + 'pip'
for p in packages:
    output += ' python3Packages.' +  p + ' '
print (output)
