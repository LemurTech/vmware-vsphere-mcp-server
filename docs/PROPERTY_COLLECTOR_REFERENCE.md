---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: ed1583c04d6834655d7f2ac73d06ce7a_2cc18bb77e5f11f1938f5254006c9bbf
    ReservedCode1: +RMiquYt8l8GjMzkJEczzsoy1WMl5c1C3vOj9+1xUyc0jyr8ByHiUJvt5tDNtAAQ4ib2BoSak+n37aFWv81orzbsaC9dvEaHEMskJPEWK/H12261ft0aDbmywqM2V96PB60oNn6A/1wzNm7Ib9udzFxJLStqyIf2AcpQugTeqy6coU2K7KPJDtwzbww=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: ed1583c04d6834655d7f2ac73d06ce7a_2cc18bb77e5f11f1938f5254006c9bbf
    ReservedCode2: +RMiquYt8l8GjMzkJEczzsoy1WMl5c1C3vOj9+1xUyc0jyr8ByHiUJvt5tDNtAAQ4ib2BoSak+n37aFWv81orzbsaC9dvEaHEMskJPEWK/H12261ft0aDbmywqM2V96PB60oNn6A/1wzNm7Ib9udzFxJLStqyIf2AcpQugTeqy6coU2K7KPJDtwzbww=
---

# pyVmomi PropertyCollector 类型速查表

## 核心原则

`config.template` 等嵌套属性路径通过 PropertyCollector 获取时，按 **扁平化键名** 查询，返回的是 Python 原始值（str/bool/int），不是嵌套对象。

## 高频路径速查

| 查询目标 | pathSet | 返回值类型 | 示例返回值 |
|---------|---------|-----------|-----------|
| VM 名称 | `name` | `str` | `"Hermes-Template-v1"` |
| 是否模板 | `config.template` | `bool` | `True` / `False` |
| 电源状态 | `runtime.powerState` | `str` | `"poweredOn"` / `"poweredOff"` |
| vCPU 数量 | `config.hardware.numCPU` | `int` | `4` |
| 内存(MB) | `config.hardware.memoryMB` | `int` | `8192` |
| Guest OS | `config.guestFullName` | `str` | `"Ubuntu Linux (64-bit)"` |
| VM 路径 | `config.files.vmPathName` | `str` | `"[DS1] vm/vm.vmx"` |
| 主机名(简短) | `guest.hostName` | `str` | `"hermes-prod-01"` |
| IP 地址 | `guest.ipAddress` | `str` | `"10.74.139.50"` |
| 硬件版本 | `config.version` | `str` | `"vmx-15"` |
| VM 标注 | `config.annotation` | `str` | `"Production app server"` |

## 集群/主机

| 查询目标 | pathSet | 返回值类型 |
|---------|---------|-----------|
| 集群名称 | `name` | `str` |
| 主机名称 | `name` | `str` |
| 主机连接状态 | `runtime.connectionState` | `str` |
| 主机电源状态 | `runtime.powerState` | `str` |
| 总 CPU(MHz) | `hardware.cpuInfo.hz` | `long` |
| CPU 核心数 | `hardware.cpuInfo.numCpuCores` | `int` |
| 总内存(B) | `hardware.memorySize` | `long` |

## 数据存储

| 查询目标 | pathSet | 返回值类型 |
|---------|---------|-----------|
| 名称 | `name` | `str` |
| 总容量(B) | `summary.capacity` | `long` |
| 可用空间(B) | `summary.freeSpace` | `long` |
| 类型 | `summary.type` | `str` |
| 可访问 | `summary.accessible` | `bool` |

## 网络

| 查询目标 | pathSet | 返回值类型 |
|---------|---------|-----------|
| 网络名称 | `name` | `str` |
| 是否分布式 | `config.distributedVirtualSwitch` 存在性 | `bool` |
| VLAN ID | 需从 name 正则提取 | — |

## 虚拟机设备（网卡）

| 查询目标 | pathSet | 返回值类型 |
|---------|---------|-----------|
| 硬件设备列表 | `config.hardware.device` | `list[VirtualDevice]` |
| NIC MAC 地址 | `macAddress` (on device) | `str` |
| NIC 连接网络 | `backing.deviceName` (on device) | `str` |

## 常见踩坑

### 1. config.template 是 bool 不是嵌套对象
```python
# ✅ 正确
prop_spec = PropertySpec(type=vim.VirtualMachine, pathSet=["name", "config.template"])
# 结果: propSet 中 config.template → True/False

# ❌ 错误（旧版思维）
# 想通过 vm.config.template 访问嵌套对象 → AttributeError
```

### 2. 跨 DC 克隆必须使用目标 DC 的 folder
```python
# ✅ target_folder 必须来自目标 DC
tg_dc = find_datacenter(target_dc_name)
target_folder = get_vm_folder(tg_dc)  # 从目标 DC 已有 VM 反向推断
clone_spec.location = relocate_spec
vm.CloneVM_Task(folder=target_folder, name=vm_name, spec=clone_spec)
```

### 3. NetworkMap 必须传端口组名称而非 MoRef
```python
# ✅ VirtualEthernetCardNetworkBackingInfo.deviceName = "VLAN-1306"
# ❌ 直接用 MoRef 对象
```

### 4. 查找模板必须加 config.template 过滤
PropertyCollector 返回所有 VM，需用 `config.template == True` 筛选模板。

## 版本要求

pyVmomi >= 8.0 支持 `clone_spec.folder`、`VirtualMachineRelocateSpecNetworkMap` 等新属性。
当前项目使用 **pyVmomi 9.1.0.0**，所有标准 API 均可用。
*（内容由AI生成，仅供参考）*
