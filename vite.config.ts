import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

const dirname = path.dirname(fileURLToPath(import.meta.url));

function resolveFrontendJsImports() {
    return {
        name: "resolve-frontend-js-imports",
        enforce: "pre" as const,
        resolveId(source: string, importer?: string) {
            if (!importer || !source.startsWith(".") || !source.endsWith(".js")) {
                return null;
            }

            const importerPath = importer.split("?")[0];
            const resolvedJsPath = path.resolve(path.dirname(importerPath), source);
            if (fs.existsSync(resolvedJsPath)) {
                return null;
            }

            const resolvedTsPath = resolvedJsPath.slice(0, -3) + ".ts";
            if (fs.existsSync(resolvedTsPath)) {
                return resolvedTsPath;
            }

            const resolvedDtsPath = resolvedJsPath.slice(0, -3) + ".d.ts";
            if (fs.existsSync(resolvedDtsPath)) {
                return resolvedDtsPath;
            }

            return null;
        },
    };
}

export default defineConfig(({ mode }) => {
    const isStandalone = mode === "standalone";
    const standaloneHtmlEntry = process.env.STANDALONE_HTML_ENTRY
        ? path.resolve(process.env.STANDALONE_HTML_ENTRY)
        : path.resolve(dirname, "output", ".standalone-build-input", "standalone.html");
    return {
        base: isStandalone ? "./" : "/static/dist/",
        plugins: [resolveFrontendJsImports()],
        build: {
            outDir: isStandalone ? "output/standalone" : "static/dist",
            emptyOutDir: true,
            ...(isStandalone ? {} : { manifest: "manifest.json" }),
            rollupOptions: {
                input: isStandalone
                    ? {
                          standalone: standaloneHtmlEntry,
                      }
                    : {
                          app: path.resolve(dirname, "frontend/server-entry.ts"),
                      },
            },
        },
        test: {
            environment: "jsdom",
            include: ["frontend/**/*.test.ts"],
        },
    };
});
