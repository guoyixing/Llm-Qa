# 每日代码审查报告

## 用户与范围

- 用户：邹宇宸（zouyuchen）
- 时区：`Asia/Hong_Kong`
- 审查窗口：`[2026-07-17 00:00:00, 2026-07-20 00:00:00)`
- 实际过滤条件：`date-range=2026-07-17,2026-07-19`；未指定项目、提交、分支、文件或目录过滤

## 注册表快照

- 路径：`project-registry.yaml`
- 版本：`1`
- 快照摘要：`dade0daa14f9c931cbc8e3ab019bdf1947229a8853edb7337ffb877657016348`
- 生效项目：`hisense-ids-app`，名称“海信 IDS 应用”，代码目录 `data/code/hisense-ids-app`，规范目录 `standards/projects/hisense-ids-app`，默认分支 `projectDevGroup`，配置键名 `PROJECT_HISENSE_IDS_APP_REPO_URL`
- 生效项目：`hisense-ids-app-spec`，名称“海信 IDS 应用-结构化分支”，代码目录 `data/code/hisense-ids-app-spec`，规范目录 `standards/projects/hisense-ids-app-spec`，默认分支 `projectDevGroup-specTemplate`，配置键名 `PROJECT_HISENSE_IDS_APP_SPEC_REPO_URL`
- 注册表条目错误：无

## 项目来源与提交

### hisense-ids-app

- 本次直接同步结果：成功，仅快进同步
- 固定来源提交：`9832cb65de32cb08115cd34844ef480ed1209c4a`
- 实际审查提交（34）：`d57ca1d425b928de9094bed2f33d018fe46d3d4e`、`b849332e34799dda5c6840cf3ef37cac0247d432`、`5a99bbcc20831484bb0805bff7d3fc026bcf991a`、`e33d3d86fc62ae05ed153858fe302f4ca01a225a`、`e628acd71107c0a9c3144922732a1c95e5b24606`、`8eb4e680cc4589c8fb4faf00f109efab172ecdf5`、`dad3b81ddbdc82af17b8c1c26fc70dc317a397b8`、`cb0cb9ba45efe2437eb27b11c9be398eb308988f`、`6ed692ec4dd9324e7ba9bb526fe49779a29bc130`、`d26885ee774e601f1c137c3d6308d0288a611b7d`、`71b6887ca705fe9cb0aea4773df7ba973634fe58`、`678c70da7f71a787b410b3f499fab894986d3e6b`、`f2d2fc33a2e3fee1aec6e8e695d5f392c105751b`、`7bb4c3b602acbe29f047eea9ea08b7d64e6489d4`、`7b4348ad5fd59d3670c87eabf9616e84352f256b`、`2e9f5a718de3142205439d0d73b7727b4e2fb5c4`、`2abb4d992ebc4c72412d22bf833c25c0a7c14c84`、`dd1908e810635edf8cbb5f568875c43c362060b0`、`dd79bd55a94a74e3ed44db555569d85c58c3481d`、`efbef927a8326608301fe439ece610a51427f51e`、`e44b655c1030e373e3ecd5a16dd5540e758308e0`、`d1dbf8f8b9ab2a058f4411be00c988da7e73d28b`、`cd0fcd327726bc7f56770442d88bb641db39bc8b`、`3c1a2d7e0f23b5f9b3c7856e72f99be613bceaf0`、`a08f4fc5ff663c443be41434b3ad394fc5d0144c`、`25072e99beed029a98132150e8fcbd62dc15ada6`、`75b2a5e25b5f30e5fc8f1fea826fe6815e55a39a`、`bc819470ca05e68d025d17065e290a4ed9a5d244`、`ae53f756a9d25038b17f2e1a5cac6e6878319050`、`575dacd8d830e27f59b558b64c123c4a18a878fe`、`5d089bb609c8c40554c5623fd91344603a83bbe5`、`f0b388feb170c8624122f3066e5e1b559779860c`、`bc16e80a4d51babd5eb3e5bb32db91f04cab2262`、`c038a57ee4f36847774a9d84d9c986e35437213c`

### hisense-ids-app-spec

- 本次直接同步结果：成功，仓库已是最新状态
- 固定来源提交：`7487243ec8a1fdb084ba538a685fe74f56d0a044`
- 该用户在范围内无提交

## 规范加载与失败

- 公共规范 `standards/common/` 的代码规范、可读性、健壮性和性能规则均已加载。
- `hisense-ids-app` 项目规范已加载，未发现覆盖冲突。
- 配置失败：`hisense-ids-app-spec` 的三个项目规范文件声明了错误的适用项目和规则标签；本次仅对该项目应用公共规则。该用户在此项目无范围内提交，因此不影响其发现判断。
- 身份解析失败：无；未归属提交：无。
- 同步失败：无；报告生成失败：无。

## 汇总

- 实际审查项目数：1
- 实际审查提交数：34
- 代码规范发现：0
- 可读性发现：0
- 健壮性发现：1
- 性能发现：1
- 严重级别：`HIGH` 1 条，`MEDIUM` 1 条
- 流程失败数：1 个项目规范配置降级

## 发现

### HIGH：并行数据库查询使用无界等待

- 项目：`hisense-ids-app`
- 提交：`7b4348ad5fd59d3670c87eabf9616e84352f256b`
- 类别：健壮性
- 严重级别：`HIGH`
- 文件与行范围：`hisense-app/src/main/java/com/glaway/masterdata/service/impl/MasterDataClassServiceImpl.java:85-184`
- 规则或代码证据：公共规则 `ROBUST-003`。分类查询提交到线程池后，主线程通过 `awaitLatchQuietly` 调用无超时的 `CountDownLatch.await()`；主数据查询异常路径也会先执行同一无界等待。
- 问题说明：只要子任务中的数据库调用、连接获取或驱动调用不返回，主请求就没有可证明的终止条件。中断处理只能响应外部中断，不能限制正常等待时长。
- 影响：请求线程可能永久占用，持续消耗数据库连接和线程池容量；并发触发时会放大为线程耗尽和级联超时。
- 建议：使用统一截止时间的 `await(timeout, unit)` 或可取消的 `Future`；超时后取消子任务、恢复中断语义，并返回明确的失败或未完成状态。

### MEDIUM：属性表连接缺少活动行约束，可能放大分页结果

- 项目：`hisense-ids-app`
- 提交：`3c1a2d7e0f23b5f9b3c7856e72f99be613bceaf0`
- 类别：性能
- 严重级别：`MEDIUM`
- 文件与行范围：`hisense-app/src/main/resources/META-INF/sql/master_data.sql.xml:703-744`
- 规则或代码证据：`getChildMDDataById` 新增的三个 `T_IBA_STRING_VALUE` 连接仅按 `instanceid + attrcode` 匹配；相邻的主数据和关联表都显式过滤 `deleteFlag = 0`，但 `pg00001`、`mdid`、`pg00061` 三个别名没有活动行过滤或唯一化处理。
- 问题说明：当同一实例和属性编码存在历史、软删除或重复记录时，一个主数据行会被多个属性行笛卡尔式展开，`ROW_NUMBER` 和分页是在展开后计算。
- 影响：结果行数、排序和分页边界可能失真，查询和网络开销随重复属性行乘法增长；多属性同时重复时放大更明显。
- 建议：在每个属性连接中加入项目一致的活动行条件，或先按 `instanceid + attrcode` 选出唯一有效记录再连接，并确保相应复合索引覆盖过滤条件。

## 结论

本次对该用户的 34 个提交完成四类只读静态审查，发现 1 条 `HIGH` 健壮性问题和 1 条 `MEDIUM` 性能问题。项目规范配置另有 1 项与该用户提交无关的降级。
