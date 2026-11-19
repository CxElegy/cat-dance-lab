# cat-dance-lab

- 任务说明 `TASK_model-attribution-survey.md` 和工作流 README 原文还没进仓库（由用户上传）
- `data/samples.csv`：278 条样本，含 is_ai / is_cat_dance / model / model_evidence / confidence
- `data/raw/`：vidIQ 原始结果（11-17 原始搜索转录为 TSV，11-19 两次补样原文）
- `data/visual_evidence.json`：封面水印和逐帧检查的结论
- `data/credit_log.csv`：vidIQ 额度记账
- `scripts/`：`parse_vidiq.py` → `labels.py`（人工标注）→ `build_samples.py` → `build_dashboard.py`
- `output/findings.md`：一页结论
- `output/dashboard.html`、`output/thumbs/`：含第三方封面，已加入 gitignore，只私下分享

重建：`python3 scripts/build_samples.py && python3 scripts/build_dashboard.py`
