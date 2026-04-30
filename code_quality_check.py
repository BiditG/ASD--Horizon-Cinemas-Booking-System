import subprocess
import os
import re
import sys

def run_flake8():
    print("Running flake8 (this may take a moment)...")
    # Using sys.executable to ensure we use the current virtual environment's pip/flake8
    result = subprocess.run([sys.executable, "-m", "flake8", "src/", "tests/", "main.py"], capture_output=True, text=True)
    with open("flake8_report.txt", "w", encoding="utf-8") as f:
        f.write(result.stdout)
        if result.stderr:
            f.write("\nErrors:\n" + result.stderr)
    
    # Count violations (number of non-empty lines in stdout)
    lines = result.stdout.strip().split("\n")
    violations = len([l for l in lines if l.strip()])
    return violations

def run_pylint():
    print("Running pylint...")
    result = subprocess.run([sys.executable, "-m", "pylint", "src/", "tests/", "main.py", "--exit-zero"], capture_output=True, text=True)
    with open("pylint_report.txt", "w", encoding="utf-8") as f:
        f.write(result.stdout)
        if result.stderr:
            f.write("\nErrors:\n" + result.stderr)
    
    # Extract score: "Your code has been rated at X/10"
    score_match = re.search(r"Your code has been rated at ([-.\d]+)/10", result.stdout)
    score = score_match.group(1) if score_match else "Unknown"
    return score

def main():
    print("Installing linter dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "flake8", "pylint"])
    
    # Count python files excluding venv and cache
    py_files = 0
    for root, dirs, files in os.walk("."):
        if ".venv" in root or "__pycache__" in root or ".git" in root:
            continue
        py_files += sum(1 for f in files if f.endswith(".py"))
        
    violations = run_flake8()
    score = run_pylint()
    
    print("\n" + "="*50)
    print("             CODE QUALITY SUMMARY               ")
    print("="*50)
    print(f"Total .py files checked : {py_files}")
    print(f"Total PEP8 violations   : {violations}")
    print(f"Pylint Score            : {score} / 10.00")
    print("="*50)
    print("Detailed reports saved to: flake8_report.txt, pylint_report.txt")

if __name__ == "__main__":
    main()
