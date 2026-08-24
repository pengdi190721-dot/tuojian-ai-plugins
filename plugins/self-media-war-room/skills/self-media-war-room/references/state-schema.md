# 状态文件

跨项目定位保存为 `.self-media-creator-profile.json`，格式由 `creator-positioning` 管理。每条内容任务另在项目目录保存 `.self-media-job.json`：

```json
{
  "schema_version": 3,
  "title": "项目名称",
  "current_stage": "positioning",
  "stages": {
    "positioning": "in_progress",
    "setup": "pending",
    "topic": "pending",
    "benchmark": "skipped",
    "research": "pending",
    "persona": "pending",
    "script": "pending",
    "production": "pending",
    "review": "pending"
  },
  "artifacts": {},
  "assumptions": [],
  "open_questions": []
}
```

使用 `../../scripts/job_state.py` 新建、读取或更新。没有对标视频时，`benchmark` 保持 `skipped`；收到对标视频后改为 `in_progress`，完成对标卡和原创映射后标记为 `completed`。定位完成后，把档案路径记录为 `creator_profile` 交付物并将 `positioning` 标记为完成。不要覆盖用户已有的同名文件；新建前先检查。
