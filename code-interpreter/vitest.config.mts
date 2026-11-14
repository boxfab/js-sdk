import { config } from 'dotenv'
import { defineConfig } from 'vitest/config'

// Projects:
//   unit-offline  upstream tests that need no network or key (CI): message parsing, helpers and
//                 the Jupyter URL
//   live          tests that create sandboxes: need BOXFAB_API_KEY and the code interpreter
//                 template (BOXFAB_TESTS_TEMPLATE, default `code-interpreter-v1`)
const env = config({ quiet: true })
const shared = {
  globals: false,
  environment: 'node' as const,
  env: { ...(process.env as Record<string, string>), ...env.parsed },
  setupFiles: ['tests/boxfab-env.setup.ts'],
}
const offline = ['tests/messaging.test.ts', 'tests/sandboxUrl.test.ts', 'tests/utils.test.ts']

export default defineConfig({
  test: {
    projects: [
      {
        test: { ...shared, name: 'unit-offline', include: offline, testTimeout: 30_000 },
      },
      {
        test: {
          ...shared,
          name: 'live',
          include: ['tests/**/*.test.ts'],
          exclude: offline,
          testTimeout: 90_000,
        },
      },
    ],
  },
})
