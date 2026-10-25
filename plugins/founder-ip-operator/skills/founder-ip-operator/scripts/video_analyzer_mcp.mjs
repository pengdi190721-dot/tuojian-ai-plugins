#!/usr/bin/env node

import { spawn } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const PACKAGE = "mcp-video-analyzer@0.10.0";
const scriptDir = dirname(fileURLToPath(import.meta.url));
const bridge = join(
  scriptDir,
  process.platform === "win32" ? "whisper_bridge.cmd" : "whisper_bridge.mjs",
);
const environment = { ...process.env };
environment.OPENAI_API_KEY = "";
delete environment.WHISPER_HF_MODEL;
environment.WHISPER_BIN = bridge;
environment.WHISPER_MODEL = "base";
environment.WHISPER_LANGUAGE = environment.WHISPER_LANGUAGE || "zh";
environment.MCP_WRITE_SIDECARS = environment.MCP_WRITE_SIDECARS || "0";

const child = spawn("npx", ["-y", PACKAGE], {
  stdio: "inherit",
  env: environment,
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => child.kill(signal));
}
child.on("error", (error) => {
  process.stderr.write(`视频解析服务无法启动：${error.message}\n`);
  process.exit(1);
});
child.on("exit", (code, signal) => {
  process.exit(code ?? (signal ? 1 : 0));
});
