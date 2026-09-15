# Asset and Data Boundaries / 资产与数据边界

The repository's root AGPL declaration covers authorized software code. It does
not by itself grant rights in separately sourced or user-provided content.

| Path or material | Boundary |
| --- | --- |
| `images/branches.webp` | Documentation screenshot. Its inclusion in the repository does not create a trademark or broader reuse grant; provenance and permission must be checked for reuse outside project documentation. |
| `tests/*.json` | API test collections and fixtures are treated as project test material, not as a license grant for any real dictionary, user, article, music, or recording content that a deployment may return. |
| Runtime database rows and uploads | Dictionary entries, definitions, articles, comments, user profiles, recordings, music, images, and other uploaded content require their own provenance and permissions. |
| `semantic_search_data/`, model caches, FAISS indexes, manifests, and generated snapshots | Generated or downloaded artifacts are not tracked source code and are governed by their inputs and applicable upstream terms. |
| Names, logos, domains, and product identity | The code license does not grant trademark rights or imply endorsement. |

Before adding data, audio, media, or model files, record the source, rightsholder,
license/permission, and any attribution or privacy constraints. Do not assume
that a code contribution agreement covers those assets.

---

根目录 AGPL 声明仅覆盖项目有权授权的软件代码。部署产生或接收的词典内容、用户
内容、录音、音乐、媒体、模型、缓存与索引不会因此自动获得 AGPL 授权；新增此类
材料前必须记录来源、权利人、许可证或许可证明、署名要求以及隐私限制。项目名称、
Logo 与域名也不因代码开源而授予商标权或背书。
