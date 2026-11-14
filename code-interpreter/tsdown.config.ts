import { defineConfig } from 'tsdown'

// Same output as the upstream package: ESM and CJS builds with declarations and source maps.
// The `boxfab` SDK stays an external dependency, as `e2b` is for @e2b/code-interpreter.
export default defineConfig({
  entry: { index: './src/index.ts' },
  target: 'es2017',
  format: ['esm', 'cjs'],
  fixedExtension: false,
  sourcemap: true,
  dts: true,
  clean: true,
})
