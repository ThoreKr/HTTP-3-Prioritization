# browsertime
1. Build chromium 95.0.4638.54 with applied credentials_flag.patch in chromium /
2. Build docker container via build.sh

## Building Chromium

1. [Build Instructions](https://chromium.googlesource.com/chromium/src/+/main/docs/linux/build_instructions.md)
2. [Release Branches](https://www.chromium.org/developers/how-tos/get-the-code/working-with-release-branches/)

### Basic Walkthrough

1. Get at least 100GB disk space
2. Download depot tools
3. Fetch the code as in the build instructions
4. Get a release branch `git checkout -b comsyschrome 95.0.4638.54`
5. Apply the patch using git apply
6. Create the `out/Default` directory within the chromium `src` directory
7. `gn gen out/Default`
8. Modify the `chromium/src/out/Default/args.gn` to contain:
```
is_debug = false
dcheck_always_on = false
```
9. `autoninja -C out/Default chrome`
10. Wait for the compilation to complete
11. `chromium/src/out/Default/chrome` is now a standalone executable.
