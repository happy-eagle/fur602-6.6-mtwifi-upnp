# HONOR FUR-602 · ImmortalWrt 6.6 + 闭源 mtwifi + UPnP 云编译

基于 `padavanonly/immortalwrt-mt798x-6.6` 的 `openwrt-24.10-6.6` 分支（内核 6.6，
闭源 `kmod-mt_wifi`），设备 `mediatek/filogic` · `honor_fur-602`。
**插件策略：基本系统 + UPnP，不加任何代理与重型插件；ttyd 保留。**
源码固定到 Run #3 成功构建时使用的上游 commit，见「源码 commit 固定」。

## 一、插件清单（已确认）

- 基准（沿用 6.6 FUR-602 参考配置，清理后 141 个 `CONFIG_PACKAGE_` 符号）：
  硬件 NAT/WED/BBR/fullcone、TurboACC-MTK、EQoS、wrtbwmon 流量统计、
  dnsmasq-full、luci-ssl-openssl、luci-theme-bootstrap、中文界面（MTK 插件）、
  htop/nano/tcpdump/ethtool、zram-swap、全套 iptables/nftables 扩展
- 本次新增：`luci-app-upnp` + `miniupnpd-nftables` + `luci-i18n-upnp-zh-cn`
  （另补全 `luci-i18n-base-zh-cn` / `luci-i18n-firewall-zh-cn`）
  - 24.10 里 `miniupnpd` 只是 `PROVIDES` 虚拟包名，**不能**写成
    `CONFIG_PACKAGE_miniupnpd=y`（`make defconfig` 会直接丢弃）。真实可选包
    是 `miniupnpd-nftables`（默认变体，本树 firewall4/nftables 用它）与
    `miniupnpd-iptables`；`luci-app-upnp` 的 `+miniupnpd` 依赖会自动解析到默认变体。
- 明确不含：HomeProxy、SSR-Plus、PassWall / VSSR、Samba / Aria2 / qBittorrent /
  DDNS / MWAN3 / Zerotier
- **ttyd 保留**：由上游默认包带入（`luci-app-ttyd` / `ttyd`），按用户确认
  不剔除、也不额外添加；主题实际为 `luci-theme-bootstrap` —— 该分支不存在
  `luci-theme-bootstrap-mod`，且 `luci-light` 硬依赖 `+luci-theme-bootstrap`，
  配置层面无法覆盖。

### SSL 后端统一为 OpenSSL（Run #2 失败修复）

`package/libs/ustream-ssl` 的 `libustream-mbedtls` / `libustream-openssl` /
`libustream-wolfssl` 是**三个独立包**（无 `PROVIDES` 虚拟名），三者都会安装
同一个 `/lib/libustream-ssl.so`。基准配置里的 `luci-ssl` 会强制拉
`libustream-mbedtls + px5g-mbedtls`，而 filogic 的 `target.mk` 在
`DEFAULT_PACKAGES` 里自带 `wpad-openssl`，`wget-ssl` / `openssl-util` 也走
OpenSSL —— 两套后端同时进 rootfs，opkg 在 `package/install` 阶段报
`check_data_file_clashes` → `Error 255`。

因此改用 `luci-ssl-openssl`（`+libustream-openssl +openssl-util`），去掉
`luci-ssl` 与 `wpad-mbedtls`，HTTPS LuCI 功能不变，全镜像只保留一种
`libustream` 实现。workflow 的编译前断言会逐项 forbid
`luci-ssl` / `libustream-mbedtls` / `px5g-mbedtls` / `wpad-mbedtls`，
并 need `wpad-openssl`。

### 配置清理（静态审查后）

种子配置删除了：

- 5.4 树残留子目标 `CONFIG_TARGET_mediatek_mt7981`、
  `CONFIG_TARGET_MULTI_PROFILE` / `CONFIG_TARGET_PER_DEVICE_ROOTFS`、
  20 行空值 `CONFIG_TARGET_DEVICE_PACKAGES_*`；
- 该分支不存在的包符号 `luci-theme-bootstrap-mod` / `kmod-nft-fullcone` /
  `tc-mod-iptables`；`ebtables` 改为真实包名 `ebtables-legacy`；
- PassWall / VSSR / rclone 等代理插件残留的关闭项；
- `CONFIG_MTK_BAND_STEERING=y` 与后面的 `# ... is not set` 自相矛盾，
  统一保持关闭（不启用漫游引导）。

workflow 新增「种子配置静态检查」步骤：对上述符号逐条 `forbid`，
并通用检测「同一符号既 `=y` 又 `is not set`」，防止清理结果回归。

### 源码 commit 固定（可复现）

`env.SOURCE_COMMIT` 固定为
`ec9ef10efc65da1e6d1de4e2c043c0e13d08eed8`（Run #3 成功构建所用上游 HEAD，
2026-07-23）。workflow 改用 `git fetch --depth=1 origin <SHA>` +
`checkout --detach FETCH_HEAD`，取代 `clone -b <分支>` —— 分支 HEAD 会移动，
会在无人知晓的情况下换内核或换包。若按 SHA 拉取失败，会回退到分支浅克隆并
打印 `::warning::`（此时本次构建不可复现）。

feeds 暂未 pin（由 `feeds.conf.default` 动态解析），但编译日志会打印各 feed
的 HEAD 快照与 `feeds.conf` 副本（`feeds.conf.snapshot`），便于事后按同一组
commit 复现。runner 目前仍为 `ubuntu-22.04`；若将来 GitHub 下线该镜像，
需改 `runs-on` 并重新验证完整编译。

### ccache 缓存（编译提速）

Run #4 日志显示 `Cache not found for input keys: ccache-6.6-*`，post-job 又报
`Path Validation Error: ~/.ccache 不存在 → no cache is being saved`：缓存从未被
保存，每次都是冷启动（Run #4 用了 78 分钟，Run #3 为 61 分钟）。原因是
`sudo ccache -M 5G` 以 root 身份写配置、且 `$HOME/.ccache` 目录从未创建，
`-z` 清零的也不是目标目录。

修复：`mkdir -p "$HOME/.ccache"` → 本步骤内先 `export CCACHE_DIR` → 去掉 `sudo` →
再执行 `-M 5G` / `-z`，最后写入 `$GITHUB_ENV`；缓存 key 改为
`<SOURCE_COMMIT>-<配置 hash>-<run_number>`（每次都能保存新缓存），配三级
`restore-keys` 按「同 commit+同配置 → 同 commit → 任意」逐级回退复用；编译后
新增 `ccache -s` 统计步骤（`if: always()`，失败也能看命中率）。

**注意**：Run #1~#4 都没有成功保存过缓存，所以修复后的**第一次编译仍会是全量
冷启动**，从第二次起才会明显提速。

## 二、目录

```
config/fur602-6.6-mtwifi-upnp.config   # 编译种子（基准 + UPnP，已清理）
dts/mt7981b-honor-fur-602.dts         # 6.6-padavanonly 设备树（WAN=MT7531 port0）
patches/apply-device.py               # 注入 filogic.mk 的 honor_fur-602 设备块
.github/workflows/build-fur602-6.6.yml
push-to-github.sh                      # 一键推送（push 后自动开始编译）
```

源码树原生**没有** FUR-602 定义，workflow 会先复制 DTS 并注入设备块，再 `make defconfig`。
`IMAGE_SIZE=116736k`（114 MiB），只适配 U-Boot 的 `expand(114m)` 布局。

## 三、开始编译（3 步）

1. 生成 GitHub Token（用于命令行推送；GitHub 网页登录仍需你自己操作）：

   - Classic PAT（推荐，最省事）：<https://github.com/settings/tokens/new?scopes=repo,workflow&description=FUR-602-6.6-Build>
     - 勾选 `repo` 和 `workflow`（推送 `.github/workflows/*.yml` 必须有 `workflow`）
     - 有效期建议选 30 天，编译完即可删除：<https://github.com/settings/tokens>
   - Fine-grained PAT（可选）：<https://github.com/settings/personal-access-tokens/new>
     - 对应仓库 `Contents: Read & Write`、`Workflows: Read & Write`、`Metadata: Read`

2. GitHub 网页新建一个**空**仓库：<https://github.com/new>
   （不要勾 README / .gitignore / License；public 即可，public 仓库 Actions 时长不限）。

3. 在本目录执行（Git Bash / WSL / Linux 均可）：

```bash
./push-to-github.sh https://github.com/<你的用户名>/fur602-6.6-mtwifi-upnp.git
```

提示输入密码时，**粘贴 Token 而不是账号密码**（用户名填 GitHub 用户名）。
推送到 `main` 会**自动触发**工作流（也可在 Actions 里手动 Run workflow）。
耗时约 1~1.5 小时（ccache 命中后更短），完成后在 Summary → Artifacts 下载
`fur602-6.6-mtwifi-upnp-<run#>`，内含 factory.bin / sysupgrade.bin /
initramfs-kernel.bin / sha256sums / config.buildinfo / feeds.buildinfo /
version.buildinfo / profiles.json / manifest / effective.config / feeds 快照
以及 5 个 `mt79xx bl2` bin。`sha256sums` 里列出的文件会全部收集并在上传前
跑一次 `sha256sum -c`，不再出现 MISSING 条目。

## 四、编译内置断言

**种子配置静态检查**（`make defconfig` 之前）： forbid 5.4 残留子目标、
`bootstrap-mod` / `kmod-nft-fullcone` / `tc-mod-iptables` 等无效符号、
虚拟包名 `miniupnpd`、多 profile 残留、空设备包列表、
`BAND_STEERING` 重复开启、代理插件残留；并通用检测
「同一符号既 `=y` 又 `is not set`」。

**编译前强校验**：内核 6.6、设备 honor_fur-602 已启用且设备块存在、DTS 就位、
`kmod-mt_wifi` 启用且**未**启用开源 mt7915e、`luci-app-upnp` 与
`miniupnpd-nftables` 均已选中、**未**选中 `miniupnpd-iptables`、
**未**混入 SSR-Plus/HomeProxy、SSL 栈只有一套 OpenSSL
（`luci-ssl-openssl` + `libustream-openssl` + `wpad-openssl` 已选中，
`luci-ssl` / `libustream-mbedtls` / `px5g-mbedtls` / `wpad-mbedtls` 全部禁用）、
主题为 `luci-theme-bootstrap` 且无 `bootstrap-mod`、
`IMAGE_SIZE=116736k`。ttyd 只打印符号、不做强断言（保留即可，
避免上游默认包调整时误判失败）。任一强校验不满足立即终止。
`make defconfig` 后还会把全部 SSL 符号和 Kconfig 中的 `select` 来源打印到日志，
便于万一再次冲突时直接定位。
断言一律用显式 `if + exit 1`，不用 `grep && echo`（后者在 `set -e` 下失败不会中断）。

**编译后校验**：factory / sysupgrade 双产物存在，且
`sha256sum -c sha256sums` 全部条目通过。

## 五、刷机前提（重要）

- 先刷 [hanwckf/bl-mt798x](https://github.com/hanwckf/bl-mt798x) 的
  `mt7981_honor_fur-602` 定制 U-Boot；
- U-Boot 里 `setenv mtd_layout_label "expand(114m)"` + `saveenv`；
- 刷前备份 Factory 分区（WiFi 校准数据），DTS 中 MAC 偏移 `0x2a` 请按实机核对；
- factory.bin 仅首次从 U-Boot 恢复页刷入，后续升级用 sysupgrade.bin；
- 管理 IP `192.168.1.1`，root 无密码；闭源 WiFi 走「网络 → MTK WiFi」配置。

## 参考

- [padavanonly/immortalwrt-mt798x-6.6](https://github.com/padavanonly/immortalwrt-mt798x-6.6)
- [saisi1222/fur602-firmware](https://github.com/saisi1222/fur602-firmware)（6.6 基准配置与设备注入脚本）
