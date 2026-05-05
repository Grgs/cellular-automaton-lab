import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(dirname, "..");
const playwrightLibRoot = path.join(rootDir, "output", "playwright-linux-libs");
const playwrightLibDebDir = path.join(playwrightLibRoot, "debs");
const playwrightLibExtractRoot = path.join(playwrightLibRoot, "root");
const defaultSuiteName = "all";
const manifestToolPath = path.join("tools", "print_playwright_suite_manifest.py");
const standaloneBuildStatusToolPath = path.join("tools", "print_standalone_build_status.py");
const envOverrides = {};
let listSuites = false;
let skipStandaloneBuild = false;
let forceStandaloneBuild = false;
let suiteName = defaultSuiteName;

for (let index = 2; index < process.argv.length; index += 1) {
    const token = process.argv[index];
    if (token === "--suite") {
        const value = process.argv[index + 1];
        if (!value) {
            throw new Error("Expected a suite name after --suite.");
        }
        suiteName = value;
        index += 1;
        continue;
    }
    if (token === "--list-suites") {
        listSuites = true;
        continue;
    }
    if (token === "--skip-standalone-build") {
        skipStandaloneBuild = true;
        continue;
    }
    if (token === "--force-standalone-build") {
        forceStandaloneBuild = true;
        continue;
    }
    if (token === "--env") {
        const assignment = process.argv[index + 1];
        if (!assignment || !assignment.includes("=")) {
            throw new Error("Expected KEY=VALUE after --env");
        }
        const [key, ...valueParts] = assignment.split("=");
        envOverrides[key] = valueParts.join("=");
        index += 1;
        continue;
    }
    throw new Error(
        `Unknown argument '${token}'. Use --suite <name>, --list-suites, --skip-standalone-build, --force-standalone-build, or --env KEY=VALUE.`,
    );
}

if (skipStandaloneBuild && forceStandaloneBuild) {
    throw new Error(
        "--skip-standalone-build and --force-standalone-build cannot be used together.",
    );
}

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
        encoding: "utf8",
        shell: false,
        ...options,
    });
    if (result.status !== 0) {
        const stdout = result.stdout ? `\nstdout:\n${result.stdout}` : "";
        const stderr = result.stderr ? `\nstderr:\n${result.stderr}` : "";
        throw new Error(`Command failed: ${command} ${args.join(" ")}${stdout}${stderr}`);
    }
    return result;
}

function runCommandCapture(command, args, options = {}) {
    return spawnSync(command, args, {
        cwd: rootDir,
        encoding: "utf8",
        shell: false,
        ...options,
    });
}

function resolveNpmExecutable() {
    return process.platform === "win32" ? "npm.cmd" : "npm";
}

function findChromiumHeadlessShell() {
    const playwrightCache = path.join(os.homedir(), ".cache", "ms-playwright");
    if (!fs.existsSync(playwrightCache)) {
        return null;
    }
    const entries = fs
        .readdirSync(playwrightCache, { withFileTypes: true })
        .filter((entry) => entry.isDirectory() && entry.name.startsWith("chromium_headless_shell-"))
        .map((entry) =>
            path.join(
                playwrightCache,
                entry.name,
                "chrome-headless-shell-linux64",
                "chrome-headless-shell",
            ),
        )
        .filter((candidate) => fs.existsSync(candidate))
        .sort();
    return entries.at(-1) ?? null;
}

function commandExists(command) {
    const result = spawnSync("bash", ["-lc", `command -v ${command}`], {
        cwd: rootDir,
        encoding: "utf8",
        shell: false,
    });
    return result.status === 0;
}

function linuxRepairError({
    missingLibraries,
    packages = [],
    missingTools = [],
    extraDetail = "",
}) {
    const lines = [
        "Playwright browser is missing shared libraries on Linux.",
        `Missing libraries: ${missingLibraries.join(", ")}`,
    ];
    if (packages.length > 0) {
        lines.push(`Attempted repair packages: ${packages.join(", ")}`);
    }
    if (missingTools.length > 0) {
        lines.push(`Missing repair tools: ${missingTools.join(", ")}`);
    }
    lines.push(
        "The local self-repair path currently assumes Debian/Ubuntu-style tooling (`apt`, `apt-cache`, and `dpkg-deb`).",
    );
    lines.push(
        "Install the required runtime libraries manually or rerun in an environment with those packaging tools available.",
    );
    lines.push(
        "Preferred browser entrypoints: `npm run test:e2e:playwright`, `npm run test:e2e:playwright:server`, or `npm run test:e2e:playwright:standalone`.",
    );
    lines.push("Troubleshooting reference: docs/TESTING.md (Playwright troubleshooting section).");
    if (extraDetail) {
        lines.push(extraDetail.trim());
    }
    return new Error(lines.join("\n"));
}

function chooseAlsaPackage(missingLibraries) {
    if (!commandExists("apt-cache")) {
        throw linuxRepairError({
            missingLibraries,
            missingTools: ["apt-cache"],
        });
    }
    const preferred = ["libasound2t64", "libasound2"];
    for (const packageName of preferred) {
        const result = runCommandCapture("apt-cache", ["policy", packageName]);
        if (result.status === 0 && /Candidate:\s+(?!\(none\))/u.test(result.stdout || "")) {
            return packageName;
        }
    }
    throw linuxRepairError({
        missingLibraries,
        packages: preferred,
        extraDetail:
            "Unable to resolve an installable ALSA runtime package with `apt-cache policy`.",
    });
}

function lddMissingLibraries(binaryPath, env) {
    const result = runCommandCapture("ldd", [binaryPath], { env });
    if (result.status !== 0) {
        throw new Error(`ldd failed for ${binaryPath}:\n${result.stderr || result.stdout || ""}`);
    }
    return (result.stdout || "")
        .split("\n")
        .map((line) => line.trim())
        .filter((line) => line.endsWith("=> not found"))
        .map((line) => line.split(" => ")[0] || line);
}

function ensureLinuxPlaywrightRuntime(env) {
    if (process.platform !== "linux") {
        return env;
    }
    const browserBinary = findChromiumHeadlessShell();
    if (!browserBinary) {
        return env;
    }

    const localLibDir = path.join(playwrightLibExtractRoot, "usr", "lib", "x86_64-linux-gnu");
    if (fs.existsSync(localLibDir)) {
        const cachedEnv = {
            ...env,
            LD_LIBRARY_PATH: env.LD_LIBRARY_PATH
                ? `${localLibDir}:${env.LD_LIBRARY_PATH}`
                : localLibDir,
        };
        if (lddMissingLibraries(browserBinary, cachedEnv).length === 0) {
            return cachedEnv;
        }
    }

    const currentMissing = lddMissingLibraries(browserBinary, env);
    if (currentMissing.length === 0) {
        return env;
    }

    const missingTools = ["apt", "apt-cache", "dpkg-deb"].filter(
        (command) => !commandExists(command),
    );
    if (missingTools.length > 0) {
        throw linuxRepairError({
            missingLibraries: currentMissing,
            missingTools,
        });
    }

    const packages = ["libnspr4", "libnss3", chooseAlsaPackage(currentMissing)];
    fs.mkdirSync(playwrightLibDebDir, { recursive: true });
    fs.mkdirSync(playwrightLibExtractRoot, { recursive: true });

    const downloadResult = runCommandCapture("apt", ["download", ...packages], {
        cwd: playwrightLibDebDir,
        stdio: "inherit",
    });
    if (downloadResult.status !== 0) {
        throw linuxRepairError({
            missingLibraries: currentMissing,
            packages,
            extraDetail:
                "Automatic browser-library repair failed while running `apt download`.\n" +
                (downloadResult.stderr ||
                    downloadResult.stdout ||
                    "The `apt download` command failed."),
        });
    }

    const debFiles = fs
        .readdirSync(playwrightLibDebDir)
        .filter((filename) => filename.endsWith(".deb"))
        .map((filename) => path.join(playwrightLibDebDir, filename))
        .sort();
    for (const debFile of debFiles) {
        runCommand("dpkg-deb", ["-x", debFile, playwrightLibExtractRoot], { stdio: "inherit" });
    }

    const nextEnv = {
        ...env,
        LD_LIBRARY_PATH: env.LD_LIBRARY_PATH
            ? `${localLibDir}:${env.LD_LIBRARY_PATH}`
            : localLibDir,
    };
    const remainingMissing = lddMissingLibraries(browserBinary, nextEnv);
    if (remainingMissing.length > 0) {
        throw linuxRepairError({
            missingLibraries: remainingMissing,
            packages,
            extraDetail:
                "Playwright browser is still missing shared libraries after the local repair attempt.",
        });
    }
    return nextEnv;
}

function runPythonCapture(args, options = {}) {
    let commandFailure = null;
    for (const [command, prefixArgs] of pythonCandidates) {
        if (!command) {
            continue;
        }
        const result = spawnSync(command, [...prefixArgs, ...args], {
            cwd: rootDir,
            encoding: "utf8",
            shell: false,
            ...options,
        });
        if (result.status === 0) {
            return result;
        }
        if (result.error) {
            continue;
        }
        commandFailure = { command, prefixArgs, result };
        break;
    }
    if (commandFailure !== null) {
        const { command, prefixArgs, result } = commandFailure;
        const stdout = result.stdout ? `\nstdout:\n${result.stdout}` : "";
        const stderr = result.stderr ? `\nstderr:\n${result.stderr}` : "";
        throw new Error(
            `Python command failed: ${command} ${prefixArgs.join(" ")} ${args.join(" ")}`.trim() +
                stdout +
                stderr,
        );
    }
    throw new Error("Unable to find a working Python interpreter.");
}

function runPythonModules(modules, env) {
    let commandFailure = null;
    for (const [command, prefixArgs] of pythonCandidates) {
        if (!command) {
            continue;
        }
        const result = spawnSync(command, [...prefixArgs, "-m", "unittest", "-q", ...modules], {
            cwd: rootDir,
            stdio: "inherit",
            shell: false,
            env,
        });
        if (result.status === 0) {
            return;
        }
        if (result.error) {
            continue;
        }
        commandFailure = { command, prefixArgs };
        break;
    }
    if (commandFailure !== null) {
        const { command, prefixArgs } = commandFailure;
        throw new Error(`Playwright tests failed with ${command} ${prefixArgs.join(" ")}`.trim());
    }
    throw new Error(
        "Unable to run Playwright tests because no working Python interpreter was found.",
    );
}

function loadSuiteManifest() {
    const result = runPythonCapture([manifestToolPath]);
    const payload = JSON.parse(result.stdout || "[]");
    if (!Array.isArray(payload)) {
        throw new Error("Playwright suite manifest did not produce a JSON array.");
    }
    return payload;
}

function loadStandaloneBuildStatus() {
    const result = runPythonCapture([standaloneBuildStatusToolPath]);
    const payload = JSON.parse(result.stdout || "{}");
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
        throw new Error("Standalone build status tool did not produce a JSON object.");
    }
    return payload;
}

const suiteManifest = loadSuiteManifest();
if (listSuites) {
    console.log(JSON.stringify(suiteManifest, null, 2));
    process.exit(0);
}

const selectedSuite = suiteManifest.find((entry) => entry.name === suiteName);
if (!selectedSuite) {
    const availableSuites = suiteManifest.map((entry) => entry.name).join(", ");
    throw new Error(
        `Unknown Playwright suite '${suiteName}'. Available suites: ${availableSuites}`,
    );
}

const baseEnv = {
    ...process.env,
    ...(selectedSuite.env || {}),
    ...envOverrides,
};
const runtimeEnv = ensureLinuxPlaywrightRuntime(baseEnv);
if (!skipStandaloneBuild && selectedSuite.requires_standalone_build) {
    const buildStatus = loadStandaloneBuildStatus();
    if (forceStandaloneBuild || buildStatus.buildCurrent !== true) {
        const reason = forceStandaloneBuild
            ? "forced rebuild requested"
            : String(buildStatus.reason || "standalone build is missing or stale");
        console.error(
            `Preparing standalone build for Playwright suite '${selectedSuite.name}': ${reason}.`,
        );
        runCommand(resolveNpmExecutable(), ["run", "build:frontend:standalone"], {
            env: runtimeEnv,
            stdio: "inherit",
        });
    } else {
        console.error(
            `Reusing current standalone build for Playwright suite '${selectedSuite.name}'.`,
        );
    }
} else if (skipStandaloneBuild && selectedSuite.requires_standalone_build) {
    const buildStatus = loadStandaloneBuildStatus();
    if (buildStatus.buildCurrent !== true) {
        console.error(
            `Skipping standalone rebuild for Playwright suite '${selectedSuite.name}' even though the build is not current: ${String(buildStatus.reason || "unknown reason")}.`,
        );
    }
}
runPythonModules([selectedSuite.module], runtimeEnv);
