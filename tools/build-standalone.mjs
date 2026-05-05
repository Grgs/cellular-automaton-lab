import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";

const dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(dirname, "..");
const outputDir = path.join(rootDir, "output", "standalone");
const standaloneBuildInputDir = path.join(rootDir, "output", ".standalone-build-input");
const standaloneHtmlInputPath = path.join(standaloneBuildInputDir, "standalone.html");
const pythonCandidates =
    process.platform === "win32"
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

function readCommandOutput(command, args, options = {}) {
    const result = spawnSync(command, args, {
        cwd: rootDir,
        stdio: ["ignore", "pipe", "ignore"],
        shell: false,
        encoding: "utf8",
        ...options,
    });
    if (result.status !== 0) {
        return null;
    }
    return String(result.stdout || "").trim() || null;
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

function collectSourceFingerprintPaths() {
    const relativePaths = collectFiles(path.join(rootDir, "frontend"), () => true).map(
        (absolutePath) => path.relative(rootDir, absolutePath).replace(/\\/g, "/"),
    );
    for (const relativePath of [
        "tools/build-standalone.mjs",
        "package.json",
        "package-lock.json",
    ]) {
        const absolutePath = path.join(rootDir, relativePath);
        if (fs.existsSync(absolutePath)) {
            relativePaths.push(relativePath);
        }
    }
    return [...new Set(relativePaths)].sort();
}

function computeSourceFingerprint(relativePaths) {
    const hash = createHash("sha256");
    for (const relativePath of relativePaths) {
        hash.update(relativePath, "utf8");
        hash.update("\0", "utf8");
        hash.update(fs.readFileSync(path.join(rootDir, relativePath)));
        hash.update("\0", "utf8");
    }
    return hash.digest("hex");
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

    throw new Error(
        `Unable to run ${path.basename(scriptPath)} because no working Python interpreter was found.`,
    );
}

function renderStandaloneShell(outputPath) {
    runPythonScript(path.join(rootDir, "tools", "render_standalone_shell.py"), [outputPath]);
}

function prepareStandaloneBuildInput() {
    fs.rmSync(standaloneBuildInputDir, { recursive: true, force: true });
    fs.mkdirSync(standaloneBuildInputDir, { recursive: true });
    renderStandaloneShell(standaloneHtmlInputPath);
    copyFileIntoDirectory(
        path.join(rootDir, "static", "css", "styles.css"),
        standaloneBuildInputDir,
    );
    copyFileIntoDirectory(path.join(rootDir, "static", "favicon.svg"), standaloneBuildInputDir);
    return standaloneHtmlInputPath;
}

function writePythonBundle() {
    const sourceRoots = [path.join(rootDir, "backend"), path.join(rootDir, "config")];
    const files = sourceRoots
        .flatMap((sourceRoot) =>
            collectFiles(
                sourceRoot,
                (absolutePath) => absolutePath.endsWith(".py") || absolutePath.endsWith(".json"),
            ),
        )
        .sort();

    const bundleEntries = files.map((absolutePath) => {
        const relativePath = path.relative(rootDir, absolutePath).replace(/\\/g, "/");
        return {
            target_path: `/app/${relativePath}`,
            contents: fs.readFileSync(absolutePath, "utf8"),
        };
    });

    fs.rmSync(path.join(outputDir, "py-src"), { recursive: true, force: true });
    fs.writeFileSync(
        path.join(outputDir, "standalone-python-bundle.json"),
        JSON.stringify({ version: 1, files: bundleEntries }),
        "utf8",
    );
}

function copyStaticAssets() {
    const nestedStandaloneHtmlPath = path.join(
        outputDir,
        "output",
        ".standalone-build-input",
        "standalone.html",
    );
    const standaloneHtmlPath = path.join(outputDir, "standalone.html");
    if (fs.existsSync(nestedStandaloneHtmlPath)) {
        const normalizedHtml = fs
            .readFileSync(nestedStandaloneHtmlPath, "utf8")
            .replaceAll("../../assets/", "./assets/");
        fs.writeFileSync(standaloneHtmlPath, normalizedHtml, "utf8");
        fs.rmSync(path.join(outputDir, "output"), { recursive: true, force: true });
    }
    if (fs.existsSync(standaloneHtmlPath)) {
        fs.copyFileSync(standaloneHtmlPath, path.join(outputDir, "index.html"));
    }
    fs.writeFileSync(path.join(outputDir, ".nojekyll"), "", "utf8");
}

function writeBuildManifest() {
    const sourceFiles = collectSourceFingerprintPaths();
    const manifest = {
        builtAt: new Date().toISOString(),
        gitHead: readCommandOutput("git", ["rev-parse", "HEAD"]),
        gitDirty: (() => {
            const status = readCommandOutput("git", ["status", "--porcelain"]);
            return status === null ? null : status.length > 0;
        })(),
        sourceFingerprint: computeSourceFingerprint(sourceFiles),
        sourceFiles,
    };
    fs.writeFileSync(
        path.join(outputDir, "build-manifest.json"),
        JSON.stringify(manifest, null, 2),
        "utf8",
    );
}

function buildStandaloneFrontend(htmlEntryPath) {
    runCommand(
        process.execPath,
        [
            path.join(rootDir, "node_modules", "vite", "bin", "vite.js"),
            "build",
            "--mode",
            "standalone",
        ],
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
    writePythonBundle();
    writeBuildManifest();
} finally {
    fs.rmSync(standaloneBuildInputDir, { recursive: true, force: true });
}
