import os
import subprocess

PROJECT_PATH = os.path.abspath(os.curdir) + '/'

# --------------
subprocess.call([f'''sed -i "s%/home/artem/PycharmProjects/arbshot/%{PROJECT_PATH}%g" "config.py"'''], shell=True)
# --------------

print(f'\n{"-" * 26}\n|{" " * 5}Configure Done{" " * 5}|\n{"-" * 26}\n\n')