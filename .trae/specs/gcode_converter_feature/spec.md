# G代码转换器功能增强 - 产品需求文档

## Overview
- **Summary**: 对现有的自然语言转换组件进行功能增强，包括：1) 在生成G代码前显示已输入和缺失的参数；2) 将G代码和工序信息显示在独立窗口；3) 添加G代码在线验证功能。
- **Purpose**: 提升用户体验，让用户在生成G代码前能清晰了解参数完整性，并提供更好的结果展示和验证方式。
- **Target Users**: 机加工编程人员

## Goals
- 在自然语言转换组件中，用户输入后能实时看到已满足的参数和缺失的参数
- 生成G代码后，G代码和工序信息在两个独立窗口显示
- 提供跳转到外部网页验证G代码的功能

## Non-Goals (Out of Scope)
- 修改后端参数提取逻辑
- 添加新的参数类型
- 修改G代码生成算法

## Background & Context
当前系统已实现自然语言转G代码的核心功能，但用户反馈需要更清晰的参数状态展示和更好的结果呈现方式。

## Functional Requirements
- **FR-1**: 自然语言转换组件应显示已输入的参数列表（已满足的参数）
- **FR-2**: 自然语言转换组件应显示未输入的参数列表（缺失的参数）
- **FR-3**: G代码和工序信息应在两个独立的弹窗窗口中显示
- **FR-4**: 提供跳转到G代码验证网页的功能

## Non-Functional Requirements
- **NFR-1**: 参数检查应在前端实时进行，无需调用后端
- **NFR-2**: 弹窗窗口应支持独立关闭和拖拽
- **NFR-3**: 响应时间小于1秒

## Constraints
- **Technical**: 使用Vue3 + Vite框架，Tailwind CSS样式
- **Dependencies**: 后端API保持不变

## Assumptions
- 用户会在输入自然语言后，先查看参数状态再点击生成按钮
- 用户需要外部G代码验证工具链接

## Acceptance Criteria

### AC-1: 显示已输入和缺失的参数
- **Given**: 用户在自然语言转换组件中输入了部分参数
- **When**: 用户未点击生成按钮时
- **Then**: 组件应显示两个列表：已满足的参数和缺失的参数
- **Verification**: `human-judgment`

### AC-2: 生成后G代码在独立窗口显示
- **Given**: 用户成功生成G代码
- **When**: 转换完成后
- **Then**: G代码应在一个独立的弹窗窗口中显示
- **Verification**: `human-judgment`

### AC-3: 生成后工序信息在独立窗口显示
- **Given**: 用户成功生成G代码
- **When**: 转换完成后
- **Then**: 工序信息应在另一个独立的弹窗窗口中显示
- **Verification**: `human-judgment`

### AC-4: 跳转到G代码验证网页
- **Given**: G代码已生成并显示
- **When**: 用户点击验证按钮
- **Then**: 应在新标签页打开G代码验证网页
- **Verification**: `human-judgment`

## Open Questions
- [ ] 具体使用哪个G代码验证网页？（默认使用常见的在线G代码查看器）