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

## Desktop sandboxes

`@boxfab/desktop` (in [desktop/](desktop)) adds a virtual Linux desktop for computer-use agents:
mouse and keyboard control, screenshots, application windows, and a live stream of the screen.

```bash
npm install @boxfab/desktop
```

See [desktop/README.md](desktop/README.md).

## Under the hood

BoxFab sandboxes are [Firecracker](https://firecracker-microvm.github.io/) microVMs, run on the
open-source [E2B](https://github.com/e2b-dev/infra) sandbox infrastructure. This SDK is derived from
the open-source E2B JavaScript SDK; [UPSTREAM.md](UPSTREAM.md) lists every change.

**Using the E2B SDKs and CLI.** BoxFab serves the same API, so the E2B SDKs and CLI work with it
as well. Set both variables, the domain first:

```bash
export E2B_DOMAIN=boxfab.io
export E2B_API_KEY="<your BoxFab API key>"
```

Without `E2B_DOMAIN`, the E2B tools send requests, including the key, to E2B's own service. The E2B
CLI's `e2b auth login` signs in to E2B's service; with BoxFab, use `E2B_API_KEY` instead.

Tested against BoxFab with `e2b` 2.62.0 (Python), `e2b` 2.61.0 (JavaScript) and `@e2b/cli` 2.23.0.

## License

MIT, as the E2B JavaScript SDK it is derived from; see [LICENSE](LICENSE).

BoxFab is a product of ContextFab, Inc.
