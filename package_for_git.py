import zipfile
import os

# Define files to include (Expert v3.5 version)
files_to_push = ['app.py', 'requirements.txt', 'README.md', '.gitignore']
zip_name = 'Fake_Review_Detector_Upgrade.zip'

try:
    with zipfile.ZipFile(zip_name, 'w') as zipMe:
        for file in files_to_push:
            if os.path.exists(file):
                zipMe.write(file, compress_type=zipfile.ZIP_DEFLATED)
                print(f"[ADDING]: {file}")
            else:
                print(f"[WARNING]: {file} not found")
    print("\n[SUCCESS]: Zip package created.")
    print(f"[LOCATION]: {os.path.abspath(zip_name)}")
    print("\nNext Steps:")
    print("1. Open your repo: https://github.com/pavithra0117/Fake-review-detector")
    print("2. Click 'Add file' -> 'Upload files'")
    print("3. Drag this ZIP file into the browser!")
except Exception as e:
    print(f"[ERROR]: {e}")
