import os
import re
import subprocess
import sys
import pkgutil
import difflib
import importlib

# Known mappings for common package name differences
PACKAGE_MAPPING = {
    "discord": "discord.py",
    "PIL": "pillow",
    "cv2": "opencv-python",
    "yaml": "pyyaml",
    "sklearn": "scikit-learn",
    "Crypto": "pycryptodome"
}

def is_standard_library(module_name):
    """Check if the module is part of the Python standard library."""
    if module_name in sys.builtin_module_names:
        return True

    stdlib_path = getattr(sys, 'prefix', '') + '/lib/python'
    for path in sys.path:
        if path.startswith(stdlib_path):
            if importlib.util.find_spec(module_name):
                return True
    return False

def is_package_installed(package_name):
    """Check if a package is installed in the current environment."""
    return importlib.util.find_spec(package_name) is not None

def find_closest_package(module_name):
    """Find the closest matching package name."""
    installed_packages = subprocess.check_output(["pip", "freeze"]).decode().splitlines()
    installed_packages = [pkg.split("==")[0].lower() for pkg in installed_packages]

    if module_name in PACKAGE_MAPPING:
        return PACKAGE_MAPPING[module_name]  # Use predefined mapping

    matches = difflib.get_close_matches(module_name, installed_packages, n=1, cutoff=0.6)
    return matches[0] if matches else None  # Return closest match if found

def traverse_directory(dir_path, file_list=None):
    """Recursively traverse the directory and collect Python file paths, excluding venv directories."""
    if file_list is None:
        file_list = []

    for root, dirs, files in os.walk(dir_path):
        for excluded in ["venv", ".venv", "Dependency"]:
            if excluded in dirs:
                dirs.remove(excluded)

        for file in files:
            if file.endswith(".py"):  # Only scan Python files
                full_path = os.path.join(root, file)
                file_list.append(full_path)

    return file_list

def find_required_packages(files):
    """Extract external packages from Python files and find the correct package names."""
    packages = set()
    import_regex = r'^\s*(?:import|from)\s+([\w\.]+)'

    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.match(import_regex, line)
                if match:
                    module_name = match.group(1).split('.')[0]

                    if is_standard_library(module_name):
                        continue  # Skip standard libraries

                    if is_package_installed(module_name):
                        packages.add(module_name)  # Already correct
                    else:
                        corrected_name = find_closest_package(module_name)
                        if corrected_name:
                            packages.add(corrected_name)

    return list(packages)

def install_packages(packages):
    """Install missing external packages using pip."""
    if packages:
        print(f"Installing packages: {', '.join(packages)}")
        try:
            subprocess.check_call(["pip", "install", *packages])
            print("All packages installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing packages: {e}")
    else:
        print("No external packages detected.")

def main():
    project_dir = "/home/container"
    requirements_path = os.path.join(project_dir, "requirements.txt")

    # Exit if requirements.txt does not exist
    if not os.path.exists(requirements_path):
        print("Error: requirements.txt not found. Exiting.")
        return

    print("Scanning all project files for required packages...")
    files = traverse_directory(project_dir)
    packages = find_required_packages(files)

    print(f"Found required packages: {', '.join(packages)}")

    # Append only new packages to requirements.txt
    with open(requirements_path, "r+", encoding="utf-8") as f:
        existing_packages = set(line.strip() for line in f if line.strip())
        new_packages = [pkg for pkg in packages if pkg not in existing_packages]
        if new_packages:
            f.write("\n".join(new_packages) + "\n")
    
    # Install packages
    install_packages(new_packages)

if __name__ == "__main__":
    main()
