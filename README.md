# 兴化语记（后端）

## 项目简介

兴化语记是 [E方言](https://edialect.top) 中`莆仙方言公共服务包` 的别称，主要服务对象包括福建省莆田市及其周边地区的莆仙方言使用者。

兴化语记目前包括网页端 ( https://pxm.edialect.top , https://hinghwa.cn )，微信小程序端（兴化语记），计划在本项目中通过 `uni-app` 增加移动端 ( https://m.pxm.edialect.top )，QQ小程序端等。

## 技术栈

> 项目采取前后端分离架构，其他的前端仓库可前往 https://github.com/e-dialect 进行寻找

采用 `Django` 框架提供网站访问服务，其他所依赖库可见 [requirementes.txt](./hinghwa-dict-backend/requirements.txt) 。

为方便项目部署，我们也通过 `docker` 将整个服务制作成镜像，以便 `Traefik` 将流量转发至容器内部。

## 未来规划

- [ ] 完善项目文档
- [ ] 开源本项目
- [ ] 从本项目迁移至通用的方言服务包后端