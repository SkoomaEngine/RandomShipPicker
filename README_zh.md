# Random Ship Picker（随机选船）

[English](README.md)

《战舰世界》客户端 mod。在港口筛选栏加一个"随机"按钮，从**当前筛选结果**里等概率随机选一艘船，选中后船坞自动滚到这艘船。

用纯 UI 实现：只有一个 ModForge 蓝图（`RSP_RandomShipPicker.xml`），不含可执行程序和 Python。它不改动 Unbound 2 船坞，可以和 Aslain 整合包、Port Interface 共存。

当前版本：1.0.0，已在客户端 15.9.0（亚服）上测试。

## 玩家

到 [Releases](../../releases) 下载压缩包。安装、使用方法和须知见 [release/README_zh.md](release/README_zh.md)。

要点：

- 需要 ModForge。Aslain 整合包会安装它。
- 每次选中后，mod 会短暂切换"隐藏不符合筛选的船"，约 0.15 秒后改回原值，船坞就是靠这一下滚过去的。
- 只认游戏自带的筛选，其他 mod 在船坞里另加的筛选它看不到。

## 目录

| 路径 | 内容 |
|---|---|
| `mod/res_mods/ForgeBlueprints/RSP_RandomShipPicker.xml` | mod 本体 |
| `release/` | 随发布包附带的英文/中文说明和 CHANGELOG |
| `tools/forge_check.py` | 离线运行游戏里安装的 ModForge，对蓝图做合并、检查和编译，结论与 ModForge 在游戏启动时相同 |
| `tools/deploy.py` | 把 `mod/res_mods/` 复制进游戏；`--remove` 撤回，`--dry-run` 只预览 |
| `tools/checklog.py` | 从 `profile/python.log` 摘出本 mod 的 ModForge 记录、运行汇总和 AS3 报错 |
| `tools/package.py` | 打发布包 `dist/RandomShipPicker-<版本>.zip`，另出一个只含 `res_mods` 的 `-res_mods-only` 包供 Aslain 自定义 mod 使用：先跑 `forge_check`，并核对 CHANGELOG 里有当前版本 |
| `docs/v1-test.md` | 1.0.0 的实机测试步骤 |
| `probe/` | 开发期间用来实测船坞行为的诊断探针及其测试说明。已退役，工具不会部署它 |

## 开发

需要 Python 3，以及装有 ModForge 的《战舰世界》。在仓库根目录运行：

```text
python tools/forge_check.py          # 部署前检查：会不会被 ModForge 拒装
python tools/deploy.py --dry-run     # 预览要复制哪些文件
python tools/deploy.py               # 部署（下次启动游戏时生效）
python tools/deploy.py --remove      # 撤回（下次启动时 ModForge 自动还原）
python tools/checklog.py             # 查看最近一次启动的日志摘要
python tools/package.py              # 打发布包到 dist/
```

工具会在 Steam 和 Wargaming Game Center 的常见安装位置找游戏。装在别处时，用 `--game` 或环境变量 `WOWS_DIR` 指定；用 `--build` 可以指定 `bin\` 下的某个版本目录，默认取最新的。

`deploy.py` 只会写入或删除 `mod/res_mods/` 里有的文件，以及已退役的探针蓝图 `RSP_Probe.xml`。`forge_check.py` 只读取游戏目录。

## 许可证

[MIT](LICENSE)
