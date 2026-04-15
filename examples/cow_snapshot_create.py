#!/usr/bin/env python3
"""
Example script demonstrating how to create a copy-on-write (COW) device snapshot
and then create a Firecracker snapshot from it.

This workflow is useful for:
- Creating efficient snapshots of base root filesystems
- Allowing multiple VMs to share a common base image
- Creating incremental snapshots without modifying the original image

Workflow:
1. Launch a Firecracker VM with a base root filesystem
2. Create a copy-on-write device snapshot (overlay device)
3. Pause the VM
4. Create a Firecracker snapshot (VM state + memory)
5. Stop the VM

Usage:
    python cow_snapshot_create.py \
        --base-rootfs /path/to/base/rootfs.img \
        --kernel /path/to/kernel \
        --snapshot-name my_snapshot_overlay \
        --snapshot-path /path/to/snapshots/state.snapshot \
        --mem-file-path /path/to/snapshots/memory.mem
"""

import signal
import argparse
from time import sleep
from pathlib import Path
import subprocess

from pyrecracker.vm import VMManager, VMError


def main():
    parser = argparse.ArgumentParser(
        description="Create a COW device snapshot and a Firecracker snapshot."
    )
    parser.add_argument(
        '--base-rootfs',
        type=str,
        required=True,
        help='Path to the base root filesystem image (will not be modified)'
    )
    parser.add_argument(
        '--kernel',
        type=str,
        required=True,
        help='Path to the kernel image'
    )
    parser.add_argument(
        '--snapshot-name',
        type=str,
        required=True,
        help='Name/path prefix for the COW overlay device (e.g., my_snapshot_overlay)'
    )
    parser.add_argument(
        '--snapshot-path',
        type=str,
        required=True,
        help='Path to save the Firecracker VM state snapshot'
    )
    parser.add_argument(
        '--mem-file-path',
        type=str,
        required=True,
        help='Path to save the VM memory file'
    )
    parser.add_argument(
        '--runtime-secs',
        type=int,
        default=10,
        help='How long to run the VM before creating snapshots (default: 10 seconds)'
    )
    args = parser.parse_args()

    # Validate input paths
    if not Path(args.base_rootfs).exists():
        print(f"Error: Base rootfs path does not exist: {args.base_rootfs}")
        return 1

    if not Path(args.kernel).exists():
        print(f"Error: Kernel path does not exist: {args.kernel}")
        return 1

    # Ensure output directories exist
    Path(args.snapshot_path).parent.mkdir(parents=True, exist_ok=True)
    Path(args.mem_file_path).parent.mkdir(parents=True, exist_ok=True)

    # Initialize VM manager
    vm = VMManager(
        socket_path="/tmp/firecracker.sock",
        kernel_image_path=args.kernel
    )

    # Configure VM settings
    vm.vcpu_count = 2
    vm.mem_size_mib = 512
    vm.boot_args = "console=ttyS0 reboot=k panic=1 pci=off ip=172.16.0.2::172.16.0.1:255.255.255.0::eth0:off"
    vm.drive_id = "rootfs"
    vm.is_root_device = True
    vm.path_on_host = args.base_rootfs
    vm.is_read_only = True  # Important: keep base image read-only
    vm.iface_id = "eth0"
    vm.host_dev_name = "tap0"
    vm.guest_mac = "AA:FC:00:00:00:01"
    vm.host_ip = "172.16.0.1"
    vm.guest_ip = "172.16.0.2"

    try:
        print("=" * 70)
        print("Creating COW Device Snapshot and Firecracker Snapshot")
        print("=" * 70)

        print("\n[1/6] Configuring VM...")
        vm.configure()

        print("[2/6] Starting VM...")
        vm.start()
        print(f"  VM launched successfully! Running for {args.runtime_secs} seconds...")
        sleep(args.runtime_secs)

        print("\n[3/6] Pausing VM and creating Firecracker snapshot...")
        print(f"  Snapshot file: {args.snapshot_path}")
        print(f"  Memory file: {args.mem_file_path}")
        vm.pause()
        vm.create_snapshot(
            snapshot_path=args.snapshot_path,
            mem_file_path=args.mem_file_path
        )
        print("✓ Firecracker snapshot created successfully!")

        print("\n[4/6] Stopping VM...")
        vm.stop()
        print("  VM stopped successfully!")

        print("\n" + "=" * 70)
        print("SUCCESS: Snapshots created!")
        print("=" * 70)
        print(f"\nSnapshots are ready at:")
        print(f"  - COW device overlay: {args.snapshot_name}.img")
        print(f"  - VM state: {args.snapshot_path}")
        print(f"  - VM memory: {args.mem_file_path}")

        print("\n[5/6] Creating copy-on-write (COW) device snapshot...")
        print(f"  Base rootfs: {args.base_rootfs}")
        print(f"  Overlay name: {args.snapshot_name}")
        # Initialize VM manager
        vm = VMManager(
            socket_path="/tmp/firecracker.sock",
            kernel_image_path=args.kernel
        )

        # Configure VM settings
        vm.vcpu_count = 2
        vm.mem_size_mib = 512
        vm.boot_args = "console=ttyS0 reboot=k panic=1 pci=off ip=172.16.0.2::172.16.0.1:255.255.255.0::eth0:off"
        vm.drive_id = "rootfs"
        vm.is_root_device = True
        vm.path_on_host = args.base_rootfs
        vm.is_read_only = True  # Important: keep base image read-only
        vm.iface_id = "eth0"
        vm.host_dev_name = "tap0"
        vm.guest_mac = "AA:FC:00:00:00:01"
        vm.host_ip = "172.16.0.1"
        vm.guest_ip = "172.16.0.2"
        vm.create_cow_dev_snapshot(
            snapshot_name=args.snapshot_name,
            base_root_fs=args.base_rootfs
        )
        print("COW device snapshot created successfully!")

        subprocess.run([
            "sudo", "chmod", "660", f"/dev/mapper/{args.snapshot_name}"
        ], check=True)

        subprocess.run([
            "sudo", "chgrp", "kvm", f"/dev/mapper/{args.snapshot_name}"
        ], check=True)
        
        print("[6/6] Loading copy on write device snapshot...")
        print(f"  Snapshot file: {args.snapshot_path}")
        print(f"  Memory file: {args.mem_file_path}")
        vm.configure()
        vm.load_cow_dev_snapshot(args.snapshot_name)
        vm.start()

        print("  Copy on write device snapshot loaded successfully!")

        def sigterm_handler(signum, frame):
            print("\nSIGINT received, stopping the VM...")
            vm.stop()
            print("VM stopped successfully!")
            print("Exiting.")
            exit(0)

        signal.signal(signal.SIGINT, sigterm_handler)
        while True:
            pass

    except VMError as err:
        print(f"\n✗ Error: {err}")
        try:
            vm.stop()
        except Exception as stop_err:
            print(f"Error while stopping VM: {stop_err}")
        return 1

    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt received. Stopping VM...")
        try:
            vm.stop()
            print("VM stopped successfully!")
        except Exception as err:
            print(f"Error while stopping VM: {err}")
        return 1


if __name__ == "__main__":
    exit(main())
