# Backend package publication

This repository publishes an immutable `linux/amd64` GHCR package for the user-approved `develop` branch. Publication is packaging evidence only. It does not authorize a production deployment, an existing SQLite upgrade, a worker topology, or a server command/configuration change.

## Quality contract

The existing workflows remain unchanged, including their push, pull-request and manual triggers. Publisher authorization checks all of these workflows on the exact current `develop` SHA:

| Workflow file | Required job names |
| --- | --- |
| `e2e.yml` | `e2e`, `docker-build` |
| `lint-changed-files.yml` | `lint` |
| `lint-json.yml` | `lint` |
| `release-safety.yml` | `Release safety`, `Package image and synthetic SQLite/BGE smoke` |

Only the latest trusted push/manual run in repository `e-dialect/hinghwa-dict-backend` (ID `388176151`) may satisfy each workflow. PR and fork runs never authorize publication. Each run's ID, attempt and workflow ID are bound together; all required jobs must have succeeded in that attempt. An additional failed job also fails its workflow. Duplicate/missing jobs, API failures and explicit unsuccessful conclusions fail closed. Pending/missing metadata gets at most 60 seconds, including hanging requests. An earlier workflow completion may therefore produce a failed publisher while another workflow is still running; the last quality workflow's completion triggers a fresh full authorization. Re-running any quality workflow invalidates an earlier attempt binding.

Authorization runs before any checkout/registry credentials and is repeated before registry login and after the exact-image smoke, immediately before publication. Reauthorization requires the same run IDs and attempts. A final second snapshot catches branch changes and reruns during job reads. Concurrent publishers are serialized; all other package writers must honor the immutable SHA tag contract, since GHCR has no cross-writer compare-and-swap guarantee.

Manual publication requires the full current SHA plus a latest trusted quality run ID. It discovers and verifies all other workflow runs rather than trusting a manually selected subset. No separate cached aggregate gate is consumed.

## Image and evidence

The independent package-image job in `release-safety.yml` runs on PRs, develop pushes and manual CI. It builds `hinghwa-dict-backend/Dockerfile.release` with the original application context for `linux/amd64`, loads the image locally without registry login/publication, and executes the real network-none probe before uploading its synthetic receipt. The publisher requires this job and repeats the probe against its exact publish/reused image. PR quality runs remain ineligible to authorize publication.

The publisher builds the same independent release Dockerfile and original context with the pinned model defaults, and does not modify application code, settings, migrations, Compose or entrypoint. It does not include another checkout's dirty files. A source tag `sha-<full SHA>` is reused only after source/platform/created/version labels and raw registry config identity verify. An existing tag is never intentionally overwritten. The exact local image config ID is bound to the smoke receipt, immutable registry digest and raw registry config digest.

The release-only profile fixes `torch==2.14.1+cpu` to match the upstream patch resolved in the current PR's original docker-build run (39293374306, job 118199500429); the historical run 35074195641 resolved 2.14.0. The original Dockerfile, requirements and all three original quality workflows remain unchanged. The CPU wheel is installed directly from [the official PyTorch source](https://download.pytorch.org/whl/cpu/torch/) with its SHA-256 pinned, followed by the original requirements under a CPU constraint and `pip check`. Build and real-image probe reject CUDA/Triton distributions and require `torch.version.cuda is None`.

| Official wheel evidence | Value |
| --- | --- |
| Wheel | `torch-2.14.1+cpu-cp310-cp310-manylinux_2_28_x86_64.whl` |
| Wheel SHA-256 | `4ce2a6ae7d302bba56ef7c5c92d9f752728896cfe2626a7f3e5293f879e36650` |
| PEP 658 metadata SHA-256 | `a3fd232f82dcc389c6dab2665dfc17649c03ffb72cb641e96a76a0690177b918` |
| HEAD Content-Length | `196197995` bytes; wheel download size, not installed/image size |

Every successful real-image receipt records actual Docker image `.Size` as `imageExpandedBytes` and `docker history --format '{{.Size}}'` layer sizes without printing history commands. It also records selected dependency versions and regular-file bytes (excluding symlinks) for torch, the model cache and static files. These component counts describe apparent contents, not unique layer/storage usage. All size evidence is bound to the probed config ID and copied into the manifest. The workflow does not declare production capacity sufficient: apply the deployment host's current free-space/retention policy to the measured expanded size before import.

`check-package.py` starts a disposable `--network none`, read-only container by its image ID with only probe inputs mounted read-only. Its only writable state is tmpfs. It imports the image's Django settings and applies synthetic in-process storage/logging/email overrides, a synthetic secret, no production credentials, and no production mounts. The probe verifies every tracked migration file against its exact source bytes, migrates a new temporary SQLite database, checks no pending migrations and SQLite integrity, creates/verifies/deletes a synthetic user, and loads the pinned model cache offline to encode synthetic text. It removes its container and temporary probe directory before emitting success. It does not start `runserver` or a semantic worker. Empty-database migration is not production-data compatibility evidence.

`backend-package-manifest` contains `release/release-manifest.json` and the synthetic receipt. The `hinghwa-backend-package-v1` manifest records every quality run binding, source SHA, image config ID, registry digest, platform, Django version, canonical tracked migration path/content SHA-256 tree, and model name/revision. `productionReadiness` remains false. This contract deliberately does not pretend to satisfy a deployment consumer's single `ciRunId`/`CI gate` or browser/static recovery contract; backend deployment support requires separate review.

Public visibility is already approved for this open-source application. The publisher verifies anonymous access to the exact digest before emitting a successful manifest. GHCR can initially create a private package: a maintainer must apply the approved public visibility in package settings, then rerun publication to reuse the existing SHA image. Failure at this point retains the package but does not report it as publicly accepted. This workflow does not claim to change package visibility or branch protection settings. Maintainers may separately require the existing quality checks and `Release safety` in develop protection.

## Local verification

These commands need only Node and Python and never invoke Docker:

```sh
node --test scripts/release.test.mjs
python3 -m unittest discover -s scripts -p 'test_*.py'
```

The Python test mocks container execution and compares the real tracked migration digest between Python and Node. It does not claim the image probe ran. Real image build, isolated probe, current exact-SHA GitHub quality jobs, registry push/pull and public visibility are accepted only when the future CI run actually completes.

The contributor guide's PR/review workflow still applies before merge (`CONTRIBUTING.md`, “Merge 规范”). The explicit approval of `develop` is the release-branch decision for this packaging change; the old generic master/develop release narrative is not silently rewritten. Production/test isolation, historical `material`/`semantic-search` files, worker participation, backups and old→new→old database compatibility remain separate unresolved decisions. No production registry is enabled by these scripts.
