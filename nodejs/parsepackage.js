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

function isLocalPath(moduleName) {
  return (
    moduleName.startsWith("./") ||
    moduleName.startsWith("../") ||
    moduleName.startsWith("/") || // Absolute paths
    moduleName.includes("__dirname") || // Handles dynamic imports using __dirname
    moduleName.includes("path.join") // Handles path.join constructs
  );
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
        if (!isLocalPath(match[1])) {
          packageSet.add(match[1]);
        }
      }

      while ((match = importRegex.exec(content)) !== null) {
        if (!isLocalPath(match[1])) {
          packageSet.add(match[1]);
        }
      }
    }
  });

  return Array.from(packageSet).filter(
    (pkg) => !pkg.startsWith(".") // Double-check to ignore local imports
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

  console.log("Scanning all project files for required packages...");
  const files = traverseDirectory(projectDir);
  const packages = findRequiredPackages(files);

  console.log(`Required packages: ${packages.length === 0 ? packages.join(", ") : "None" }`);
  installPackages(packages);
}

main();
