import os
import re
import subprocess
import sys
import pkgutil

def is_standard_library(module_name):
    """Check if the module is a Python standard library."""
    if module_name in sys.builtin_module_names:
        return True

    stdlib_path = getattr(sys, 'prefix', '') + '/lib/python'  # Standard lib path
    for path in sys.path:
        if path.startswith(stdlib_path):
            if pkgutil.find_loader(module_name):
                return True
    return False

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
                    if not is_standard_library(module_name):
                        packages.add(module_name)

    return list(packages)

def install_packages(packages):
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

    # Check if requirements.txt exists, create if not
    if not os.path.exists(requirements_path):
        print("No requirements.txt found. Creating a new one...")
        with open(requirements_path, "w") as f:
            f.write("# Auto-generated requirements.txt\n")

    print("Scanning all project files for required packages...")
    files = traverse_directory(project_dir)
    packages = find_required_packages(files)

    print(f"Found required packages: {', '.join(packages)}")

    # Write to requirements.txt
    with open(requirements_path, "a") as f:
        for package in packages:
            f.write(f"{package}\n")

    # Install packages
    install_packages(packages)

if __name__ == "__main__":
    main()
