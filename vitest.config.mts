import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { config } from 'dotenv'
import { defineConfig } from 'vitest/config'

// Projects:
//   unit-offline     upstream unit tests that need no network or key (CI)
//   connectionConfig environment/config resolution (CI)
//   live             tests that create sandboxes, templates or volumes: need BOXFAB_API_KEY
// A test file is "live" when it uses the shared fixtures in tests/setup.ts (sandboxTest,
// buildTemplate, ...) or is listed in LIVE_EXTRA.
const LIVE_EXTRA = ['tests/template/backgroundBuild.test.ts', 'tests/template/exists.test.ts']
const SETUP_IMPORT = /from '(\.\.\/)+setup(\.js)?'|from '\.\/setup(\.js)?'/

function testFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const p = join(dir, name)
    if (statSync(p).isDirectory()) return testFiles(p)
    return p.endsWith('.test.ts') ? [p] : []
  })
}
const all = testFiles('tests')
const live = all.filter((f) => LIVE_EXTRA.includes(f) || SETUP_IMPORT.test(readFileSync(f, 'utf8')))
const offline = all.filter(
  (f) => !live.includes(f) && f !== 'tests/connectionConfig.test.ts' && !f.startsWith('tests/template/')
)
const offlineTemplate = all.filter((f) => f.startsWith('tests/template/') && !live.includes(f))

const env = config({ quiet: true })
const maxWorkers = process.env.BOXFAB_TEST_MAX_WORKERS
  ? Number(process.env.BOXFAB_TEST_MAX_WORKERS)
  : undefined
const shared = {
  globals: false,
  environment: 'node' as const,
  maxWorkers,
  deps: { interopDefault: true },
  env: { ...(process.env as Record<string, string>), ...env.parsed },
}

export default defineConfig({
  test: {
    maxWorkers,
    projects: [
      {
        test: {
          ...shared,
          name: 'unit-offline',
          include: [...offline, ...offlineTemplate],
          // Several suites patch global fetch via msw and rely on module mocks; they need isolation.
          isolate: true,
          testTimeout: 30_000,
          setupFiles: ['tests/boxfab-env.setup.ts', 'tests/globalFetchFallback.setup.ts'],
        },
      },
      {
        test: {
          ...shared,
          name: 'connectionConfig',
          include: ['tests/connectionConfig.test.ts'],
          isolate: true,
          testTimeout: 10_000,
          setupFiles: ['tests/boxfab-env.setup.ts'],
        },
      },
      {
        test: {
          ...shared,
          name: 'live',
          include: live,
          isolate: true,
          testTimeout: 180_000,
          setupFiles: ['tests/boxfab-env.setup.ts', 'tests/globalFetchFallback.setup.ts'],
        },
      },
    ],
  },
})
