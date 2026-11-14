import {
  ConnectionOpts,
  BoxFabClientOpts,
  BoxFab as CoreBoxFab,
  Secret,
  Template,
  Volume,
} from 'boxfab'

import { Sandbox } from './sandbox'

export type { BoxFabClientOpts }

/**
 * BoxFab client with an explicitly bound connection configuration.
 *
 * The resources exposed by the client ({@link BoxFab.Sandbox},
 * {@link BoxFab.Volume}, {@link BoxFab.Template}, {@link BoxFab.Secret}) behave exactly
 * like the top-level `Sandbox` / `Volume` / `Template` / `Secret` exports,
 * except the options passed to the client are used as the defaults instead of
 * the environment variables.
 * Per-call options still take precedence over the client's options.
 *
 * Multiple clients are fully isolated from each other and from the top-level
 * env-configured exports.
 *
 * @example
 * ```ts
 * import { BoxFab } from '@boxfab/desktop'
 *
 * const client = new BoxFab({ apiKey: 'e2b_...', domain: 'boxfab.io' })
 *
 * const desktop = await client.Sandbox.create()
 * await desktop.stream.start()
 * ```
 */
export class BoxFab {
  /**
   * Desktop `Sandbox` class bound to this client's connection configuration.
   */
  readonly Sandbox: typeof Sandbox

  /**
   * `Volume` class bound to this client's connection configuration.
   */
  readonly Volume: typeof Volume

  /**
   * `Template` bound to this client's connection configuration. Both the
   * builder (`client.Template()`) and the statics
   * (`client.Template.build(...)`, `client.Template.exists(...)`, …) work like
   * the top-level `Template`.
   */
  readonly Template: typeof Template

  /**
   * `Secret` class bound to this client's connection configuration.
   */
  readonly Secret: typeof Secret

  /**
   * Create a new client with the connection options bound to it.
   *
   * @param opts connection options used as the defaults for every call made
   *   through this client's resource classes.
   */
  constructor(opts?: BoxFabClientOpts) {
    // Options are copied so later mutations of the caller's object cannot
    // change the bound configuration. `signal` is dropped rather than only
    // typed away, since it cancels a single request and a caller passing a
    // wider-typed object (or plain JS) would otherwise bind it to every call.
    const boundOpts: BoxFabClientOpts = { ...(opts ?? {}) }
    delete (boundOpts as ConnectionOpts).signal

    if (boundOpts.headers) {
      boundOpts.headers = { ...boundOpts.headers }
    }
    if (boundOpts.apiHeaders) {
      boundOpts.apiHeaders = { ...boundOpts.apiHeaders }
    }

    this.Sandbox = class extends Sandbox {
      protected static override readonly boundOpts = boundOpts
    }

    // The resources that are not specific to the Desktop are bound by the core
    // client.
    const core = new CoreBoxFab(boundOpts)
    this.Volume = core.Volume
    this.Template = core.Template
    this.Secret = core.Secret
  }
}
