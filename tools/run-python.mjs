import path from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(dirname, "..");
const args = process.argv.slice(2);
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

if (args.length === 0) {
    throw new Error("Expected a Python script path or module invocation.");
}

for (const [command, prefixArgs] of pythonCandidates) {
    if (!command) {
        continue;
    }
    const result = spawnSync(command, [...prefixArgs, ...args], {
        cwd: rootDir,
        stdio: "inherit",
        shell: false,
        env: process.env,
    });
    if (result.status === 0) {
        process.exit(0);
    }
    if (result.error) {
        continue;
    }
    process.exit(result.status ?? 1);
}

throw new Error("Unable to find a working Python interpreter.");
