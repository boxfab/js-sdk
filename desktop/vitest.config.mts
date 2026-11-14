import { config } from 'dotenv'
import { defineConfig } from 'vitest/config'

// Projects:
//   unit-offline  upstream tests that need no network or key (CI): the client binding and the
//                 desktop readiness checks
//   live          tests that create desktop sandboxes: need BOXFAB_API_KEY and a desktop template
//                 (BOXFAB_DESKTOP_TEMPLATE, default `desktop`)
const env = config({ quiet: true })
const shared = {
  globals: false,
  environment: 'node' as const,
  env: { ...(process.env as Record<string, string>), ...env.parsed },
  setupFiles: ['tests/boxfab-env.setup.ts'],
}

export default defineConfig({
  test: {
    projects: [
      {
        test: {
          ...shared,
          name: 'unit-offline',
          include: ['tests/client.test.ts', 'tests/readiness.test.ts'],
          testTimeout: 30_000,
        },
      },
      {
        test: {
          ...shared,
          name: 'live',
          include: ['tests/apps.test.ts', 'tests/mouse.test.ts', 'tests/screen.test.ts'],
          testTimeout: 180_000,
        },
      },
    ],
  },
})
