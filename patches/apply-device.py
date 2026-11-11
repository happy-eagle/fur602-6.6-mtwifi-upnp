#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 HONOR FUR-602 设备定义注入 padavanonly 的 filogic.mk。
- 闭源 mtwifi 驱动：DEVICE_PACKAGES 用 kmod-mt_wifi + conninfra/warp/hnat
  （kmod-mt_wifi 定义在源码树 package/mtk/drivers/mt_wifi/Makefile，已核对存在；
   kmod-mt7981-firmware / mt7981-wo-firmware 为固件包，上游 filogic.mk 中
   所有 mt7981 设备均这样列，随 feeds update/install 提供，不引入 mt7915e 驱动）
- DTS 文件请另行复制到 target/linux/mediatek/dts/mt7981b-honor-fur-602.dts
- 幂等且纠正式：若 filogic.mk 中已存在 honor_fur-602 块（无论对错），先删掉再注入正确版本，
  避免上游若自带错误/旧块时被跳过。
用法: python3 apply-device.py <path-to-filogic.mk>
"""
import sys
import os

BLOCK = '''define Device/honor_fur-602
  DEVICE_VENDOR := HONOR
  DEVICE_MODEL := FUR-602
  DEVICE_DTS := mt7981b-honor-fur-602
  DEVICE_DTS_DIR := ../dts
  SUPPORTED_DEVICES += mediatek,mt7981-spim-snand-rfb
  # 闭源 mtwifi 配套：kmod-mt_wifi 为主驱动（自带 MT7981 WiFi 固件，安装到 /lib/firmware/）；
  # 后两个是上游 mt7981 设备统一引用的固件包；conninfra/warp/hnat 为驱动依赖。
  DEVICE_PACKAGES := kmod-mt_wifi kmod-mt7981-firmware mt7981-wo-firmware kmod-conninfra kmod-warp kmod-mediatek_hnat
  UBINIZE_OPTS := -E 5
  BLOCKSIZE := 128k
  PAGESIZE := 2048
  IMAGE_SIZE := 116736k
  KERNEL_IN_UBI := 1
  IMAGES += factory.bin
  IMAGE/factory.bin := append-ubi | check-size $$$$(IMAGE_SIZE)
  IMAGE/sysupgrade.bin := sysupgrade-tar | append-metadata
  KERNEL = kernel-bin | lzma | \\
	fit lzma $$(KDIR)/image-$$(firstword $$(DEVICE_DTS)).dtb
  KERNEL_INITRAMFS = kernel-bin | lzma | \\
	fit lzma $$(KDIR)/image-$$(firstword $$(DEVICE_DTS)).dtb with-initrd
endef
TARGET_DEVICES += honor_fur-602

'''

# 注入锚点：优先用 huasifei_wh3000-pro（已在 openwrt-24.10-6.6 的
# filogic.mk 第 1199 行核对存在）；若上游改名，退而求其次用相邻的 mt7981 设备块。
ANCHORS = (
    "define Device/huasifei_wh3000-pro",
    "define Device/cmcc_a10",
    "define Device/h3c_magic-nx30-pro-nmbm",
)

MARK_BEGIN = "define Device/honor_fur-602"
MARK_END = "endef"
MARK_TAIL = "TARGET_DEVICES += honor_fur-602"


def remove_existing(lines):
    """删除已有的 honor_fur-602 设备块（define ... endef + 紧随的 TARGET_DEVICES += 行）。"""
    out = []
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].strip() == MARK_BEGIN:
            # 跳到 endef
            i += 1
            while i < n and lines[i].strip() != MARK_END:
                i += 1
            # 现在 lines[i] == 'endef'
            i += 1
            # 跳过紧随的 TARGET_DEVICES += honor_fur-602
            if i < n and lines[i].strip() == MARK_TAIL:
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return out


def main():
    if len(sys.argv) < 2:
        print("usage: apply-device.py <filogic.mk>")
        sys.exit(1)
    path = sys.argv[1]
    if not os.path.isfile(path):
        print("ERROR: file not found:", path)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    before_existing = any(ln.strip() == MARK_BEGIN for ln in lines)
    lines = remove_existing(lines)
    if before_existing:
        print("已移除 filogic.mk 中既有的 honor_fur-602 块（如有错误/旧版本）。")

    out = []
    inserted = False
    used_anchor = ""
    for ln in lines:
        if not inserted and ln.strip() in ANCHORS:
            out.append(BLOCK)
            inserted = True
            used_anchor = ln.strip()
        out.append(ln)
    if not inserted:
        # 上游结构变了时不要静默追加到文件末尾（可能落在 BuildImage eval 之后，
        # 设备不会被注册，产生一个看似成功却没有 profile 的编译）——直接报错。
        print("ERROR: 在 filogic.mk 中找不到任何已知锚点，请检查上游分支是否变更。")
        print("       已尝试:", ", ".join(ANCHORS))
        sys.exit(1)
    print("注入位置:", used_anchor)

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(out)
    print("已注入/校正 FUR-602 设备定义到", path)


if __name__ == "__main__":
    main()
