import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(dirname, "..", "..");
const vitestPath = path.join(rootDir, "node_modules", "vitest", "vitest.mjs");
const environment = { ...process.env };
const isWsl =
    process.platform === "linux" && Boolean(environment.WSL_DISTRO_NAME || environment.WSL_INTEROP);
const hasWindowsTemp = [environment.TMPDIR, environment.TEMP, environment.TMP].some((value) =>
    value?.startsWith("/mnt/"),
);

if (isWsl && hasWindowsTemp) {
    environment.TMPDIR = "/tmp";
    environment.TEMP = "/tmp";
    environment.TMP = "/tmp";
}

const result = spawnSync(process.execPath, [vitestPath, ...process.argv.slice(2)], {
    cwd: rootDir,
    stdio: "inherit",
    shell: false,
    env: environment,
});

if (result.error) {
    throw result.error;
}
process.exit(result.status ?? 1);
