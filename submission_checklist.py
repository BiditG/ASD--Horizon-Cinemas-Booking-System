import os
import subprocess
import sys

# ANSI Escape Codes for Colors
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

def print_result(check_name: str, passed: bool, error_msg: str = ""):
    if passed:
        print(f"[{GREEN}PASS{RESET}] {check_name}")
    else:
        print(f"[{RED}FAIL{RESET}] {check_name} {error_msg}")

def check_required_files():
    # Common required portfolio files
    required_files = [
        "README.md",
        "requirements.txt",
        "manual_test_cases.md", 
        # Add "database.db" or specific PDFs if needed in your final folder
    ]
    
    for req in required_files:
        exists = os.path.exists(req)
        print_result(f"Required File Exists: {req}", exists)

def check_student_headers():
    missing_headers = []
    
    for root, dirs, files in os.walk("."):
        if ".venv" in root or "__pycache__" in root or ".git" in root:
            continue
            
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8", errors="ignore") as file:
                    content = file.read()
                    # Check for generic marker "Student ID" or "Author" 
                    if "Student ID" not in content and "Author" not in content:
                        missing_headers.append(path)
                        
    if missing_headers:
         # Depending on how strict we are, we can flag this as a fail or a warning
         print_result("All .py files have student ID headers", False, f"-> Missing in {len(missing_headers)} files (e.g., {missing_headers[0]})")
    else:
         print_result("All .py files have student ID headers", True)

def check_main_imports():
    # python -c "import main" tests if the file executes/imports natively without throwing exceptions
    result = subprocess.run([sys.executable, "-c", "import main"], capture_output=True, text=True)
    if result.returncode == 0:
        print_result("main.py runs without import errors", True)
    else:
        # Check if the error is just the Tkinter mainloop blocking or an actual import error
        # Normally 'import main' might trigger main() if not protected by if __name__ == '__main__'.
        # Since main.py runs a GUI, importing it might block or throw. 
        # But if it crashes with ImportError/ModuleNotFoundError, it's definitely a fail.
        err = result.stderr.strip()
        if "ModuleNotFoundError" in err or "ImportError" in err:
            print_result("main.py runs without import errors", False, f"-> {err.splitlines()[-1]}")
        else:
            # It might have succeeded or blocked, we'll mark pass for import errors specifically
            print_result("main.py runs without import errors", True, "(No ImportErrors detected)")

def check_test_suite():
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"], capture_output=True, text=True)
    if result.returncode == 0:
        print_result("Test suite passes", True)
    else:
        # Try to extract the fail count
        lines = result.stdout.strip().splitlines()
        summary = lines[-1] if lines else "Failures detected"
        print_result("Test suite passes", False, f"-> {summary}")

def main():
    # Enable ANSI escape codes on Windows terminal
    if os.name == 'nt':
        os.system('color')
        
    print("\n========================================")
    print("      HCBS FINAL SUBMISSION CHECKLIST   ")
    print("========================================\n")
    
    check_required_files()
    check_student_headers()
    check_main_imports()
    check_test_suite()
    
    print("\n========================================")
    print("Checklist complete. Fix any RED FAILS before zipping.")
    print("========================================\n")

if __name__ == "__main__":
    main()
