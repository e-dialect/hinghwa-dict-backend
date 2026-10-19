import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { hash } from './release-image.mjs'

export { releaseBaseImage } from './release-image.mjs'
export const torchCPUWheel = {
  version: '2.14.1+cpu',
  url: 'https://download-r2.pytorch.org/whl/cpu/torch-2.14.1%2Bcpu-cp310-cp310-manylinux_2_28_x86_64.whl',
  sha256: '4ce2a6ae7d302bba56ef7c5c92d9f752728896cfe2626a7f3e5293f879e36650',
  coreMetadataSHA256: 'a3fd232f82dcc389c6dab2665dfc17649c03ffb72cb641e96a76a0690177b918',
}
export const semanticModel = { name: 'BAAI/bge-small-zh-v1.5', revision: '7999e1d3359715c523056ef9478215996d62a620' }
export function migrationTree(sourceSHA) {
  assert.match(sourceSHA ?? '', /^[0-9a-f]{40}$/)
  const paths = execFileSync('git', ['ls-tree', '-rz', '--name-only', sourceSHA]).toString().split('\0')
    .filter(name => name.startsWith('hinghwa-dict-backend/') && name.includes('/migrations/')).sort()
  assert.ok(paths.length > 0, 'No tracked Django migration files')
  const entries = paths.map(name => [name.slice('hinghwa-dict-backend/'.length), hash(execFileSync('git', ['show', `${sourceSHA}:${name}`]))])
  return { algorithm: 'sha256-canonical-path-content-v1', entries, digest: hash(JSON.stringify(entries)) }
}
export function qualityBindings(raw) {
  const bindings = JSON.parse(raw ?? 'null')
  const files = ['e2e.yml', 'lint-changed-files.yml', 'lint-json.yml', 'release-safety.yml']
  assert.deepEqual(Object.keys(bindings ?? {}), files)
  for (const binding of Object.values(bindings)) for (const field of ['id', 'attempt', 'workflowID']) assert.ok(Number.isSafeInteger(binding[field]) && binding[field] > 0)
  return bindings
}
