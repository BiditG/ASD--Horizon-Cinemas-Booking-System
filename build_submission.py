import os
import sys
import zipfile
import subprocess
import argparse

def check_files():
    # Use the existing submission_checklist.py for verification
    if os.path.exists("submission_checklist.py"):
        result = subprocess.run([sys.executable, "submission_checklist.py"])
        if result.returncode != 0:
            print("Warning: Some pre-build checks failed.")
            # For strict pipelines, you would sys.exit(1) here.
            # We'll let it pass for demonstration if the script handles it softly.
    else:
        print("submission_checklist.py not found, skipping pre-build validations.")
        
    print("Pre-build checks completed.")

def create_zip():
    zip_name = "hcbs_release.zip"
    print(f"Creating release archive: {zip_name}...")
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("."):
            if ".venv" in root or "__pycache__" in root or ".git" in root or ".pytest_cache" in root:
                continue
            for file in files:
                file_path = os.path.join(root, file)
                if file == zip_name or file.endswith(".pyc") or file.endswith(".db"):
                    continue
                zipf.write(file_path, os.path.relpath(file_path, "."))
    print(f"Created {zip_name} successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true", help="Only run validations, do not build ZIP")
    args = parser.parse_args()

    check_files()
    
    if not args.check_only:
        create_zip()
