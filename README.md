# BoxFab JavaScript SDK

Secure cloud sandboxes for AI agents and code execution, from JavaScript and TypeScript.

```bash
npm install boxfab@alpha
export BOXFAB_API_KEY=e2b_...
```

```ts
import { Sandbox } from 'boxfab'

const sandbox = await Sandbox.create()        // the "base" template
const result = await sandbox.commands.run('echo Hello from $(hostname)')
console.log(result.stdout)

await sandbox.files.write('/home/user/hello.txt', 'Hello, BoxFab!')
console.log(await sandbox.files.read('/home/user/hello.txt'))

await sandbox.kill()
```

Requires Node.js 22.19 or newer.

## Configuration

| Variable | Meaning | Default |
|---|---|---|
| `BOXFAB_API_KEY` | your team's API key | none |
| `BOXFAB_DOMAIN` | the BoxFab domain | `boxfab.io` |

Both can also be passed as options, for example `Sandbox.create({ apiKey })`. A client object
binds its own configuration: `new BoxFab({ apiKey }).Sandbox.create()`.

Documentation: [boxfab.dev/docs](https://boxfab.dev/docs). Dashboard:
[dashboard.boxfab.io](https://dashboard.boxfab.io).

## License

MIT. Derived from an open-source MIT-licensed SDK; see `LICENSE`, `LICENSE-E2B` and `UPSTREAM.md`.
