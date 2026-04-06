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
const defaultModule = "tests.e2e.test_playwright_all";
const envOverrides = {};
const requestedModules = [];
let skipStandaloneBuild = false;
for (let index = 2; index < process.argv.length; index += 1) {
    const token = process.argv[index];
    if (token === "--skip-standalone-build") {
        skipStandaloneBuild = true;
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
    requestedModules.push(token);
}
const modules = requestedModules.length > 0 ? requestedModules : [defaultModule];
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
    const entries = fs.readdirSync(playwrightCache, { withFileTypes: true })
        .filter((entry) => entry.isDirectory() && entry.name.startsWith("chromium_headless_shell-"))
        .map((entry) => path.join(playwrightCache, entry.name, "chrome-headless-shell-linux64", "chrome-headless-shell"))
        .filter((candidate) => fs.existsSync(candidate))
        .sort();
    return entries.at(-1) ?? null;
}

function chooseAlsaPackage() {
    const preferred = ["libasound2t64", "libasound2"];
    for (const packageName of preferred) {
        const result = runCommandCapture("apt-cache", ["policy", packageName]);
        if (result.status === 0 && /Candidate:\s+(?!\(none\))/u.test(result.stdout || "")) {
            return packageName;
        }
    }
    throw new Error("Unable to resolve an ALSA runtime package for Playwright.");
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

    const packages = ["libnspr4", "libnss3", chooseAlsaPackage()];
    fs.mkdirSync(playwrightLibDebDir, { recursive: true });
    fs.mkdirSync(playwrightLibExtractRoot, { recursive: true });

    runCommand("apt", ["download", ...packages], {
        cwd: playwrightLibDebDir,
        stdio: "inherit",
    });

    const debFiles = fs.readdirSync(playwrightLibDebDir)
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
        throw new Error(`Playwright browser is still missing shared libraries: ${remainingMissing.join(", ")}`);
    }
    return nextEnv;
}

function shouldBuildStandaloneOutputs() {
    return modules.some((moduleName) => (
        moduleName.includes("standalone")
        || moduleName.endsWith("test_playwright_all")
    ));
}

function runPythonModules(env) {
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
        throw new Error(`Playwright tests failed with ${command} ${prefixArgs.join(" ")}`.trim());
    }
    throw new Error("Unable to run Playwright tests because no working Python interpreter was found.");
}

const baseEnv = { ...process.env, ...envOverrides };
const runtimeEnv = ensureLinuxPlaywrightRuntime(baseEnv);
if (!skipStandaloneBuild && shouldBuildStandaloneOutputs()) {
    runCommand(resolveNpmExecutable(), ["run", "build:frontend:standalone"], {
        env: runtimeEnv,
        stdio: "inherit",
    });
}
runPythonModules(runtimeEnv);
