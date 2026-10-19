import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { appendFile, readFile, writeFile } from 'node:fs/promises'
import { existingImageDigest, inspectImage, verifyImage, verifiedRuntimeImage, verifyPublicPull } from './release-image.mjs'
import { migrationTree, qualityBindings, semanticModel } from './release-contract.mjs'

const sha = process.env.SOURCE_SHA
const date = process.env.BUILD_DATE
const image = 'ghcr.io/e-dialect/hinghwa-dict-backend'
const tag = `sha-${sha}`
assert.match(sha ?? '', /^[0-9a-f]{40}$/)
assert.match(date ?? '', /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/)
assert.ok(process.env.GITHUB_OUTPUT)
function docker(args) {
  try { return execFileSync('docker', args, { stdio: ['ignore', 'pipe', 'pipe'] }).toString().trim() }
  catch { throw new Error('Exact-image operation failed; diagnostics withheld') }
}
let digest = await existingImageDigest('backend', sha, date)
if (process.argv[2] === 'prepare') {
  if (digest) {
    docker(['pull', '--platform', 'linux/amd64', `${image}@${digest}`])
    docker(['tag', `${image}@${digest}`, `${image}:${tag}`])
  }
  await appendFile(process.env.GITHUB_OUTPUT, `existing=${digest}\n`)
} else if (process.argv[2] === 'publish') {
  const migrations = migrationTree(sha)
  const receipt = JSON.parse(await readFile('release/runtime.json'))
  verifiedRuntimeImage(receipt, sha, migrations.digest)
  const ciRuns = qualityBindings(process.env.CI_RUNS)
  assert.equal(docker(['image', 'inspect', '--format', '{{.Id}}', `${image}:${tag}`]), receipt.imageId)
  if (!digest) {
    docker(['push', `${image}:${tag}`])
    digest = docker(['buildx', 'imagetools', 'inspect', `${image}:${tag}`, '--format', '{{.Manifest.Digest}}'])
  }
  const { raw, configRaw } = await inspectImage('backend', digest, sha, date)
  const configDigest = verifyImage(raw, configRaw, digest, sha, date)
  assert.equal(configDigest, receipt.imageId, 'Published image differs from smoke-tested image')
  const publicPullVerified = await verifyPublicPull(digest)
  const manifest = {
    schemaVersion: 1, contract: 'hinghwa-backend-package-v1',
    repository: 'e-dialect/hinghwa-dict-backend', repositoryID: 388176151,
    branch: 'develop', sourceSHA: sha, platform: 'linux/amd64', publicPullVerified,
    quality: { policy: 'all-latest-trusted-workflows-v1', runs: ciRuns },
    djangoVersion: receipt.djangoVersion, semanticModel,
    migrations,
    validation: { syntheticPackage: receipt },
    productionReadiness: { approved: false, existingDataUpgradeVerified: false, workerTopologyApproved: false },
    images: { backend: { image, imageRef: `${image}@${digest}`, tag, digest, configDigest, platform: 'linux/amd64', revision: sha } },
  }
  await writeFile('release/release-manifest.json', JSON.stringify(manifest, null, 2) + '\n')
} else {
  throw new Error('Use prepare or publish')
}
