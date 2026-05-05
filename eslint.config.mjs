import js from "@eslint/js";
import eslintConfigPrettier from "eslint-config-prettier";
import tseslint from "typescript-eslint";

export default tseslint.config(
    {
        ignores: ["node_modules/**", "output/**", "static/dist/**"],
    },
    js.configs.recommended,
    ...tseslint.configs.recommended,
    {
        files: ["frontend/**/*.ts", "vite.config.ts"],
        rules: {
            "@typescript-eslint/no-unused-vars": [
                "error",
                {
                    argsIgnorePattern: "^_",
                    caughtErrorsIgnorePattern: "^_",
                    varsIgnorePattern: "^_",
                },
            ],
            "no-console": "off",
        },
    },
    eslintConfigPrettier,
);
