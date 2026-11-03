import { defineConfig } from 'tsdown'

// Same output as the upstream SDK: ESM and CJS builds with declarations and source maps.
export default defineConfig({
  entry: { index: './src/index.ts' },
  target: 'es2017',
  format: ['esm', 'cjs'],
  fixedExtension: false,
  sourcemap: true,
  dts: true,
  clean: true,
  // ESM-only package inlined into both output formats: the engines range includes Node versions
  // that cannot require() ESM from the CJS build.
  noExternal: ['error-stack-parser-es'],
})
