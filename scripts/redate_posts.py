import os, re, datetime

posts_dir = os.path.join(os.path.dirname(__file__), '..', '_posts')
files = sorted(os.listdir(posts_dir))

# Old-to-new date mapping (date only), preserving time
# #1 welcome: 2026-05-31 09:00 -> 2026-05-31 08:00 (keep, make earliest)
# #2 pcie-gen6: 2026-05-31 13:00 -> 2026-05-31 09:00 (keep, second)
# #3 onwards: consecutive days from 2026-06-01
old_dates = [
    ("2026-05-31", "welcome"),
    ("2026-05-31", "pcie-gen6"),
    ("2026-06-07", "cxl-memory-pooling"),
    ("2026-06-08", "nvme-2-0-2-1-zns-kv"),
    ("2026-06-10", "nvme-over-tcp-implementation"),
    ("2026-06-12", "zns-ssd-principles"),
    ("2026-06-14", "ssd-controller-architecture"),
    ("2026-06-16", "cxl-type3-memory-device"),
    ("2026-06-18", "coherent-optical-400zr-800zr"),
    ("2026-06-20", "dwdm-datacenter-optical-network"),
    ("2026-06-22", "silicon-photonics-interconnect"),
    ("2026-06-24", "co-packaged-optics-cpo"),
    ("2026-06-26", "1-6t-optical-transceiver-roadmap"),
    ("2026-06-29", "afa-all-flash-array-architecture"),
    ("2026-07-06", "distributed-storage-ceph-minio"),
    ("2026-07-13", "smartnic-dpu-bluefield-ipu"),
    ("2026-07-20", "dci-datacenter-interconnect-design"),
    ("2026-07-27", "ssd-form-factor-edsff-e3-e1"),
    ("2026-08-03", "storage-tiering-architecture"),
    ("2026-08-10", "dc-network-topology-spine-leaf-dragonfly"),
    ("2026-08-17", "nvme-over-rdma-roce-infiband"),
    ("2026-08-24", "storage-data-protection-raid-erasure-coding"),
    ("2026-08-31", "container-storage-csi-rook-longhorn"),
    ("2026-09-07", "hpc-storage-lustre-weka-gpfs"),
]

new_dates = [
    ("2026-05-31", "08:00:00"),  # #1 welcome
    ("2026-05-31", "09:00:00"),  # #2 pcie
]
for i in range(3, 25):
    d = datetime.date(2026, 6, 1) + datetime.timedelta(days=i - 3)
    new_dates.append((d.strftime("%Y-%m-%d"), "09:00:00"))

for (old_date, slug), (new_date, new_time) in zip(old_dates, new_dates):
    old_name = f"{old_date}-{slug}.md"
    new_name = f"{new_date}-{slug}.md"
    old_path = os.path.join(posts_dir, old_name)
    new_path = os.path.join(posts_dir, new_name)

    if not os.path.exists(old_path):
        # maybe already renamed in a previous run; find by slug
        matches = [f for f in os.listdir(posts_dir) if f.endswith(f"-{slug}.md")]
        if matches:
            old_path = os.path.join(posts_dir, matches[0])
            old_name = matches[0]
        else:
            print(f"  SKIP {slug} (not found)")
            continue

    with open(old_path, encoding='utf-8') as f:
        content = f.read()

    new_dt = f"{new_date} {new_time} +0900"
    # Update date in frontmatter
    content = re.sub(r'^date: .+', f'date: {new_dt}', content, count=1, flags=re.MULTILINE)

    if new_name != old_name:
        os.rename(old_path, new_path)
        print(f"  {old_name} -> {new_name}")
    else:
        print(f"  {old_name} (date unchanged)")

    with open(new_path, 'w', encoding='utf-8') as f:
        f.write(content)

print("Done.")
