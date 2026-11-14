// BoxFab: tests talk to BoxFab only. The SDK reads BOXFAB_* variables and ignores E2B_* ones;
// this guard additionally stops a run that was pointed at an E2B-hosted domain by mistake.
const domain = process.env.BOXFAB_DOMAIN || 'boxfab.io'
if (/(^|\.)e2b(-[a-z]+)?\.(app|dev|pro)$/.test(domain)) {
  throw new Error(`BOXFAB_DOMAIN=${domain} is an E2B domain; tests run against BoxFab only`)
}
