# 兴化语记（后端）

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/e-dialect/hinghwa-dict-backend)

## 项目简介

兴化语记是 [E方言](https://edialect.top) 中`莆仙方言公共服务包` 的别称，主要服务对象包括福建省莆田市及其周边地区的莆仙方言使用者。

兴化语记目前包括网页端 ( https://pxm.edialect.top , https://hinghwa.cn )，微信小程序端（兴化语记），计划在本项目中通过 `uni-app` 增加移动端 ( https://m.pxm.edialect.top )，QQ小程序端等。

## 技术栈

> 项目采取前后端分离架构，其他的前端仓库可前往 https://github.com/e-dialect 进行寻找

采用 `Django` 框架提供网站访问服务，其他所依赖库可见 [requirementes.txt](./hinghwa-dict-backend/requirements.txt) 。

为方便项目部署，我们也通过 `docker` 将整个服务制作成镜像，以便 `Traefik` 将流量转发至容器内部。

词语查询的语义检索部署与索引维护见 [语义检索说明](docs/SEMANTIC_SEARCH.md)。

## 未来规划

- [ ] 完善项目文档
- [ ] 开源本项目
- [ ] 从本项目迁移至通用的方言服务包后端

## 许可证

本仓库中由 e-dialect 有权授权的原创软件代码，除另有说明外采用
**GNU Affero General Public License v3.0 only（`AGPL-3.0-only`）**。
AGPL 允许商业使用，但使用者须遵守其全部条款；无法或不希望遵守这些条款的组织，
可以联系维护者了解替代商业许可。数据、词典内容、语料、录音、模型权重、商标、
Logo 和第三方组件不自动适用该许可证。详见 [`LICENSING.md`](LICENSING.md)。
