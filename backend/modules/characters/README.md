# characters 模块

`characters` 是人物系统核心模块。

人物模板、人物包、读写、校验、CLI 和 debug 都围绕本模块管理。

## 目录结构

```text
backend/modules/characters/
  api.py
  service.py
  repository.py
  schemas.py
  pack_loader.py
  pack_writer.py
  validator.py
  templates/
    default_character.json
  packs/
    role01/
      character.json
      voice_refs/
        neutral/
          .gitkeep
      backups/
        .gitkeep
    .trash/
      .gitkeep
```

## 职责

- 列出 active 角色。
- 读取角色详情。
- 创建角色包。
- 更新角色包。
- 安全删除角色到 `.trash`。
- 从 `.trash` 恢复角色。
- 上传并记录角色头像。
- 校验角色包。
- 提供人物 debug 信息。

## 角色包

每个角色一个目录：

```text
backend/modules/characters/packs/{character_id}/
```

`character.json` 是唯一必需文件。

`voice_refs/` 保存本角色语音参考素材。

`backups/` 保存上一版 `character.json`。

旧目录 `backend/data/character_packs` 已废弃。
不要在新代码中恢复旧路径。

## 主要文件

- `repository.py`：统一管理路径。
- `pack_loader.py`：只负责读取角色包。
- `pack_writer.py`：只负责安全写入角色包。
- `validator.py`：只负责校验角色包。
- `service.py`：角色业务逻辑。
- `api.py`：角色相关 FastAPI router。
- `schemas.py`：本模块请求和响应模型。

## CLI

进入后端目录后可以使用：

```powershell
python -m tools.character_pack list
python -m tools.character_pack new asa_mitaka --name "三鹰朝"
python -m tools.character_pack validate asa_mitaka
python -m tools.character_pack delete asa_mitaka
python -m tools.character_pack restore asa_mitaka
```

## 注意事项

- 不允许静默返回默认角色。
- 不允许 fallback 到 mock。
- 写入前必须校验。
- 删除只能移动到 `.trash`。
- `role01` 是默认角色，不应被安全删除接口删除。
