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

# 依赖要求
requirements = python3,kivy==2.1.0,pillow

# Android配置
android.api = 31
android.minapi = 21
android.archs = arm64-v8a,armeabi-v7a

# 权限
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# 打包
android.accept_sdk_license = True

# 日志级别
log_level = 2
