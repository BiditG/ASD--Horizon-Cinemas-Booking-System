import subprocess
import sys

def main():
    print("Installing autopep8...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "autopep8"])
    
    print("Running autopep8 to fix PEP8 issues in-place recursively...")
    print("This will format your source files to comply with PEP8 standards.")
    
    # Run autopep8 across the project
    result = subprocess.run([sys.executable, "-m", "autopep8", "--in-place", "--aggressive", "--recursive", "."], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Successfully formatted all Python files!")
    else:
        print("Completed with some errors:")
        print(result.stderr)

if __name__ == "__main__":
    main()
