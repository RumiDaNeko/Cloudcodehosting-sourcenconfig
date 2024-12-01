import os
import re
import subprocess
import io  # Use for encoding
import sys
import os
import pkgutil
import re

def is_standard_library(module_name):
    """Check if a module is part of the Python standard library."""
    if module_name in sys.builtin_module_names:  # Check built-in modules
        return True

    # Get the path to the standard library
    stdlib_paths = [os.path.dirname(os.__file__)]
    if hasattr(sys, 'real_prefix'):  # For virtualenvs
        stdlib_paths.append(os.path.join(sys.real_prefix, 'lib'))

    for stdlib_path in stdlib_paths:
        for root, dirs, files in os.walk(stdlib_path):
            if f"{module_name}.py" in files or module_name in dirs:
                return True

    # In Python 2.x, `pkgutil` might not work consistently for all standard libraries
    return pkgutil.find_loader(module_name) is not None

def traverse_directory(dir_path, file_list=None):
    if file_list is None:
        file_list = []

    for root, dirs, files in os.walk(dir_path):
        # Skip Python virtual environment directories
        if "venv" in dirs:
            dirs.remove("venv")
        if ".venv" in dirs:
            dirs.remove(".venv")

        for file in files:
            full_path = os.path.join(root, file)
            file_list.append(full_path)

    return file_list

def is_local_path(module_name):
    return (
        module_name.startswith("./") or
        module_name.startswith("../") or
        module_name.startswith("/") or
        "__file__" in module_name or
        "os.path" in module_name
    )

def find_required_packages(files):
    packages = set()
    import_regex = r'^\s*(?:import|from)\s+([\w\.]+)'

    for file in files:
        with open(file, 'r') as f:
            for line in f:
                match = re.match(import_regex, line)
                if match:
                    module_name = match.group(1).split('.')[0]
                    if not is_standard_library(module_name):  # Exclude standard libraries
                        packages.add(module_name)

    return list(packages)
    
def install_packages(packages):
    if packages:
        print("Installing packages: {0}".format(", ".join(packages)))
        try:
            subprocess.call(["pip", "install"] + packages)  # Use subprocess.call in Python 2.7
            print("All packages installed successfully.")
        except subprocess.CalledProcessError as e:
            print("Error installing packages: {0}".format(e))
    else:
        print("No external packages detected.")

def main():
    project_dir = "/home/container"
    requirements_path = os.path.join(project_dir, "requirements.txt")

    # Check if requirements.txt exists, create if not
    if not os.path.exists(requirements_path):
        print("No requirements.txt found. Creating a new one...")
        with io.open(requirements_path, "w", encoding="utf-8") as f:  # Use io.open for file writing
            f.write("# Auto-generated requirements.txt\n")

    print("Scanning all project files for required packages...")
    files = traverse_directory(project_dir)
    packages = find_required_packages(files)

    print("Found required packages: {0}".format(", ".join(packages)))

    # Write to requirements.txt
    with io.open(requirements_path, "a", encoding="utf-8") as f:
        for package in packages:
            f.write("{0}\n".format(package))

    # Install packages
    install_packages(packages)

if __name__ == "__main__":
    main()
