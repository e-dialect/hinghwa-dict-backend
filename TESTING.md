## 测试说明

### 原则

理论上的测试类型包括：

- 单元测试（Unit test）
- 集成测试（Integration test）
- 端到端测试（End-to-End test, e2e test）

然而在这个项目中，由于时间精力和函数的实际复杂程度，我们直接使用端到端测试检验函数的正确性。（正常来说，应该是金字塔模型： 底部是单元测试，中间是集成测试，最上层是端到端测试）

一个功能的上线要经过下列流程：

- 发起 Pull Request 提交代码（具体见 [CONTRIBUTING.md](CONTRIBUTING.md) ）
- 运行 [CI](./.github/workflows) 进行 `Github Actions` 进行一些相应的检查
- 部署到测试服务器进行测试
- 上线服务至正式服务器

### CI

CI，（*Continuous Integration*，持续集成），是一个可以帮助我们控制代码质量的好方法。

在本项目目前的 CI 包括：

- e2e：运行 [`tests`](./tests) 文件夹中的 `Apifox` 自动化测试脚本进行端到端测试
- lint：通过 `blank` 进行代码格式化检查

在运行端到端测试时，在会通过以下命令创建初始数据库：


```shell
python3 manage.py makemigrations
python3 manage.py migrate
DJANGO_SUPERUSER_PASSWORD=testtest123 python manage.py createsuperuser --username admin --email test@test.com --no-input
DJANGO_SUPERUSER_PASSWORD=testtest222 python manage.py createsuperuser --username admin2 --email test@test.com --no-input
curl 127.0.0.1:8000/users/1
curl 127.0.0.1:8000/users/2
```

> 创建两个用户的原因是在目前的代码中，发送邮件默认是由2号用户进行发送。
>
> 获取用户详细信息的原因是：直接创建的用户只有 Django 默认的用户模型，不包括我们自定义的 `UserInfo` 模型，在获取用户模块中实现了自动创建功能，否则在其他模块调用时会出错。

#### Apifox 自动化测试

- 在 `Apifox` - `自动化测试` - `测试用例` 中添加相应的测试用例或测试套件。
- 选择 `测试环境` 导出 `Apifox CLI` 格式的 `json` 源文件，格式化后放入 `tests` 文件夹即可。
- 测试套件或测试用例可以自己根据需要进行组合、拼装。
