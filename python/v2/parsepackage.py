import os
import re
import subprocess
import io  # Use for encoding

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
    package_set = set()
    import_regex = re.compile(r'^\s*(?:from|import)\s+([\w.]+)', re.MULTILINE)

    for file in files:
        if file.endswith(".py"):
            with io.open(file, "r", encoding="utf-8") as f:  # Use io.open for encoding in Python 2.7
                content = f.read()
                matches = import_regex.findall(content)
                for match in matches:
                    # Exclude local modules
                    if not is_local_path(match):
                        base_package = match.split(".")[0]  # Only the root package
                        package_set.add(base_package)

    return list(package_set)

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
