# BoxFab Desktop (JavaScript / TypeScript)

A virtual Linux desktop in a [BoxFab](https://boxfab.io) sandbox, for computer-use agents: mouse
and keyboard control, screenshots, application windows, and a live stream of the screen in the
browser.

## Getting started

### 1. Get a BoxFab API key

Get a key from the [BoxFab dashboard](https://dashboard.boxfab.io) and set it as
`BOXFAB_API_KEY`. The SDK reads only `BOXFAB_*` variables.

### 2. Install the SDK

```bash
npm install @boxfab/desktop
```

> **Stream access.** `desktop.stream.start()` runs without a password unless you pass
> `requireAuth: true`. The stream URL contains the sandbox ID, and anyone who has the URL can see
> and control the desktop. Pass `requireAuth: true` whenever the URL leaves your backend; the auth
> key is then part of the URL returned by `getUrl({ authKey })`, so share that URL only with the
> intended viewer.

### 3. Create Desktop Sandbox

```javascript
import { Sandbox } from '@boxfab/desktop'

// Start a new desktop sandbox
const desktop = await Sandbox.create()

// Launch an application
await desktop.launch('google-chrome') // or vscode, firefox, etc.

// Wait 10s for the application to open
await desktop.wait(10000)

// Stream the application's window
// Note: there can be only one stream at a time
// You need to stop the current stream before streaming another application
await desktop.stream.start({
  windowId: await desktop.getCurrentWindowId(), // if not provided the whole desktop will be streamed
  requireAuth: true,
})

// Get the stream auth key
const authKey = desktop.stream.getAuthKey()

// Print the stream URL
console.log('Stream URL:', desktop.stream.getUrl({ authKey }))

// Kill the sandbox after the tasks are finished
// await desktop.kill()
```

### 4. Bind the configuration to a client

The top-level `Sandbox` export reads its configuration from the environment variables. To use an explicit configuration — e.g. several API keys or domains in one process — create a `BoxFab` client and use the resources it exposes:

```javascript
import { BoxFab } from '@boxfab/desktop'

const client = new BoxFab({ apiKey: 'e2b_***', domain: 'boxfab.io' })

const desktop = await client.Sandbox.create()
await desktop.stream.start()

// The core resources are bound to the client's configuration as well.
const volume = await client.Volume.create('my-volume')
const exists = await client.Template.exists('my-template')
await client.Secret.create('openai-api-key', 'sk-***')

// The classes can be destructured and used like the top-level ones.
const { Sandbox } = client
const paginator = Sandbox.list()
```

Per-call options still take precedence over the client's options, and clients are isolated from each other and from the env-configured top-level exports.

## Features

### Streaming desktop's screen

```javascript
import { Sandbox } from '@boxfab/desktop'

const desktop = await Sandbox.create()

// Start the stream
await desktop.stream.start()

// Get stream URL
const url = desktop.stream.getUrl()
console.log(url)

// Stop the stream
await desktop.stream.stop()
```

### Streaming with password protection

```javascript
import { Sandbox } from '@boxfab/desktop'

const desktop = await Sandbox.create()

// Start the stream
await desktop.stream.start({
  requireAuth: true, // Enable authentication with an auto-generated key
})

// Retrieve the authentication key
const authKey = await desktop.stream.getAuthKey()

// Get stream URL
const url = desktop.stream.getUrl({ authKey })
console.log(url)

// Stop the stream
await desktop.stream.stop()
```

### Streaming specific application

> [!WARNING]
>
> - Will throw an error if the desired application is not open yet
> - The stream will close once the application closes
> - Creating multiple streams at the same time is not supported, you may have to stop the current stream and start a new one for each application

```javascript
import { Sandbox } from '@boxfab/desktop'

const desktop = await Sandbox.create()

// Get current (active) window ID
const windowId = await desktop.getCurrentWindowId()

// Get all windows of the application
const windowIds = await desktop.getApplicationWindows('Firefox')

// Start the stream
await desktop.stream.start({ windowId: windowIds[0] })

// Stop the stream
await desktop.stream.stop()
```

### Mouse control

```javascript
import { Sandbox } from '@boxfab/desktop'

const desktop = await Sandbox.create()

await desktop.doubleClick()
await desktop.leftClick()
await desktop.leftClick(100, 200)
await desktop.rightClick()
await desktop.rightClick(100, 200)
await desktop.middleClick()
await desktop.middleClick(100, 200)
await desktop.scroll(10) // Scroll by the amount. Positive for up, negative for down.
await desktop.moveMouse(100, 200) // Move to x, y coordinates
await desktop.drag([100, 100], [200, 200]) // Drag using the mouse
await desktop.mousePress('left') // Press the mouse button
await desktop.mouseRelease('left') // Release the mouse button
```

### Keyboard control

```javascript
import { Sandbox } from '@boxfab/desktop'

const desktop = await Sandbox.create()

// Write text at the current cursor position with customizable typing speed
await desktop.write('Hello, world!')
await desktop.write('Fast typing!', { chunkSize: 50, delayInMs: 25 }) // Faster typing

// Press keys
await desktop.press('enter')
await desktop.press('space')
await desktop.press('backspace')
await desktop.press(['ctrl', 'c']) // Key combination
```

### Window control

```javascript
import { Sandbox } from '@boxfab/desktop'

const desktop = await Sandbox.create()

// Get current (active) window ID
const windowId = await desktop.getCurrentWindowId()

// Get all windows of the application
const windowIds = await desktop.getApplicationWindows('Firefox')

// Get window title
const title = await desktop.getWindowTitle(windowId)
```

### Screenshot

```javascript
import { Sandbox } from '@boxfab/desktop'

const desktop = await Sandbox.create()
const image = await desktop.screenshot()
// Save the image to a file
fs.writeFileSync('screenshot.png', image)
```

### Open file

```javascript
import { Sandbox } from '@boxfab/desktop'

const desktop = await Sandbox.create()

// Open file with default application
await desktop.files.write('/home/user/index.js', "console.log('hello')") // First create the file
await desktop.open('/home/user/index.js') // Then open it
```

### Launch applications

```javascript
import { Sandbox } from '@boxfab/desktop'

const desktop = await Sandbox.create()

// Launch the application
await desktop.launch('google-chrome')
```

### Run any bash commands

```javascript
import { Sandbox } from '@boxfab/desktop'

const desktop = await Sandbox.create()

// Run any bash command
const out = await desktop.commands.run('ls -la /home/user')
console.log(out)
```

### Wait

```javascript
import { Sandbox } from '@boxfab/desktop'

const desktop = await Sandbox.create()
await desktop.wait(1000) // Wait for 1 second
```

## Under the hood

The desktop-like environment is based on Linux and [Xfce](https://www.xfce.org/) at the moment. We chose Xfce because it's a fast and lightweight environment that's also popular and actively supported. However, this Sandbox template is fully customizable and you can create your own desktop environment.
BoxFab's template is in [boxfab/desktop](https://github.com/boxfab/desktop/tree/main/template), generated from [e2b-dev/desktop](https://github.com/e2b-dev/desktop/tree/main/template).

BoxFab sandboxes are [Firecracker](https://firecracker-microvm.github.io/) microVMs, run on the
open-source [E2B](https://github.com/e2b-dev/infra) sandbox infrastructure. This package is derived
from the open-source E2B Desktop SDK;
[UPSTREAM.md](https://github.com/boxfab/js-sdk/blob/main/UPSTREAM.md) lists every change.

## License

MIT, as the E2B Desktop SDK it is derived from; see [LICENSE](LICENSE).

BoxFab is a product of ContextFab, Inc.
