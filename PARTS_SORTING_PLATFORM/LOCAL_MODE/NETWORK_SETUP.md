# Network setup: Android phone hotspot

Local mode's network is specifically **the Android phone creates a WiFi
hotspot**; the local-server computer and the ESP32 both join that
hotspot as ordinary clients. There is no separate router/access point.
This replaces the earlier vague "predefined WiFi access point" language
with the concrete topology actually used.

This matters because a phone hotspot is not a full router: it generally
has no admin page to reserve a fixed IP for a specific device, which
breaks the assumption baked into `firmware/esp32_local_http/esp32_local_http.ino`
that `LOCAL_SERVER_HOST` is a static/reserved address. The options below
cover how to get a stable, known IP for the local-server computer anyway,
in order of preference. **None of this has been tested against real
phone hardware** -- verify each step on the actual phone/Android version
in use.

## Gateway IP (the phone itself)

On stock Android, the hotspot device (the phone) commonly takes
`192.168.43.1` as its own gateway/DHCP-server address on the hotspot
subnet. This is **not guaranteed** -- OEM skins (Samsung, Xiaomi, etc.)
and Android versions have been observed to use different subnets.
**Verify on the actual phone**: after enabling the hotspot, check the
phone's own IP (hotspot settings screen, or `ip addr`/`ifconfig` if a
second device can ADB into it) rather than assuming `192.168.43.1`.

## Getting a stable IP for the local-server computer

### Option A: manual static IP on the computer (preferred)

Connect the computer to the phone's hotspot once, note the subnet (e.g.
`192.168.43.0/24`), then manually configure the computer's WiFi adapter
with a static IP outside the DHCP range the phone hands out (commonly
the phone's DHCP pool is a small range near the gateway; picking an
address near the top of the subnet, e.g. `.50`+, usually avoids
collisions, but **verify the phone's actual DHCP range** first).

Tradeoff: **not guaranteed to work.** Some Android versions/OEMs reject
or silently drop traffic from a client IP configured outside what their
hotspot's DHCP server handed out, even if it's in the same subnet. This
needs on-site testing with the specific phone before relying on it.

### Option B: read the DHCP lease from the phone's hotspot UI

Connect the computer to the hotspot normally (DHCP), then open the
phone's hotspot settings -- most Android hotspot screens have a
"connected devices" list showing each device's assigned IP. Read that IP
and hardcode it into `esp32_local_http.ino`'s `LOCAL_SERVER_HOST`.

Tradeoff: that lease can change if it expires or the computer disconnects
and reconnects after being idle for a long time (exact lease duration is
phone/OEM-specific and not something to assume a value for). If the
ESP32 stops reaching local-server, re-check this screen for a changed IP
before assuming something else broke.

### Option C (future improvement, not implemented): mDNS

The more robust fix is to have local-server advertise itself on the LAN
by name (e.g. `local-server.local`) via mDNS, so the ESP32 resolves the
name instead of relying on any hardcoded IP. This is **not implemented
in this codebase** -- it's documented here as a next step, not shipped.

Sketch of what it would take:

- On the Python side, the lightweight option is the `zeroconf` package
  (`pip install zeroconf`): register a service
  (`ServiceInfo`/`Zeroconf().register_service(...)`) advertising
  `local-server.local` with the FastAPI app's port alongside starting
  uvicorn in `app/main.py`.
- On the ESP32 side, `ESPmDNS.h` (bundled with Arduino-ESP32 core) can
  resolve `.local` names via `MDNS.queryHost("local-server")`, replacing
  the hardcoded `LOCAL_SERVER_HOST` constant with a resolved IP looked up
  at connect time (and re-resolved on failure, in case the IP changed).
- This avoids both Option A and B's fragility, at the cost of adding a
  dependency and some mDNS-specific failure modes (multicast can behave
  inconsistently on some phone hotspot implementations -- would need its
  own verification pass).

## Client limits

Android hotspots typically cap connected clients somewhere around 5-10
devices (exact number is OEM/Android-version specific). This setup only
needs three devices on the hotspot (phone itself, the local-server
computer, the ESP32), so it comfortably fits regardless of the exact
cap -- just confirming this isn't a concern here.

## 2.4GHz vs 5GHz band

Most ESP32 and ESP32-S3 boards' WiFi radios **only support 2.4GHz**. If
the phone's hotspot defaults to 5GHz-only, or a dual-band "AP" mode that
prefers 5GHz, the ESP32 will not see the network at all (it won't even
show up in a WiFi scan from the board).

Before flashing or debugging a "can't connect to WiFi" issue on the
ESP32, check the phone's hotspot settings for a band selector and force
it to **2.4GHz** (sometimes labeled "compatibility mode" or similar,
depending on OEM/Android version) -- **verify the exact menu wording on
the phone in use**, it is not consistent across Android skins.
