# HONOR FUR-602 · ImmortalWrt 6.6 + 闭源 mtwifi + UPnP 云编译

基于 `padavanonly/immortalwrt-mt798x-6.6` 的 `openwrt-24.10-6.6` 分支（内核 6.6，
闭源 `kmod-mt_wifi`），设备 `mediatek/filogic` · `honor_fur-602`。
**插件策略：基本系统 + UPnP，不加任何代理与重型插件。**

## 一、插件清单（已确认）

- 基准（沿用 6.6 FUR-602 参考配置，共 145 项）：硬件 NAT/WED/BBR/fullcone、
  TurboACC-MTK、EQoS、wrtbwmon 流量统计、dnsmasq-full、luci-ssl、
  luci-theme-bootstrap-mod、中文界面（MTK 插件）、htop/nano/tcpdump/ethtool、
  zram-swap、全套 iptables/nftables 扩展
- 本次新增：`luci-app-upnp` + `miniupnpd-nftables` + `luci-i18n-upnp-zh-cn`
  （另补全 `luci-i18n-base-zh-cn` / `luci-i18n-firewall-zh-cn`）
  - 24.10 里 `miniupnpd` 只是 `PROVIDES` 虚拟包名，**不能**写成
    `CONFIG_PACKAGE_miniupnpd=y`（`make defconfig` 会直接丢弃）。真实可选包
    是 `miniupnpd-nftables`（默认变体，本树 firewall4/nftables 用它）与
    `miniupnpd-iptables`；`luci-app-upnp` 的 `+miniupnpd` 依赖会自动解析到默认变体。
- 明确不含：HomeProxy、SSR-Plus、ttyd、Samba / Aria2 / qBittorrent / DDNS /
  MWAN3 / Zerotier；主题沿用 bootstrap-mod

## 二、目录

```
config/fur602-6.6-mtwifi-upnp.config   # 编译种子（基准 + UPnP）
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
耗时约 3~5 小时，完成后在 Summary → Artifacts 下载
`fur602-6.6-mtwifi-upnp-<run#>`，内含 factory.bin / sysupgrade.bin /
initramfs-kernel.bin / sha256sums / config.buildinfo / manifest。

## 四、编译内置断言

编译前强制校验：内核 6.6、设备 honor_fur-602 已启用且设备块存在、DTS 就位、
`kmod-mt_wifi` 启用且**未**启用开源 mt7915e、`luci-app-upnp` 与
`miniupnpd-nftables` 均已选中、**未**选中 `miniupnpd-iptables`、
**未**混入 SSR-Plus/HomeProxy、`IMAGE_SIZE=116736k`。任一不满足立即终止。
断言用显式 `if + exit 1`，不用 `grep && echo`（后者在 `set -e` 下失败不会中断）。
编译后校验 factory / sysupgrade 双产物存在。

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
