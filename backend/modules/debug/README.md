# debug 模块

`debug` 模块负责提供开发和排错用接口。

## 职责

- 暴露人物系统 debug 信息。
- 汇总 active 和 trash 角色状态。
- 帮助定位角色包缺失、JSON 错误和校验错误。

## 主要接口

```text
GET /debug/characters
GET /debug/characters/{character_id}
```

## 边界

debug 接口只展示状态，不应修改业务数据。

如果需要修复人物包，应通过 characters 模块或 CLI 操作。

## 注意事项

- 不要在 debug 接口里写文件。
- 不要隐藏校验错误。
- 不要输出敏感环境变量。
