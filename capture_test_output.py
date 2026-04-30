"""
capture_test_output.py
======================
Programmatically runs pytest and captures the console output to a text file
for portfolio evidence.
"""

import subprocess
import datetime
import sys

def main():
    print("Running test suite and capturing output...")
    # Make sure we use the same python executable to find pytest in the current env
    result = subprocess.run(
        [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short'], 
        capture_output=True, 
        text=True
    )
    
    today = datetime.date.today()
    filename = f'test_output_{today}.txt'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("======================================================================\n")
        f.write("                     HCBS TEST RUN OUTPUT                             \n")
        f.write("======================================================================\n")
        f.write(f"Date Captured : {datetime.datetime.now()}\n")
        f.write(f"Python Exec   : {sys.executable}\n")
        f.write("======================================================================\n\n")
        f.write(result.stdout)
        
        if result.stderr:
            f.write("\n======================================================================\n")
            f.write("                             STDERR                                   \n")
            f.write("======================================================================\n\n")
            f.write(result.stderr)
            
    print(f"Test output successfully captured and saved to {filename}")

if __name__ == "__main__":
    main()
