import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(dirname, "..");
const SOURCE_ROOTS = [
    path.join(rootDir, "frontend"),
    path.join(rootDir, "static", "css"),
    path.join(rootDir, "templates"),
    path.join(rootDir, "vite.config.ts"),
];
const SOURCE_EXTENSIONS = new Set([".css", ".html", ".js", ".mjs", ".ts"]);
const ignoredDirectoryNames = new Set(["node_modules", "dist"]);

async function listSourceFiles(entryPath) {
    const entry = await fs.stat(entryPath);
    if (entry.isFile()) {
        return [entryPath];
    }
    const children = await fs.readdir(entryPath, { withFileTypes: true });
    const nested = await Promise.all(children.map(async (child) => {
        if (child.isDirectory()) {
            if (ignoredDirectoryNames.has(child.name)) {
                return [];
            }
            return listSourceFiles(path.join(entryPath, child.name));
        }
        if (!child.isFile()) {
            return [];
        }
        const childPath = path.join(entryPath, child.name);
        return SOURCE_EXTENSIONS.has(path.extname(child.name)) ? [childPath] : [];
    }));
    return nested.flat();
}

function collectFormattingIssues(filePath, content) {
    const issues = [];
    if (!content.endsWith("\n")) {
        issues.push("missing final newline");
    }
    const lines = content.split("\n");
    for (let index = 0; index < lines.length; index += 1) {
        const line = lines[index].replace(/\r$/, "");
        if (/[ \t]+$/.test(line)) {
            issues.push(`line ${index + 1}: trailing whitespace`);
        }
        if (/^\t+/.test(line)) {
            issues.push(`line ${index + 1}: leading tabs are not allowed`);
        }
    }
    return issues;
}

async function main() {
    const files = (await Promise.all(SOURCE_ROOTS.map((entryPath) => listSourceFiles(entryPath)))).flat().sort();
    const failures = [];
    for (const filePath of files) {
        const content = await fs.readFile(filePath, "utf8");
        const issues = collectFormattingIssues(filePath, content);
        for (const issue of issues) {
            failures.push(`${path.relative(rootDir, filePath)}: ${issue}`);
        }
    }
    if (failures.length > 0) {
        console.error("Frontend formatting check failed:");
        for (const failure of failures) {
            console.error(`- ${failure}`);
        }
        process.exitCode = 1;
        return;
    }
    console.log(`Frontend formatting check passed for ${files.length} files.`);
}

await main();
