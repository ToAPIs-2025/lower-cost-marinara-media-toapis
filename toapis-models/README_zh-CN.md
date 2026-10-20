# 独立图片／视频多模型脚本

[English](README.md) · [中文](README_zh-CN.md)

报价核对：2026-10-20。图片案例日期2026-10-17；视频案例日期2026-10-20。表格按本例金额／秒金额排序，质量、分辨率和输入不同，不是同配置质量排名。图片日志的阶段未知，不能当作单任务最终净结算；当前报价与历史金额分别显示。视频金额均由billing=settled确认，$/s按实际文件时长折算，任务处理耗时不参与计算。Token模型不是固定每秒价，底层$/M只作小字补充。

gpt-image-2(VIP)通用价格为$0.0019/image起；本例low/1K为$0.0019/image。新脚本有31套历史成功图片请求模板、8套视频模板；当前26套图片与8套视频可匹配价格，另5套图片因当前Key缺价而默认阻止新付费调用。

这里的新增支持属于独立API脚本，不自动注册为上游产品的原生Provider，也不扩大原项目的验收结论。

```powershell
$env:TOAPIS_API_KEY="your_private_generation_key"
python unified_client.py --model gpt-image-2-vip --prompt "A tiny red robot beside a harbor kiosk"
python unified_client.py --model gpt-image-2-vip --prompt "A tiny red robot beside a harbor kiosk" --live
python unified_client.py --model MiniMax-H3-Max-Turbo --prompt "A tiny red robot walks slowly beside a harbor kiosk" --max-usd 1.50 --live
python unified_client.py --model seedance-2-mini --prompt "A gentle camera push-in" --image first-frame.png --max-usd 1.50 --live
```

不加--live仅查当前Key价格；首次付费前检查同档位报价。图片默认估算门槛$0.20，视频$1.50；这是客户端估算检查，不是托管账户的硬消费限制。Token费用可波动，保留预算余量。脚本在POST前保存记录，未知提交不自动重试，使用相同run-id恢复原任务；更换run-id会创建新付费任务。只用生成Key，不读取账户凭证或余额。结果下载不携带Key。

标准库即可运行。先进入本文件所在目录；Key通过环境变量配置，.env.example只是占位示例，不自动加载。请求档位固定在presets.json，不透传不支持的参数。仅文生图；视频按各档位限制使用文生视频或单PNG首帧。

[Full current rates and real cases](https://github.com/ToAPIs-2025/toapis-quickstart/tree/main/tutorials/model-support-2026-10-20) · [Pricing API](https://docs.toapis.com/docs/en/api-reference/account/pricing)
