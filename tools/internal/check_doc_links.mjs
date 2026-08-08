import { promises as fs } from "node:fs";
import path from "node:path";
import process from "node:process";
import { Parser } from "htmlparser2";
import { marked } from "marked";
import { gfmHeadingId } from "marked-gfm-heading-id";

marked.use(gfmHeadingId());

const DEFAULT_PATHS = ["*.md", ".github", "docs"];
const MARKDOWN_EXTENSIONS = new Set([".md", ".mdx"]);
const LINK_ATTRIBUTES = new Map([
    ["a", ["href"]],
    ["area", ["href"]],
    ["audio", ["src"]],
    ["embed", ["href", "src"]],
    ["iframe", ["src"]],
    ["img", ["src"]],
    ["input", ["src"]],
    ["object", ["data"]],
    ["source", ["src"]],
    ["track", ["src"]],
    ["video", ["poster", "src"]],
]);

function parseArgs(args) {
    let root = process.cwd();
    const requestedPaths = [];
    for (let index = 0; index < args.length; index += 1) {
        if (args[index] === "--root") {
            const value = args[index + 1];
            if (!value) {
                throw new Error("--root requires a path");
            }
            root = path.resolve(value);
            index += 1;
        } else {
            requestedPaths.push(args[index]);
        }
    }
    return { root, requestedPaths };
}

async function isFile(filePath) {
    try {
        return (await fs.stat(filePath)).isFile();
    } catch {
        return false;
    }
}

async function collectMarkdownFiles(root, requestedPaths) {
    const files = new Set();

    async function addDirectory(directory) {
        let entries;
        try {
            entries = await fs.readdir(directory, { withFileTypes: true });
        } catch {
            return;
        }
        for (const entry of entries) {
            const entryPath = path.join(directory, entry.name);
            if (entry.isDirectory()) {
                await addDirectory(entryPath);
            } else if (
                entry.isFile() &&
                MARKDOWN_EXTENSIONS.has(path.extname(entry.name).toLowerCase())
            ) {
                files.add(entryPath);
            }
        }
    }

    const inputs = requestedPaths.length > 0 ? requestedPaths : DEFAULT_PATHS;
    for (const input of inputs) {
        if (input === "*.md") {
            for (const entry of await fs.readdir(root, { withFileTypes: true })) {
                if (
                    entry.isFile() &&
                    MARKDOWN_EXTENSIONS.has(path.extname(entry.name).toLowerCase())
                ) {
                    files.add(path.join(root, entry.name));
                }
            }
            continue;
        }

        const inputPath = path.resolve(root, input);
        let stats;
        try {
            stats = await fs.stat(inputPath);
        } catch {
            throw new Error(`documentation path does not exist: ${input}`);
        }
        if (stats.isDirectory()) {
            await addDirectory(inputPath);
        } else if (stats.isFile()) {
            files.add(inputPath);
        }
    }
    return [...files].sort();
}

function parseDocument(html) {
    const links = [];
    const fragments = new Set();
    const parser = new Parser({
        onopentag(tag, attributes) {
            if (attributes.id) {
                fragments.add(attributes.id);
            }
            if (tag === "a" && attributes.name) {
                fragments.add(attributes.name);
            }
            for (const attribute of LINK_ATTRIBUTES.get(tag) ?? []) {
                if (attributes[attribute]) {
                    links.push(attributes[attribute]);
                }
            }
        },
    });
    parser.write(html);
    parser.end();
    return { links, fragments };
}

async function renderDocument(filePath) {
    const source = await fs.readFile(filePath, "utf8");
    if (MARKDOWN_EXTENSIONS.has(path.extname(filePath).toLowerCase())) {
        return parseDocument(await marked.parse(source, { gfm: true }));
    }
    return parseDocument(source);
}

function splitLink(link) {
    const hashIndex = link.indexOf("#");
    const beforeHash = hashIndex === -1 ? link : link.slice(0, hashIndex);
    const queryIndex = beforeHash.indexOf("?");
    return {
        pathname: queryIndex === -1 ? beforeHash : beforeHash.slice(0, queryIndex),
        fragment: hashIndex === -1 ? "" : link.slice(hashIndex + 1),
    };
}

function isExternalOrSpecial(link) {
    return link.startsWith("//") || /^[a-z][a-z\d+.-]*:/i.test(link);
}

function decodeLinkPart(value) {
    try {
        return decodeURIComponent(value);
    } catch {
        return null;
    }
}

async function checkLinks(root, files) {
    const rendered = new Map();
    const failures = [];
    let linkCount = 0;

    async function getRendered(filePath) {
        if (!rendered.has(filePath)) {
            rendered.set(filePath, await renderDocument(filePath));
        }
        return rendered.get(filePath);
    }

    for (const file of files) {
        const { links } = await getRendered(file);
        for (const rawLink of links) {
            const link = rawLink.trim();
            if (!link || isExternalOrSpecial(link)) {
                continue;
            }
            linkCount += 1;
            const { pathname, fragment } = splitLink(link);
            const decodedPath = decodeLinkPart(pathname);
            const decodedFragment = decodeLinkPart(fragment);
            if (decodedPath === null || decodedFragment === null) {
                failures.push(`${path.relative(root, file)}: invalid URL encoding in ${rawLink}`);
                continue;
            }

            const target = decodedPath
                ? path.resolve(
                      decodedPath.startsWith("/") ? root : path.dirname(file),
                      decodedPath.replace(/^\/+/, ""),
                  )
                : file;
            const relativeTarget = path.relative(root, target);
            if (relativeTarget.startsWith("..") || path.isAbsolute(relativeTarget)) {
                failures.push(`${path.relative(root, file)}: ${rawLink} escapes the repository`);
                continue;
            }

            let targetStats;
            try {
                targetStats = await fs.stat(target);
            } catch {
                failures.push(`${path.relative(root, file)}: ${rawLink} points to a missing path`);
                continue;
            }

            if (decodedFragment && targetStats.isFile()) {
                if (!(await isFile(target))) {
                    failures.push(`${path.relative(root, file)}: ${rawLink} is not a file`);
                    continue;
                }
                const { fragments } = await getRendered(target);
                if (!fragments.has(decodedFragment)) {
                    failures.push(
                        `${path.relative(root, file)}: ${rawLink} points to a missing anchor`,
                    );
                }
            }
        }
    }
    return { failures, linkCount };
}

async function main() {
    const { root, requestedPaths } = parseArgs(process.argv.slice(2));
    const files = await collectMarkdownFiles(root, requestedPaths);
    const { failures, linkCount } = await checkLinks(root, files);
    if (failures.length > 0) {
        for (const failure of failures) {
            console.error(`BROKEN ${failure}`);
        }
        console.error(`Documentation link check failed with ${failures.length} broken link(s).`);
        process.exitCode = 1;
        return;
    }
    console.log(`Checked ${linkCount} local link(s) in ${files.length} documentation file(s).`);
}

await main();
