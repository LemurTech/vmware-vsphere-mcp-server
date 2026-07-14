---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: ed1583c04d6834655d7f2ac73d06ce7a_2d2f50287e5f11f1baf4525400bff409
    ReservedCode1: euHmbURLdvHJaI8iIT2dIytxBKlo+SHQy2/5+DvGOab/hfKy2nTZZPFHJD2BUfxxQsCZIaFE7A4GpjtRK9GWdT3ZpWIFRaMrB/0BC4j/XjvPm+6qR9PRGdvcDFfM6uaTWXDFB4oqSfFjSPieBCZhnvLh/E1RQoWUEryV9DfVR6RfsA741cTie/TkCYE=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: ed1583c04d6834655d7f2ac73d06ce7a_2d2f50287e5f11f1baf4525400bff409
    ReservedCode2: euHmbURLdvHJaI8iIT2dIytxBKlo+SHQy2/5+DvGOab/hfKy2nTZZPFHJD2BUfxxQsCZIaFE7A4GpjtRK9GWdT3ZpWIFRaMrB/0BC4j/XjvPm+6qR9PRGdvcDFfM6uaTWXDFB4oqSfFjSPieBCZhnvLh/E1RQoWUEryV9DfVR6RfsA741cTie/TkCYE=
---

# Hermes VM 克隆 — 踩坑与最佳实践

> 基于 2026-07 月 28 轮迭代的完整经验沉淀。
> 目标：从 Ubuntu 模板克隆 VM 到指定集群，横跨双数据中心。

## 环境信息

| 项 | 值 |
|---|-----|
| vCenter | 10.74.139.100 |
| 账户 | aiops-readonly@vsphere.local |
| 模板 | Ubuntu 模板（datacenter-3） |
| 目标集群 | UAT-G01-H3C-R4900G3-5220R-AFVSAN（datacenter-70700） |
| 目标 Datastore | HZHQDC02-vsanDatastore-UAT-G01 |
| pyVmomi 版本 | 9.1.0.0 |

## 6 阶段踩坑全景

### 阶段 1: 环境确认（2 轮）
- pyvmomi 版本太老（6.x），缺少 `clone_spec.folder`、NetworkMap 等 API
- **解决**: 升级到 pyvmomi 9.1.0.0

### 阶段 2: 模板检索（7 轮）
- **核心踩坑**: PropertyCollector 中 `config.template` 返回 `bool` 而非嵌套对象
- 旧代码用 `vm.config.template` 访问 → AttributeError
- 前 6 轮因对返回类型认知错误而找不到模板
- **解决**: pathSet 中使用 `"config.template"` 扁平键名，返回 True/False

### 阶段 3: 集群/存储定位（1 轮）
- 集群在 datacenter-70700，需先定位目标 DC
- Datastore 名含下划线，需精确匹配

### 阶段 4: 克隆目标路径排查（8 轮）
- **核心踩坑**: 模板在 datacenter-3，目标集群在 datacenter-70700
- 跨 DC 克隆时 `folder` 必须来自目标 DC
- **解决**: 从目标 DC 已有 VM 反向提取父文件夹作为 Clone 目标

### 阶段 5: 网络绑定失败（多轮）
- 旧 pyvmomi 缺少 `VirtualMachineRelocateSpecNetworkMap`
- 尝试多种方案（MoRef 直接绑定、deviceChange）均失败
- **终局**: 依赖模板默认网络 + pyvmomi 9.x 的 deviceChange 机制

### 阶段 6: 最终执行
- 成功脚本: `clone_v15.py`（已固化为 MCP 工具 `clone_vm`）
- 使用 vim.vm.RelocateSpec + vim.vm.CloneSpec 标准路径

## 最佳实践清单

1. **始终升级 pyvmomi** → 版本 >= 8.0 解锁完整 API
2. **PropertyCollector 扁平化查询** → 见 `PROPERTY_COLLECTOR_REFERENCE.md`
3. **跨 DC 克隆三段式**:
   ```
   ① 找到模板所在 VM 对象（source DC）
   ② 在目标 DC 定位 cluster / datastore / folder
   ③ 用目标 DC 的 folder 作为 CloneVM_Task 的目标
   ```
4. **网络绑定用 deviceChange** → 遍历模板 NIC，逐个映射到目标网络
5. **Folder 反推策略** → `target_dc.vmFolder` 作为兜底
6. **Task 轮询超时** → 600s 超时 + 3s 间隔

## 等效 MCP 调用

```python
# 步骤 1: 查找模板
find_template_pyvmomi(name="ubuntu", datacenter="datacenter-3")

# 步骤 2: 确认目标环境
list_clusters_pyvmomi(datacenter="datacenter-70700")
list_datastores()  # 找到 HZHQDC02-vsanDatastore-UAT-G01

# 步骤 3: 执行克隆
clone_vm(
    template_name="Ubuntu-Template",
    vm_name="hermes-new-vm-01",
    cluster_name="UAT-G01-H3C-R4900G3-5220R-AFVSAN",
    datastore_name="HZHQDC02-vsanDatastore-UAT-G01",
    target_datacenter="datacenter-70700",
    cpu_count=4,
    memory_gb=8,
    network_name="v1306-MEL03",
    confirm=True
)
```
*（内容由AI生成，仅供参考）*
