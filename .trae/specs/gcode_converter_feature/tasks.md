# G代码转换器功能增强 - 实现计划

## [x] Task 1: 修改NaturalLanguageInput组件 - 实时显示已输入和缺失参数

* **Priority**: P0

* **Depends On**: None

* **Description**:

  * 在NaturalLanguageInput.vue中添加参数实时解析功能

  * 显示已满足的参数列表（绿色）

  * 显示缺失的参数列表（红色）

  * 使用本地解析逻辑，无需调用后端

* **Acceptance Criteria Addressed**: \[AC-1]

* **Test Requirements**:

  * `human-judgement` TR-1.1: 输入部分参数后，应正确显示已满足和缺失的参数列表

  * `human-judgement` TR-1.2: 参数状态应在输入时实时更新

## [x] Task 2: 创建独立的G代码显示弹窗组件

* **Priority**: P0

* **Depends On**: None

* **Description**:

  * 创建GCodeModal.vue组件

  * 显示生成的G代码内容

  * 提供复制功能

  * 提供跳转到验证网页的按钮

* **Acceptance Criteria Addressed**: \[AC-2, AC-4]

* **Test Requirements**:

  * `human-judgement` TR-2.1: G代码应在独立弹窗中显示

  * `human-judgement` TR-2.2: 点击验证按钮应在新标签页打开验证网页

## [x] Task 3: 创建独立的工序信息显示弹窗组件

* **Priority**: P0

* **Depends On**: None

* **Description**:

  * 创建ProcessCardModal.vue组件

  * 显示工序卡基本信息

  * 显示刀具信息

  * 显示操作步骤表格

* **Acceptance Criteria Addressed**: \[AC-3]

* **Test Requirements**:

  * `human-judgement` TR-3.1: 工序信息应在独立弹窗中显示

  * `human-judgement` TR-3.2: 弹窗应支持独立关闭

## [x] Task 4: 修改App.vue - 调用两个独立弹窗

* **Priority**: P1

* **Depends On**: Task 2, Task 3

* **Description**:

  * 修改App.vue中处理转换结果的逻辑

  * 移除DualPanel组件的使用

  * 分别打开GCodeModal和ProcessCardModal两个弹窗

* **Acceptance Criteria Addressed**: \[AC-2, AC-3]

* **Test Requirements**:

  * `human-judgement` TR-4.1: 生成G代码后应同时打开两个独立窗口

  * `human-judgement` TR-4.2: 两个窗口应可以独立关闭

## [x] Task 5: 更新后端API - 添加参数预检查接口

* **Priority**: P1

* **Depends On**: None

* **Description**:

  * 在natural\_language.py中添加预检查接口

  * 返回已提取的参数和缺失的参数

  * 不生成G代码，仅做参数检查

* **Acceptance Criteria Addressed**: \[AC-1]

* **Test Requirements**:

  * `human-judgement` TR-5.1: 调用预检查接口应返回已提取和缺失的参数列表

