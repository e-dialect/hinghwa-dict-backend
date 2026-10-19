import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { torchCPUWheel, releaseBaseImage } from './release-contract.mjs'
import { hash, verifyImage, existingImageDigest, verifiedRuntimeImage, verifyPublicPull } from './release-image.mjs'

const sha = 'a'.repeat(40)
const date = '2026-10-14T00:00:00Z'
function fixture(change = {}) {
  const config = Buffer.from(JSON.stringify({ os: 'linux', architecture: 'amd64', config: { Labels: {
    'org.opencontainers.image.revision': sha,
    'org.opencontainers.image.source': 'https://github.com/e-dialect/hinghwa-dict-backend',
    'org.opencontainers.image.version': `sha-${sha}`,
    'org.opencontainers.image.created': date,
    'org.opencontainers.image.base.name': releaseBaseImage.image,
    'org.opencontainers.image.base.digest': releaseBaseImage.manifestDigest,
  } }, ...change }))
  const raw = Buffer.from(JSON.stringify({ mediaType: 'application/vnd.oci.image.manifest.v1+json', config: { digest: hash(config), size: config.length } }))
  return { config, raw, digest: hash(raw) }
}
test('manifest hashes actual raw config and accepts only correct identity', () => {
  const f = fixture()
  assert.equal(verifyImage(f.raw, f.config, f.digest, sha, date), hash(f.config))
  assert.throws(() => verifyImage(f.raw, Buffer.from('{}'), f.digest, sha, date))
  assert.throws(() => verifyImage(f.raw, f.config, 'sha256:' + '0'.repeat(64), sha, date))
  assert.throws(() => verifyImage(f.raw, f.config, f.digest, 'b'.repeat(40), date))
  const arm = fixture({ architecture: 'arm64' })
  assert.throws(() => verifyImage(arm.raw, arm.config, arm.digest, sha, date))
})
test('raw config must bind both exact base labels', () => {
  for (const key of ['org.opencontainers.image.base.name', 'org.opencontainers.image.base.digest']) {
    for (const replacement of [undefined, 'untrusted-base']) {
      const labels = JSON.parse(fixture().config).config.Labels
      if (replacement === undefined) delete labels[key]
      else labels[key] = replacement
      const f = fixture({ config: { Labels: labels } })
      assert.throws(() => verifyImage(f.raw, f.config, f.digest, sha, date), /Image label mismatch/)
    }
  }
})
test('unknown registry access fails closed and only new-package 404 is absent', async () => {
  const old = globalThis.fetch
  process.env.GHCR_TOKEN = 'synthetic-only'
  try {
    globalThis.fetch = async () => ({ status: 403, ok: false })
    await assert.rejects(existingImageDigest('backend', sha, date))
    globalThis.fetch = async () => ({ status: 404, ok: false })
    assert.equal(await existingImageDigest('backend', sha, date), '')
  } finally { globalThis.fetch = old; delete process.env.GHCR_TOKEN }
})

const yaml = readFileSync(new URL('../.github/workflows/release.yml', import.meta.url), 'utf8')
const scripts = [...yaml.matchAll(/          script: \|\n([\s\S]*?)(?=\n(?:  publish:|      - name:)|$)/g)].map(match => match[1].split('\n').map(line => line.replace(/^            /, '')).join('\n').trim())
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const files = ['e2e.yml', 'lint-changed-files.yml', 'lint-json.yml', 'release-safety.yml']
const jobNames = [['e2e', 'docker-build'], ['lint'], ['lint'], ['Release safety', 'Package image and synthetic SQLite/BGE smoke']]
const identity = { full_name: 'e-dialect/hinghwa-dict-backend', id: 388176151 }
function fakeClock() {
  let now = 0, sequence = 0, scheduled = false
  const timers = new Map()
  function pump() {
    if (scheduled || !timers.size) return
    scheduled = true
    setImmediate(() => {
      scheduled = false
      const task = [...timers].sort((a, b) => a[1].at - b[1].at || a[0] - b[0])[0]
      if (!task) return
      timers.delete(task[0]); now = task[1].at; task[1].callback(); pump()
    })
  }
  return {
    Date: { now: () => now },
    setTimeout(callback, delay) { const id = ++sequence; timers.set(id, { callback, at: now + delay }); pump(); return id },
    clearTimeout(id) { timers.delete(id) },
    close() { timers.clear() },
  }
}
const bindings = Object.fromEntries(files.map((file, i) => [file, { id: i + 100, attempt: 1, workflowID: i + 10 }]))
async function authorize(options = {}) {
  const clock = fakeClock(), out = {}, stats = options.stats ?? {}
  Object.assign(stats, { snapshots: 0, outputs: out, requests: [] })
  let round = -1
  const runFor = i => ({ id: i + 100, workflow_id: i + 10, run_number: 7, run_attempt: 1,
    head_sha: sha, head_branch: 'develop', event: 'push', repository: identity, head_repository: identity,
    status: 'completed', conclusion: 'success', ...(options.run?.(i, round) ?? {}) })
  const track = args => { stats.requests.push(args); assert.ok(args.request.signal instanceof AbortSignal) }
  const github = { rest: { repos: { getBranch: async args => {
    track(args); round++; stats.snapshots++
    return { data: { commit: { sha: options.branch?.(round) ?? sha } } }
  } }, actions: {
    getWorkflow: async args => { track(args); return { data: { id: files.indexOf(args.workflow_id) + 10 } } },
    listWorkflowRuns: async args => {
      track(args)
      const i = args.workflow_id - 10
      return { data: { workflow_runs: options.candidates?.(i, round) ?? [runFor(i)] } }
    },
    getWorkflowRun: async args => {
      track(args)
      if (options.block) return new Promise(() => {})
      if (options.apiError) throw new Error('synthetic API error')
      return { data: runFor(args.run_id - 100) }
    }, listJobsForWorkflowRun: () => {},
  } }, paginate: async (_endpoint, args) => {
    track(args)
    const i = args.run_id - 100
    return options.jobs?.(i, round) ?? jobNames[i].map(name => ({ name, run_attempt: 1, status: 'completed', conclusion: 'success' }))
  } }
  const previous = process.env.EXPECTED_CI_RUNS
  if (options.expected) process.env.EXPECTED_CI_RUNS = JSON.stringify(options.expected)
  else delete process.env.EXPECTED_CI_RUNS
  try {
    await new AsyncFunction('github', 'context', 'core', 'Date', 'setTimeout', 'clearTimeout', scripts[options.code ?? 0])(github,
      { repo: { owner: 'e-dialect', repo: 'hinghwa-dict-backend' }, payload: { repository: identity, workflow_run: { id: 100, head_sha: sha } } },
      { setOutput: (key, value) => { out[key] = value } }, clock.Date, clock.setTimeout, clock.clearTimeout)
    return out
  } finally {
    stats.elapsed = clock.Date.now(); clock.close()
    if (previous === undefined) delete process.env.EXPECTED_CI_RUNS
    else process.env.EXPECTED_CI_RUNS = previous
  }
}
test('all three authorization sites share the actual bounded aggregate policy', async () => {
  assert.equal(scripts.length, 3)
  assert.equal(scripts[0], scripts[1]); assert.equal(scripts[0], scripts[2])
  for (let code = 0; code < 3; code++) {
    assert.deepEqual(await authorize({ code, expected: code ? bindings : undefined }), { source_sha: sha, ci_runs: JSON.stringify(bindings) })
  }
})
for (let workflow = 0; workflow < files.length; workflow++) {
  for (const field of ['head_sha', 'head_branch', 'head_repository', 'repository', 'workflow_id', 'event']) {
    test(`reject ${files[workflow]} with wrong ${field}`, async () => {
      const changes = { head_sha: 'b'.repeat(40), head_branch: 'main', head_repository: { ...identity, id: 1 }, repository: { ...identity, id: 1 }, workflow_id: 99, event: 'pull_request' }
      await assert.rejects(authorize({ run: i => i === workflow ? { [field]: changes[field] } : {} }))
    })
  }
  for (const conclusion of ['failure', 'cancelled', 'skipped', 'neutral', 'timed_out', 'action_required', null]) {
    test(`reject failed ${files[workflow]} ${conclusion} without retry`, async () => {
      const stats = {}
      await assert.rejects(authorize({ stats, run: i => i === workflow ? { conclusion } : {} }))
      assert.equal(stats.elapsed, 0); assert.deepEqual(stats.outputs, {})
    })
  }
  test(`reject newly rerun ${files[workflow]} after initial binding`, async () => {
    await assert.rejects(authorize({ expected: bindings, run: i => i === workflow ? { run_attempt: 2 } : {} }), /attempts changed/)
  })
}
for (const [workflow, names] of jobNames.entries()) for (const name of names) {
  test(`each original quality job required: ${files[workflow]}/${name}`, async () => {
    for (const problem of ['missing', 'duplicate', 'failure', 'skipped', 'wrong-attempt']) {
      await assert.rejects(authorize({ jobs: i => {
        if (i !== workflow) return undefined
        const good = names.map(job => ({ name: job, run_attempt: 1, status: 'completed', conclusion: 'success' }))
        if (problem === 'missing') return good.filter(job => job.name !== name)
        if (problem === 'duplicate') return [...good, good.find(job => job.name === name)]
        return good.map(job => job.name === name ? { ...job, ...(problem === 'wrong-attempt' ? { run_attempt: 2 } : { conclusion: problem }) } : job)
      } }))
    }
  })
}
test('pending jobs converge at five seconds with all workflow IDs bound', async () => {
  const stats = {}
  assert.equal((await authorize({ stats, jobs: (i, round) => i === 0 && round === 0 ? [] : undefined })).source_sha, sha)
  assert.equal(stats.elapsed, 5_000)
})
test('missing metadata and hanging requests stop at exactly sixty seconds', async () => {
  for (const change of [{ jobs: () => [] }, { candidates: () => [] }, { block: true }]) {
    const stats = {}
    await assert.rejects(authorize({ ...change, stats }), /Timed out/)
    assert.equal(stats.elapsed, 60_000); assert.deepEqual(stats.outputs, {})
    assert.ok(stats.requests.every(request => request.request.signal.aborted))
  }
})
test('branch moves, newer CI runs, attempts and in-progress reruns invalidate successful job reads', async () => {
  for (const change of [
    { branch: round => round > 0 ? 'b'.repeat(40) : sha },
    { run: (i, round) => round > 0 && i === 2 ? { run_attempt: 2 } : {} },
    { run: (i, round) => round > 0 && i === 2 ? { status: 'in_progress', conclusion: null } : {} },
    { candidates: (i, round) => round > 0 && i === 2 ? [] : undefined },
  ]) await assert.rejects(authorize(change))
})
test('API errors fail closed without polling', async () => {
  const stats = {}
  await assert.rejects(authorize({ apiError: true, stats })); assert.equal(stats.elapsed, 0)
})
test('newer quality run is rejected against bound IDs even for the same SHA', async () => {
  const changed = structuredClone(bindings); changed['lint-json.yml'].id++
  await assert.rejects(authorize({ expected: changed }), /changed after authorization/)
})
test('only complete backend synthetic receipts authorize the smoke-tested config ID', () => {
  const good = { result: 'PASS', cleanup: 'PASS', sourceSHA: sha, migrationTreeDigest: 'sha256:' + 'f'.repeat(64), djangoVersion: '5.0.3', semanticModel: { name: 'BAAI/bge-small-zh-v1.5', revision: '7999e1d3359715c523056ef9478215996d62a620' }, modelLoadedOffline: true, emptySQLiteMigrated: true, sqliteIntegrity: true, syntheticUserRoundtrip: true, noPendingMigrations: true, network: 'none', productionDataUsed: false, imageId: 'sha256:' + 'c'.repeat(64), torchCPU: { version: '2.14.1+cpu', cuda: null, cudaAvailable: false, forbiddenDistributions: [] }, dependenciesConsistent: true, imageExpandedBytes: 123456, layerSizesHuman: ['12.3MB', '0B'], components: { versions: { torch: '2.14.1+cpu' }, regularFileBytesNoSymlinks: { torch: 123, semanticModelCache: 456, static: 789 } } }
  assert.equal(verifiedRuntimeImage(good, sha, good.migrationTreeDigest), good.imageId)
  for (const change of [
    { cleanup: 'FAIL' }, { sourceSHA: 'b'.repeat(40) }, { migrationTreeDigest: '' }, { djangoVersion: '4.2' },
    { semanticModel: { ...good.semanticModel, revision: 'main' } },
    { torchCPU: { ...good.torchCPU, version: '2.14.1' } }, { torchCPU: { ...good.torchCPU, cuda: '13.0' } },
    { torchCPU: { ...good.torchCPU, forbiddenDistributions: ['nvidia-cublas'] } }, { dependenciesConsistent: false },
    { imageExpandedBytes: 0 }, { imageExpandedBytes: '12345' }, { layerSizesHuman: [] },
    { components: { ...good.components, versions: { torch: '2.14.1' } } },
    { components: { ...good.components, regularFileBytesNoSymlinks: { torch: 0, semanticModelCache: 456, static: 789 } } }, { network: 'default' }, { productionDataUsed: true },
    ...['modelLoadedOffline', 'emptySQLiteMigrated', 'sqliteIntegrity', 'syntheticUserRoundtrip', 'noPendingMigrations'].map(flag => ({ [flag]: false })),
  ]) assert.throws(() => verifiedRuntimeImage({ ...good, ...change }, sha, good.migrationTreeDigest))
})

test('public package evidence uses anonymous credentials and exact digest only', async () => {
  const previous = globalThis.fetch
  const digest = 'sha256:' + 'c'.repeat(64)
  const calls = []
  try {
    globalThis.fetch = async (url, options) => {
      calls.push({ url: String(url), options })
      return calls.length === 1
        ? { ok: true, json: async () => ({ token: 'synthetic-anonymous' }) }
        : { ok: true, headers: new Map([['docker-content-digest', digest]]) }
    }
    assert.equal(await verifyPublicPull(digest), true)
    assert.equal(calls[0].options.headers, undefined)
    assert.equal(calls[1].options.headers.Authorization, 'Bearer synthetic-anonymous')
    assert.equal(calls[1].url.endsWith('/manifests/' + digest), true)
    globalThis.fetch = async () => ({ ok: false })
    await assert.rejects(verifyPublicPull(digest), /public visibility/)
  } finally { globalThis.fetch = previous }
})

test('release recipe fixes the official wheel hash and constraint used by its manifest contract', () => {
  const recipe = readFileSync(new URL('../hinghwa-dict-backend/Dockerfile.release', import.meta.url), 'utf8')
  const constraint = readFileSync(new URL('../hinghwa-dict-backend/requirements.release-cpu.txt', import.meta.url), 'utf8')
  assert.ok(recipe.includes(`${torchCPUWheel.url}#sha256=${torchCPUWheel.sha256}`))
  assert.ok(constraint.split('\n').includes(`torch==${torchCPUWheel.version}`))
  assert.ok(recipe.includes('pip check'))
  assert.ok(recipe.includes('torch.version.cuda is None'))
  const pinnedBase = `python:3.10-slim-bookworm@${releaseBaseImage.manifestDigest}`
  assert.equal(recipe.split(`FROM ${pinnedBase}`).length - 1, 2)
  const runtime = recipe.split(' AS runtime\n')[1]
  assert.ok(runtime.includes('COPY --from=dependencies /opt/venv /opt/venv'))
  assert.ok(runtime.includes('--no-install-recommends ffmpeg libgomp1'))
  assert.equal(runtime.includes('build-essential'), false)
  assert.ok(runtime.includes('cache_folder='))
  assert.ok(runtime.includes(`org.opencontainers.image.base.digest="${releaseBaseImage.manifestDigest}"`))
  for (const workflow of ['release.yml', 'release-safety.yml']) {
    const content = readFileSync(new URL(`../.github/workflows/${workflow}`, import.meta.url), 'utf8')
    assert.ok(content.includes('file: ./hinghwa-dict-backend/Dockerfile.release'))
  }
})
