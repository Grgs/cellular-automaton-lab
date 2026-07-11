// Vite asset-query imports. `?inline` resolves to the file's content as a
// string (CSS is run through Vite's minifier at build time) without emitting
// a separate asset. This file must stay free of top-level imports/exports so
// the wildcard declaration remains ambient.
declare module "*.css?inline" {
    const css: string;
    export default css;
}
