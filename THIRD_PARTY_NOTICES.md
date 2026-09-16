# Third-Party Notices / 第三方声明

The root AGPL declaration does not replace the following upstream terms.
Dependencies installed from `requirements.txt` also retain their own licenses.

## AudioCompare

- Local paths: `hinghwa-dict-backend/AudioCompare/**`, except separately
  identified components below.
- Upstream: <https://github.com/charlesconnell/AudioCompare>
- Audited upstream revision: `f91ecf6404a7306063b2c05c9c9003ff27b07ce3`
- Copyright: 2013–2026 An Dang, Cory Finger, Zheng Hui Er, Charles Connell.
- License: BSD 3-Clause; full text is preserved in
  `hinghwa-dict-backend/AudioCompare/LICENSE.AudioCompare`.

The local tree is an older layout and may contain local changes. The upstream
reference fixes the provenance and currently published license; it does not
assert that the local files are byte-identical to that revision.

## matplotlib-derived FFT fragment

- Local path: the identified fragment in
  `hinghwa-dict-backend/AudioCompare/FFT.py`.
- Copyright: 2002–2011 John D. Hunter; all rights reserved.
- License: Matplotlib License Agreement 1.2.0, preserved in
  `hinghwa-dict-backend/AudioCompare/LICENSE.matplotlib` as required by the
  upstream project's own acknowledgement.

## LAME 3.98.4

- Historical path: `hinghwa-dict-backend/AudioCompare/lame`.
- Current status: removed from the current tree on 2026-09-16 after a real MP3
  regression check confirmed that the existing application path decodes MP3
  through its pre-existing `pydub`/`ffmpeg` implementation without executing
  the vendored file. Runtime behavior was not migrated to direct LAME execution.
- Historical binary identification: 32-bit GNU/Linux executable embedding
  version strings `3.98.4` and `LAME3.98r` and its own LGPL notice.
- Historical binary SHA-256:
  `e4c437fe6498c08be16ffaa1542dc07f91dd6b183f29c4f191cf426321868388`.
- Upstream release: <https://sourceforge.net/projects/lame/files/lame/3.98.4/>
- Official source archive: `lame-3.98.4.tar.gz`; SHA-256 verified on
  2026-09-16:
  `ac3144c76617223a9be4aaa3e28a66b51bcab28141050c3af04cb06836f772c8`.
- Audited source mirror tag: `RELEASE__3_98_4`, commit
  `26e6bdb494ba926b0ec27f040aeacac7120236f8` at
  <https://github.com/enzo1982/lame/tree/RELEASE__3_98_4>.
- License: GNU Library/Lesser General Public License version 2 or any later
  version (`LGPL-2.0-or-later`); the version 2 license text from that fixed tag
  is preserved in `hinghwa-dict-backend/AudioCompare/LICENSE.LAME`.
- Historical corresponding-source reference: the unmodified 3.98.4 release at
  the upstream link above and the fixed source mirror tag. The repository does
  not claim to have built or modified the historical executable. Git history
  is retained, so this record and `LICENSE.LAME` remain available for auditing
  earlier revisions even though the executable is absent from the current tree.

## BAAI/bge-small-zh-v1.5

- Runtime/build-time model, not tracked in this Git repository.
- Upstream: <https://huggingface.co/BAAI/bge-small-zh-v1.5>
- Pinned revision: `7999e1d3359715c523056ef9478215996d62a620`.
- Published model license: MIT. The model weights and model-card materials are
  not relicensed by this repository's AGPL declaration.

None of these third-party components is included in the scope of an alternative
commercial license unless the relevant rightsholder separately authorizes it.

---

根目录 AGPL 声明不覆盖或替换上述第三方条款。`AudioCompare/` 的主体代码和其中的
matplotlib 派生片段适用各自的相邻许可证；实际回归确认现有 `pydub`/`ffmpeg` 路径
不执行历史 LAME 二进制后，该二进制已从当前代码树移除，音频运行逻辑没有迁移为直接
调用 LAME；构建时下载的 BGE 模型继续适用上游条款。
除非相关权利人另行授权，这些内容均不属于替代商业许可证的授权范围。
