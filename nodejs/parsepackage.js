const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const IGNORED_DIRS = new Set(["node_modules", ".git", "dist", "build"]);

function isInsideNodeModules(filePath) {
  return filePath.split(path.sep).includes("node_modules");
}

function traverseDirectory(dir) {
  const fileList = [];
  const stack = [dir];

  while (stack.length > 0) {
    const currentDir = stack.pop();
    let files;
    try {
      files = fs.readdirSync(currentDir);
    } catch (err) {
      console.warn(`Cannot read directory ${currentDir}: ${err.message}`);
      continue;
    }

    for (const file of files) {
      const fullPath = path.join(currentDir, file);

      if (IGNORED_DIRS.has(file)) continue;
      if (isInsideNodeModules(fullPath)) continue;
      
      let stat;
      try {
        stat = fs.statSync(fullPath);
      } catch (err) {
        console.warn(`Cannot access ${fullPath}: ${err.message}`);
        continue;
      }

      if (stat.isDirectory()) {
        stack.push(fullPath);
      } else if (/\.(js|ts|mjs)$/.test(file)) {
        fileList.push(fullPath);
      }
    }
  }

  return fileList;
}

function isLocalPath(moduleName) {
  return (
    moduleName.startsWith("./") ||
    moduleName.startsWith("../") ||
    moduleName.startsWith("/") ||
    moduleName.startsWith("node:") ||
    moduleName.includes("__dirname") ||
    moduleName.includes("path.join")
  );
}

function findRequiredPackages(files) {
  const packageSet = new Set();
  const requireRegex = /require\(['"]([^'"]+)['"]\)/g;
  const importRegex = /import(?:.+from\s+)?['"]([^'"]+)['"]/g;

  for (const file of files) {
    let content;
    try {
      content = fs.readFileSync(file, "utf-8");
    } catch (err) {
      console.warn(`Failed to read ${file}: ${err.message}`);
      continue;
    }

    let match;
    while ((match = requireRegex.exec(content)) !== null) {
      const pkg = match[1];
      if (!isLocalPath(pkg)) packageSet.add(pkg.split("/")[0]);
    }

    while ((match = importRegex.exec(content)) !== null) {
      const pkg = match[1];
      if (!isLocalPath(pkg)) packageSet.add(pkg.split("/")[0]);
    }
  }

  return [...packageSet];
}

function installPackages(packages) {
  if (packages.length > 0) {
    console.log("Installing packages:", packages.join(", "));
    try {
      execSync(`npm install ${packages.join(" ")}`, { stdio: "inherit" });
      console.log("All packages installed successfully.");
    } catch (err) {
      console.error("Failed to install packages:", err.message);
    }
  } else {
    console.log("No external packages detected.");
  }
}

function main() {
  const projectDir = path.resolve("/home/container");
  console.log("Scanning project files for required packages...");

  const files = traverseDirectory(projectDir);
  const packages = findRequiredPackages(files);

  console.log(
    packages.length > 0
      ? `Required packages: ${packages.join(", ")}`
      : "No required packages found."
  );

  installPackages(packages);
}

main();
