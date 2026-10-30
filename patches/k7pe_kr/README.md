# K7 Premier KR V039.001.260902 — test candidate

The owner's nine core stock inputs exactly match `dl3hev/stock`. This manifest
intentionally references the existing `dl3hev` app deltas and the shared AA
library delta, rather than duplicating binaries or transplanting different code.

Seven reconstructed outputs match the recorded manifest hashes. Static framework
checks and host full-mode install/uninstall passed. See
[the Korean capture report](../../docs/K7_CAPTURE_RESULT_ko.md) for evidence and limits.

Real-car wireless projection and Kia Connect remain unverified. The initial kit
has no wlan interface and `wl` cannot find an adapter; this does not establish
whether hardware is physically absent or simply not started. Do not bypass Wi-Fi,
stock checksum, backup or uninstall checks.
