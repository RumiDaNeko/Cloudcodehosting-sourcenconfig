import os
import re
import subprocess
import sys
import importlib
import difflib

PACKAGE_MAPPING = {
    "discord": "discord.py",
    "PIL": "pillow",
    "cv2": "opencv-python",
    "yaml": "pyyaml",
    "sklearn": "scikit-learn",
    "Crypto": "pycryptodome"
}

checked_modules = {}
cached_installed_packages = None

def get_installed_packages():
    global cached_installed_packages
    if cached_installed_packages is None:
        try:
            result = subprocess.check_output(["pip", "freeze"]).decode().splitlines()
            cached_installed_packages = [pkg.split("==")[0].lower() for pkg in result]
        except Exception:
            cached_installed_packages = []
    return cached_installed_packages

def is_standard_library(module_name):
    if module_name in checked_modules:
        return checked_modules[module_name]

    try:
        spec = importlib.util.find_spec(module_name)
        result = bool(spec and spec.origin and "site-packages" not in spec.origin)
    except Exception:
        result = False

    checked_modules[module_name] = result
    return result

def is_package_installed(module_name):
    if module_name in checked_modules:
        return checked_modules[module_name]

    try:
        result = importlib.util.find_spec(module_name) is not None
    except Exception:
        result = False

    checked_modules[module_name] = result
    return result

def find_closest_package(module_name):
    if module_name in PACKAGE_MAPPING:
        return PACKAGE_MAPPING[module_name]

    packages = get_installed_packages()
    matches = difflib.get_close_matches(module_name.lower(), packages, n=1, cutoff=0.6)
    return matches[0] if matches else module_name

def traverse_directory(dir_path):
    file_list = []
    for root, dirs, files in os.walk(dir_path):
        for exclude in ["venv", ".venv", "Dependency"]:
            if exclude in dirs:
                dirs.remove(exclude)
        for file in files:
            if file.endswith(".py"):
                file_list.append(os.path.join(root, file))
    return file_list

def find_required_packages(files):
    packages = set()
    seen_modules = set()
    import_pattern = re.compile(r'^\s*(?:import|from)\s+([\w\.]+)')

    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    match = import_pattern.match(line)
                    if match:
                        module = match.group(1).split('.')[0]
                        if module in seen_modules:
                            continue
                        seen_modules.add(module)

                        if is_standard_library(module):
                            continue
                        if is_package_installed(module):
                            packages.add(module)
                        else:
                            packages.add(find_closest_package(module))
        except (UnicodeDecodeError, FileNotFoundError):
            continue

    return list(packages)

def install_packages(packages):
    if not packages:
        print("No new packages to install.")
        return

    print(f"Installing: {', '.join(packages)}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])
        print("Installation complete.")
    except subprocess.CalledProcessError as e:
        print(f"Installation failed: {e}")

def main():
    project_dir = "/home/container"
    requirements_file = os.path.join(project_dir, "requirements.txt")

    if not os.path.exists(requirements_file):
        print("requirements.txt not found. Exiting.")
        return

    print("Scanning for dependencies...")
    files = traverse_directory(project_dir)
    packages = find_required_packages(files)

    print(f"Detected packages: {', '.join(packages)}")

    with open(requirements_file, "r+", encoding="utf-8") as f:
        existing = set(line.strip() for line in f if line.strip())
        new_packages = [pkg for pkg in packages if pkg not in existing]

        if new_packages:
            f.write("\n" + "\n".join(new_packages) + "\n")

    install_packages(new_packages)

if __name__ == "__main__":
    main()
