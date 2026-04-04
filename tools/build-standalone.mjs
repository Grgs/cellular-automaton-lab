import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(dirname, "..");
const outputDir = path.join(rootDir, "output", "standalone");
const standaloneBuildInputDir = path.join(rootDir, "output", ".standalone-build-input");
const standaloneHtmlInputPath = path.join(standaloneBuildInputDir, "standalone.html");
const pythonCandidates = process.platform === "win32"
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

function copyFileIntoDirectory(sourcePath, targetDir, filename = path.basename(sourcePath)) {
    const destinationPath = path.join(targetDir, filename);
    fs.mkdirSync(path.dirname(destinationPath), { recursive: true });
    fs.copyFileSync(sourcePath, destinationPath);
    return destinationPath;
}

function exportBootstrapData() {
    const scriptPath = path.join(rootDir, "tools", "export_bootstrap_data.py");
    const destinationPath = path.join(outputDir, "standalone-bootstrap.json");
    runPythonScript(scriptPath, [destinationPath]);
}

function runPythonScript(scriptPath, args = []) {
    for (const [command, prefixArgs] of pythonCandidates) {
        if (!command) {
            continue;
        }
        const result = spawnSync(command, [...prefixArgs, scriptPath, ...args], {
            cwd: rootDir,
            stdio: "inherit",
            shell: false,
        });
        if (result.status === 0) {
            return;
        }
    }

    throw new Error(`Unable to run ${path.basename(scriptPath)} because no working Python interpreter was found.`);
}

function renderStandaloneShell(outputPath) {
    runPythonScript(path.join(rootDir, "tools", "render_standalone_shell.py"), [outputPath]);
}

function prepareStandaloneBuildInput() {
    fs.rmSync(standaloneBuildInputDir, { recursive: true, force: true });
    fs.mkdirSync(standaloneBuildInputDir, { recursive: true });
    renderStandaloneShell(standaloneHtmlInputPath);
    copyFileIntoDirectory(path.join(rootDir, "static", "css", "styles.css"), standaloneBuildInputDir);
    copyFileIntoDirectory(path.join(rootDir, "static", "favicon.svg"), standaloneBuildInputDir);
    return standaloneHtmlInputPath;
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
    const nestedStandaloneHtmlPath = path.join(outputDir, "output", ".standalone-build-input", "standalone.html");
    const standaloneHtmlPath = path.join(outputDir, "standalone.html");
    if (fs.existsSync(nestedStandaloneHtmlPath)) {
        const normalizedHtml = fs.readFileSync(nestedStandaloneHtmlPath, "utf8")
            .replaceAll("../../assets/", "./assets/");
        fs.writeFileSync(standaloneHtmlPath, normalizedHtml, "utf8");
        fs.rmSync(path.join(outputDir, "output"), { recursive: true, force: true });
    }
    if (fs.existsSync(standaloneHtmlPath)) {
        fs.copyFileSync(standaloneHtmlPath, path.join(outputDir, "index.html"));
    }
    fs.writeFileSync(path.join(outputDir, ".nojekyll"), "", "utf8");
}

function buildStandaloneFrontend(htmlEntryPath) {
    runCommand(
        process.execPath,
        [path.join(rootDir, "node_modules", "vite", "bin", "vite.js"), "build", "--mode", "standalone"],
        {
            env: {
                ...process.env,
                STANDALONE_HTML_ENTRY: htmlEntryPath,
            },
        },
    );
}

const standaloneHtmlEntry = prepareStandaloneBuildInput();
try {
    buildStandaloneFrontend(standaloneHtmlEntry);
    copyStaticAssets();
    exportBootstrapData();
    writePythonManifest();
} finally {
    fs.rmSync(standaloneBuildInputDir, { recursive: true, force: true });
}
