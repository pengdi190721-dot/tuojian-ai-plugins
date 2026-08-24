#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { basename, extname, join, resolve } from "node:path";
import { mkdirSync, renameSync, writeFileSync } from "node:fs";

const TRANSCRIBER_PACKAGE = "@coroboros/scrybe@0.2.0";

function optionValue(args, name, fallback = undefined) {
  const index = args.indexOf(name);
  return index >= 0 && index + 1 < args.length ? args[index + 1] : fallback;
}

const args = process.argv.slice(2);
const input = args[0];
if (!input) {
  process.stderr.write("缺少待转写音频。\n");
  process.exit(2);
}

const outputDir = resolve(optionValue(args, "--output_dir", "."));
const model = optionValue(args, "--model", "base");
const language = optionValue(args, "--language", "zh");
mkdirSync(outputDir, { recursive: true });

const command = [
  "-y",
  TRANSCRIBER_PACKAGE,
  resolve(input),
  "--model",
  model,
  "--lang",
  language,
  "--json",
  "--out-dir",
  outputDir,
  "--force",
  "--no-color",
];
const completed = spawnSync("npx", command, {
  encoding: "utf8",
  env: { ...process.env, OPENAI_API_KEY: "" },
  maxBuffer: 20 * 1024 * 1024,
});

if (completed.error) {
  process.stderr.write(`本地语音识别无法启动：${completed.error.message}\n`);
  process.exit(1);
}
if (completed.status !== 0) {
  process.stderr.write(completed.stderr || "本地语音识别没有完成。\n");
  process.exit(completed.status || 1);
}

let payload;
try {
  payload = JSON.parse(completed.stdout);
} catch {
  process.stderr.write("本地语音识别结果格式异常。\n");
  process.exit(1);
}

const stem = basename(input, extname(input));
const outputPath = join(outputDir, `${stem}.json`);
const temporaryPath = `${outputPath}.${process.pid}.tmp`;
writeFileSync(temporaryPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
renameSync(temporaryPath, outputPath);
process.stdout.write("本地语音识别完成。\n");
