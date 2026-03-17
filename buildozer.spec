[app]

# 应用名称
title = CardMem
package.name = cardmem
package.domain = org.cardmem

# 版本
version = 1.0.0

# 源码
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json

# 主入口
main.py = main.py

# 依赖要求 - 使用更兼容的版本
requirements = python3,kivy,pillow

# Android配置 - 简化架构
android.api = 31
android.minapi = 21
android.archs = armeabi-v7a

# 权限
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# 打包
android.accept_sdk_license = True

# 日志级别
log_level = 2
