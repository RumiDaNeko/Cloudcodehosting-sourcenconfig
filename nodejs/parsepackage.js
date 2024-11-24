const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

function traverseDirectory(dir, fileList = []) {
  const files = fs.readdirSync(dir);

  files.forEach((file) => {
    const fullPath = path.join(dir, file);
    
    if (file === "node_modules") {
      return;
    }
    
    if (fs.statSync(fullPath).isDirectory()) {
      traverseDirectory(fullPath, fileList);
    } else {
      fileList.push(fullPath);
    }
  });

  return fileList;
}

function findRequiredPackages(files) {
  const packageSet = new Set();
  const requireRegex = /require\(['"]([^'"]+)['"]\)/g;
  const importRegex = /import(?:.+from\s+)?['"]([^'"]+)['"]/g;

  files.forEach((file) => {
    if (file.endsWith(".js") || file.endsWith(".ts") || file.endsWith(".mjs")) {
      const content = fs.readFileSync(file, "utf-8");

      let match;
      while ((match = requireRegex.exec(content)) !== null) {
        packageSet.add(match[1]);
      }

      while ((match = importRegex.exec(content)) !== null) {
        packageSet.add(match[1]);
      }
    }
  });

  return Array.from(packageSet).filter(
    (pkg) => !pkg.startsWith(".") // Ignore local file imports
  );
}

function installPackages(packages) {
  if (packages.length > 0) {
    console.log("Installing packages:", packages.join(", "));
    execSync(`npm install ${packages.join(" ")}`, { stdio: "inherit" });
    console.log("All packages installed successfully.");
  } else {
    console.log("No external packages detected.");
  }
}

function main() {
  const projectDir = path.resolve("/home/container");
  const packageJsonPath = path.join(projectDir, "package.json");

  // Check if package.json exists, create if not
  if (!fs.existsSync(packageJsonPath)) {
    console.log("No package.json found. Creating a new one...");
    fs.writeFileSync(
      packageJsonPath,
      JSON.stringify(
        {
          name: "dynamic-project",
          version: "1.0.0",
          description: "Auto-generated package.json",
          main: "index.js",
          scripts: {
            start: "node index.js",
          },
          dependencies: {},
        },
        null,
        2
      )
    );
  }

  console.log("Scanning all project files for required packages...");
  const files = traverseDirectory(projectDir);
  const packages = findRequiredPackages(files);

  console.log(`Found required packages: ${packages.join(", ")}`);
  installPackages(packages);
}

main();
