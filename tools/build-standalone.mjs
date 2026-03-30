import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(dirname, "..");
const outputDir = path.join(rootDir, "output", "standalone");

function runCommand(command, args, options = {}) {
    const result = spawnSync(command, args, {
        cwd: rootDir,
        stdio: "inherit",
        shell: false,
        ...options,
    });
    if (result.status !== 0) {
        throw new Error(`Command failed: ${command} ${args.join(" ")}`);
    }
}

function collectFiles(directory, predicate, bucket = []) {
    const entries = fs.readdirSync(directory, { withFileTypes: true });
    for (const entry of entries) {
        const absolutePath = path.join(directory, entry.name);
        if (entry.isDirectory()) {
            collectFiles(absolutePath, predicate, bucket);
            continue;
        }
        if (predicate(absolutePath)) {
            bucket.push(absolutePath);
        }
    }
    return bucket;
}

function copyFileIntoOutput(sourcePath, relativeDestination) {
    const destinationPath = path.join(outputDir, relativeDestination);
    fs.mkdirSync(path.dirname(destinationPath), { recursive: true });
    fs.copyFileSync(sourcePath, destinationPath);
}

function exportBootstrapData() {
    const scriptPath = path.join(rootDir, "tools", "export_bootstrap_data.py");
    const destinationPath = path.join(outputDir, "standalone-bootstrap.json");
    const candidates = process.platform === "win32"
        ? [
            [process.env.PYTHON, []],
            ["py", ["-3"]],
            ["python", []],
        ]
        : [
            [process.env.PYTHON, []],
            ["python3", []],
            ["python", []],
        ];

    for (const [command, prefixArgs] of candidates) {
        if (!command) {
            continue;
        }
        const result = spawnSync(command, [...prefixArgs, scriptPath, destinationPath], {
            cwd: rootDir,
            stdio: "inherit",
            shell: false,
        });
        if (result.status === 0) {
            return;
        }
    }

    throw new Error("Unable to export standalone bootstrap data because no working Python interpreter was found.");
}

function writePythonManifest() {
    const sourceRoots = [
        path.join(rootDir, "backend"),
        path.join(rootDir, "config"),
    ];
    const files = sourceRoots.flatMap((sourceRoot) => collectFiles(
        sourceRoot,
        (absolutePath) => absolutePath.endsWith(".py") || absolutePath.endsWith(".json"),
    ));

    const manifestEntries = files.map((absolutePath) => {
        const relativePath = path.relative(rootDir, absolutePath).replace(/\\/g, "/");
        const outputRelativePath = `py-src/${relativePath}`;
        copyFileIntoOutput(absolutePath, outputRelativePath);
        return {
            url: `./${outputRelativePath}`,
            target_path: `/app/${relativePath}`,
        };
    });

    fs.writeFileSync(
        path.join(outputDir, "standalone-python-manifest.json"),
        JSON.stringify({ files: manifestEntries }, null, 2),
        "utf8",
    );
}

function copyStaticAssets() {
    copyFileIntoOutput(path.join(rootDir, "static", "css", "styles.css"), "styles.css");
    copyFileIntoOutput(path.join(rootDir, "static", "favicon.svg"), "favicon.svg");
    const standaloneHtmlPath = path.join(outputDir, "standalone.html");
    if (fs.existsSync(standaloneHtmlPath)) {
        fs.copyFileSync(standaloneHtmlPath, path.join(outputDir, "index.html"));
    }
    fs.writeFileSync(path.join(outputDir, ".nojekyll"), "", "utf8");
}

function buildStandaloneFrontend() {
    runCommand(process.execPath, [path.join(rootDir, "node_modules", "vite", "bin", "vite.js"), "build", "--mode", "standalone"]);
}

buildStandaloneFrontend();
copyStaticAssets();
exportBootstrapData();
writePythonManifest();
