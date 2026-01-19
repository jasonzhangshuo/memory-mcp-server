# 锁屏状态下的同步说明

## ✅ 可以同步

**好消息**：macOS 的 LaunchAgent 在**锁屏状态下也可以执行**！

## 🔍 工作原理

### LaunchAgent vs LaunchDaemon

- **LaunchAgent**（我们使用的）：
  - ✅ 用户登录状态下运行（包括锁屏）
  - ✅ 可以访问用户环境变量
  - ✅ 可以访问用户文件
  - ✅ **锁屏时仍然可以执行**

- **LaunchDaemon**（系统级）：
  - 需要 root 权限
  - 即使没有用户登录也能运行
  - 我们不需要这个

## 📋 执行条件

定时任务会在以下情况下执行：

1. ✅ **电脑开机**
2. ✅ **用户已登录**（即使锁屏也可以）
3. ✅ **到达指定时间**（23:30）

## ⚠️ 不会执行的情况

1. ❌ 电脑关机或休眠
2. ❌ 用户未登录（完全退出登录）
3. ❌ 系统时间未到达 23:30

## 🧪 验证方法

### 方法 1: 查看日志

第二天早上查看日志文件，确认是否执行：

```bash
tail -20 memory-mcp-server/sync.log
```

### 方法 2: 手动测试

可以临时修改时间为 23:30 后几分钟，然后锁屏测试：

```bash
# 修改 plist 文件中的时间为当前时间后几分钟
# 然后重新加载任务
launchctl unload ~/Library/LaunchAgents/com.jason.memory-sync.feishu.plist
launchctl load ~/Library/LaunchAgents/com.jason.memory-sync.feishu.plist
```

## 💡 建议

1. **保持电脑开机**：如果电脑经常关机，可以考虑使用云服务器
2. **检查日志**：定期查看日志确认同步是否正常
3. **网络连接**：确保电脑有网络连接（WiFi 或以太网）

## 📝 当前配置

- **ProcessType**: Background（后台进程）
- **RunAtLoad**: false（不在加载时运行，只在指定时间运行）
- **KeepAlive**: false（不保持常驻，执行完就退出）

这个配置确保了任务在锁屏状态下也能正常执行。
