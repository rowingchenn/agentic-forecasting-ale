# Sandbox images

This directory separates Task foundations from the tools that build and run them.

```text
base/
├── container-ubuntu22/  Ubuntu desktop container base
├── vm-ubuntu24/         Ubuntu OCI source for a bootable VM
└── vm-windows10/        private Windows seed preparation recipe
builders/
└── vm-materializer/     converts a VM OCI rootfs to qcow2
runtimes/
└── qemu-runner/         container that runs a prepared qcow2 with QEMU/KVM
```

Task repositories extend or reference only entries under `base/`. Linux VM Tasks build an
OCI rootfs from `vm-ubuntu24`; the materializer converts it to qcow2 and the QEMU runner
boots it. Windows preparation already produces qcow2, so it goes directly to the runner.

The image contract, identity rules and required labels are defined in
[`../docs/specs/sandbox-image.md`](../docs/specs/sandbox-image.md).

Each image's version lives in `packages/ale-run/src/ale/run/releases.json` with a hash of
its sources. A published version never changes: after editing an image, give it a new
version there and record the new hash (the image lock test prints it).

```bash
just images                                  # pull published releases, build new ones
images/build.sh vm-ubuntu24-base             # one image
```

`.github/workflows/images.yml` publishes each new version once; its manual `promote`
input gives an already-published image a version without rebuilding it. The licensed
Windows disk remains private. Do not add Task content or Provider credentials here.
