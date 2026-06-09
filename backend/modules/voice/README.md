# voice 模块

`voice` 负责 GPT-SoVITS 语音调用。

## 参考音频

`neutral` 是默认语音参考。没有明确选择 emotion 时使用 `neutral`。

用户明确选择 `angry`、`sad`、`happy` 等 emotion 时，必须存在该 emotion 的参考音频：

```text
backend/modules/characters/packs/{character_id}/voice_refs/{emotion}/ref_001.wav
```

缺少参考音频时直接报错，错误会说明 `character_id`、`emotion` 和 `ref_audio_path`。不会退回 `neutral`。

GPT-SoVITS 的 `prompt_text` 可以为空；缺少 `ref_001.txt` 时传空字符串。
