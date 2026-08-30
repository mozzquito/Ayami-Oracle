#!/usr/bin/env python3
"""
Megvii MegCube AIOTAP WebAPI client.

Bypasses the box's web UI (which blocks video preview / rule drawing on Mac)
by talking to the AIOTAP HTTP API directly.

Credentials are read from environment variables, never hardcoded:
    MEGVII_HOST      e.g. 192.168.1.100  (default: 192.168.1.100)
    MEGVII_USER      e.g. admin
    MEGVII_PASSWORD  device login password

Usage:
    export MEGVII_HOST=192.168.1.100
    export MEGVII_USER=admin
    export MEGVII_PASSWORD='...'
    python3 megvii_client.py cap                        # capability set (read-only)
    python3 megvii_client.py list                        # list configured monitors (read-only)
    python3 megvii_client.py add-rule --device-id 2 --event-type INTRUSION \
        --points 0,0 0,1 1,1 1,0                          # whole-frame intrusion zone

Payload format verified against a live device on 2026-08-24 by reading back
its own working config (device already had SMOKING/HOLDWEAPON/FIGHT rules on
device_id=2) rather than guessing from the bundled AIOTAP docs alone — several
doc-derived assumptions turned out wrong in practice:
  - common_param.alg_type must be ["bypass"], NOT ["alert_alarm"]
    ("alert_alarm" instead goes in warehouse_v20_param.labels.algoCabinName)
  - warehouse_v20_param.rulesParams[].areas[] does NOT need "multiPoints" or
    "custom" — the full JSON-schema in the docs (aipaas.v1.Area) documents a
    lower-level cloud algorithm-orchestration protocol, not what this
    endpoint actually accepts.
  - rulesParams[] does NOT need a "destinations" field (image/feature/event
    dest with S3/Kafka config) despite the docs marking it required — that
    too belongs to the lower-level protocol, not this device's local API.
  - A device/channel can only have ONE "bypass"-type monitor. Additional
    perimeter/behavior rules are added as new entries in that monitor's
    warehouse_v20_param.rulesParams array via PUT, not as separate monitors.

Session notes:
    Login session expires after ~15-30s of inactivity (device-dependent).
    This client sends a keep_alive ping automatically every 10s while
    logged in for any command that runs longer than that.
"""
import argparse
import hashlib
import os
import sys
import threading

import requests

requests.packages.urllib3.disable_warnings()  # box uses a self-signed cert


class MegviiClient:
    def __init__(self, host: str, username: str, password: str):
        self.base = f"https://{host}"
        self.username = username
        self.password = password
        self.session_id = None
        self._keepalive_thread = None
        self._keepalive_stop = threading.Event()

    def login(self):
        r = requests.get(
            f"{self.base}/auth/login/challenge",
            headers={"Content-Type": "application/json"},
            verify=False,
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()["data"]
        session_id, challenge, salt = data["session_id"], data["challenge"], data["salt"]

        pw_hash = hashlib.sha256(
            (self.password + salt + challenge).encode()
        ).hexdigest()

        r = requests.post(
            f"{self.base}/auth/login",
            json={"session_id": session_id, "username": self.username, "password": pw_hash},
            headers={"Content-Type": "application/json"},
            verify=False,
            timeout=10,
        )
        r.raise_for_status()
        body = r.json()
        if body.get("code") != 0:
            raise RuntimeError(f"Login failed: {body}")
        self.session_id = body["data"]["session_id"]
        self._start_keepalive()
        return self.session_id

    def logout(self):
        self._stop_keepalive()
        if not self.session_id:
            return
        try:
            requests.delete(
                f"{self.base}/login_manager/logout",
                headers={"Content-Type": "application/json", "Cookie": f"sessionID={self.session_id}"},
                verify=False,
                timeout=10,
            )
        except requests.RequestException:
            pass
        self.session_id = None

    def _keep_alive_once(self):
        if not self.session_id:
            return
        try:
            requests.put(
                f"{self.base}/login_manager/keep_alive",
                headers={"Content-Type": "application/json", "Cookie": f"sessionID={self.session_id}"},
                verify=False,
                timeout=10,
            )
        except requests.RequestException:
            pass

    def _start_keepalive(self, interval: float = 10.0):
        self._keepalive_stop.clear()

        def loop():
            while not self._keepalive_stop.wait(interval):
                self._keep_alive_once()

        self._keepalive_thread = threading.Thread(target=loop, daemon=True)
        self._keepalive_thread.start()

    def _stop_keepalive(self):
        self._keepalive_stop.set()
        if self._keepalive_thread:
            self._keepalive_thread.join(timeout=1)
            self._keepalive_thread = None

    def _request(self, method: str, path: str, payload: dict):
        if not self.session_id:
            self.login()
        r = requests.request(
            method,
            f"{self.base}{path}",
            json=payload,
            headers={"Content-Type": "application/json", "Cookie": f"sessionID={self.session_id}"},
            verify=False,
            timeout=10,
        )
        r.raise_for_status()
        return r.json()

    def get_intelli_cap(self):
        return self._request("POST", "/intelli_manager/cap", {})

    def list_monitors(self) -> list[dict]:
        body = self._request("POST", "/intelli_manager/monitor_list", {})
        return body["data"]["param"]

    def query_alarm_history(self, minutes: int = 15, minor_types: list[str] | None = None, size: int = 20):
        """On-device alarm log — POST /device_alarm/alarm_history.
        Independent of alarm-bridge.mjs: this reads what the box itself
        recorded, whether or not a push server was configured/reachable at
        the time. start_time/end_time are unix ms timestamps, per docs."""
        import time
        end = int(time.time() * 1000)
        start = end - minutes * 60 * 1000
        # major_type is required by the device despite docs marking alarm_type as a whole
        # Optional — a query with no alarm_type at all errors with {"message": "alarm_type"}.
        alarm_type = {"major_type": "alert_alarm"}
        if minor_types:
            alarm_type["minor_type"] = minor_types
        query_condition = {"start_time": str(start), "end_time": str(end), "alarm_type": [alarm_type]}
        payload = {"offset": 0, "size": size, "query_condition": query_condition}
        body = self._request("POST", "/device_alarm/alarm_history", payload)
        return body.get("data", {})

    def configure_alarm_push(self, server_path: str, minor_types: list[str] | None = None,
                              major_type: str = "alert_alarm", link_type: str = "http", enable: bool = True):
        """
        server_path: bare "ip:port", NO protocol prefix, e.g. "192.168.1.4:8788". Do
        NOT prepend "http://" yourself — this bit me once already (2026-08-24): I
        misread the web UI's input box placeholder ("http(https)://main(ip):port")
        as meaning the prefix belongs in the stored value, added it here, and every
        push silently died (the device stored "http://192.168.1.4:8788" as the
        server_path, then the UI's own display re-prepended "http://" on top of that
        when rendering it back, showing "http://http://192.168.1.4:8788" — a
        malformed address the device could never actually connect to, so nothing
        ever arrived at alarm-bridge.mjs and there was no error anywhere to notice).
        The placeholder is just a hint for what protocol+host+port *conceptually*
        means; the actual field value the working UI submits is protocol-free.
        The box will POST heartbeats (JSON) and alarms (multipart/form-data, field
        "alarm_info") to this address — see alarm-bridge.mjs, which must be running
        and reachable at this address for the box to successfully push.

        minor_types: subtypes to filter to, e.g. ["HOLDWEAPON"], ["INTRUSION", "TRIPWIRE"].
        None/omitted = every subtype under major_type (all alert_alarm rules configured
        via add_rule: INTRUSION, TRIPWIRE, SMOKING, HOLDWEAPON, FIGHT, ...).

        PAYLOAD VERIFIED 2026-08-24 by intercepting the web UI's own XHR (System >
        Data Integration > Alarm Push > HTTP(s) > Save) — the bundled AIOTAP docs for
        this endpoint (POST /device_alarm/alarm_push_server, alarm_type optional) do
        NOT match reality on this device/firmware:
          - Method must be PUT, not POST (POST returns a generic "unknown" error).
          - server_info.server_path is a bare "ip:port" — no protocol prefix (see the
            big warning above; this file itself got this wrong once).
          - server_info.http_param (even {"username": "", "password": ""}) is required.
          - alarm_param.alarm_type is NOT "optional, empty = all" in practice — it must
            be a real array with at least one {"major_type": ...} entry, or the save
            silently defaults to unrelated types (face_basic_business/structure, the
            web UI's own default for its "Capture" Data Type dropdown).
          - alarm_param.retrans_live and .retrans_history, and a top-level heart_beat
            object, are required despite being documented as optional.
        """
        alarm_type_entry = {"major_type": major_type}
        if minor_types:
            alarm_type_entry["minor_type"] = minor_types
        payload = {
            "server_cfg_id": "http_main",
            "link_type": link_type,
            "enable": enable,
            "server_info": {
                "server_path": server_path,
                "http_param": {"username": "", "password": ""},
            },
            "alarm_param": {
                "alarm_type": [alarm_type_entry],
                "push_enable": {
                    "push_image_enable": True,
                    "full_image_enable": True,
                    "small_image_enable": True,
                    "upload_feature_enable": False,
                },
                "retrans_live": {"interval": 3, "retrans_times": 0},
                "retrans_history": {},
            },
            "heart_beat": {"enable": False, "interval": 10},
        }
        return self._request("PUT", "/device_alarm/alarm_push_server", payload)

    def add_rule(self, device_id: int, event_type: str, points: list[dict],
                 channel_id: int = 0, area_type: str = "POLYGON",
                 target_types: list[str] | None = None, threshold: float = 0.7,
                 rule_custom_name: str | None = None):
        """
        Add a perimeter/behavior rule for `device_id` (see `list` command for existing
        device_id/monitor_id mappings). If a "bypass"-type monitor already exists for
        this device_id+channel_id, the rule is appended to it (PUT); otherwise a new
        monitor is created (POST) — a device/channel can only have one bypass monitor.

        points: list of {"x": float, "y": float}, normalized 0.0-1.0, top-left origin.
        event_type: e.g. "INTRUSION", "TRIPWIRE", "SMOKING", "FIGHT", "HOLDWEAPON" —
                    see AlgoCabinEventType enum in the bundled AIOTAP docs
                    (base_interface/alg/warehouse_v2.html) for the full list.
        area_type: "POLYGON" (zone) or a line variant for tripwire-style rules.
        """
        target_types = target_types or ["PERSON"]
        rule_custom_name = rule_custom_name or event_type.lower()

        monitors = self.list_monitors()
        existing = next(
            (m for m in monitors
             if m["common_param"].get("device_id") == device_id
             and m["common_param"].get("channel_id", 0) == channel_id
             and m["common_param"].get("alg_type") == ["bypass"]),
            None,
        )

        new_rule = {
            "areas": [{"areaId": 1, "areaType": area_type, "points": points}],
            "eventType": event_type,
            "extendParams": {
                "cooldownDuration": 600,
                "duration": 1,
                "level": "ALARM_LEVEL",
                "targetMax": 1,
                "targetMin": 0,
                "targetTypes": target_types,
                "threshold": {event_type: threshold},
            },
            "labels": {},
            "masks": [],
            "ruleCustomName": rule_custom_name,
            "ruleId": 1,
        }

        if existing:
            rules = existing["common_param"]["warehouse_v20_param"]["rulesParams"]
            new_rule["areas"][0]["areaId"] = max((a["areaId"] for r in rules for a in r["areas"]), default=0) + 1
            new_rule["ruleId"] = max((r["ruleId"] for r in rules), default=0) + 1
            rules.append(new_rule)
            return self._request("PUT", "/intelli_manager/monitor", existing)

        # No bypass monitor yet for this device/channel — create one.
        #
        # KNOWN LIMITATION (as of 2026-08-24): this branch reliably returns
        # invalid_param on this device/firmware. Only the "append to an
        # existing bypass monitor" branch above has been verified working
        # (proven live against device_id=2 / camera "hik"). The exact field
        # this POST-create path is missing/wrong on is unconfirmed — every
        # field it sends matches an existing monitor's structure byte-for-
        # byte, so the device is validating *something* about brand-new
        # monitor creation beyond field shape. Untested hypothesis worth
        # trying if this ever needs to actually work: create any task for
        # the device once through the box's own web UI first (any algorithm
        # type), then retry this script — device_id=2 only accepted this
        # path after it already had a "face" monitor (201) created via the
        # UI, so a from-scratch first-ever monitor via pure API may need
        # something the UI's own create flow implicitly sets up. Not
        # verified — just the most likely lead if this is revisited.
        #
        # monitor_id must be unique device-wide; nnn convention seen in the wild
        # is <device_id>0<n> (e.g. 203 for device_id=2's 3rd monitor) but any
        # unused integer works. Pick device_id*100 + 99 to stay out of the way.
        monitor_id = device_id * 100 + 99
        stream_id = device_id
        payload = {
            "common_param": {
                "monitor_id": monitor_id,
                "device_id": device_id,
                "channel_type": 1,
                "channel_id": channel_id,
                "monitor_name": rule_custom_name,
                "enable": True,
                "alg_type": ["bypass"],
                "intelli_frame_enable": False,
                "object_frame_cfg": {"enable": True},
                "negative_sample_filter_enable": True,
                "stream_id": stream_id,
                "warehouse_v20_param": {
                    "custom": {},
                    "id": str(monitor_id),
                    "labels": {"algoCabinName": "alert_alarm", "version": "V2.0.0"},
                    "name": str(monitor_id),
                    "rulesParams": [new_rule],
                },
            },
            "extend_param": {"meg_box_param": {"warehouse_param": {"enable": True}}},
        }
        return self._request("POST", "/intelli_manager/monitor", payload)


def parse_point(s: str) -> dict:
    x, y = s.split(",")
    return {"x": float(x), "y": float(y)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["cap", "list", "add-rule", "configure-push", "alarm-history"])
    parser.add_argument("--device-id", type=int, help="target device_id (see `list` for existing mappings)")
    parser.add_argument("--channel-id", type=int, default=0)
    parser.add_argument("--event-type", default="INTRUSION")
    parser.add_argument(
        "--points", nargs="+", type=parse_point, default=None,
        help='Zone points as "x,y x,y x,y ..." using 0.0-1.0 normalized coordinates '
             '(top-left origin). Defaults to the whole frame if omitted.',
    )
    parser.add_argument("--area-type", default="POLYGON",
                         choices=["POLYGON", "SINGLE_LINE", "SINGLE_LINE_BOTH", "MULTI_LINE", "MULTI_LINE_BOTH"])
    parser.add_argument("--threshold", type=float, default=0.7)
    parser.add_argument("--server-path", help='configure-push only: "ip:port" of alarm-bridge.mjs (no protocol prefix — added automatically), e.g. 192.168.1.4:8788')
    parser.add_argument("--link-type", default="http", choices=["http", "https", "ws", "wss"])
    parser.add_argument("--disable-push", action="store_true", help="configure-push only: disable instead of enable")
    parser.add_argument("--minor-types", nargs="+", default=None,
                         help='configure-push only: alarm subtypes to notify on, e.g. --minor-types HOLDWEAPON. '
                              'Omit for every alert_alarm subtype (INTRUSION, SMOKING, HOLDWEAPON, FIGHT, ...). '
                              'alarm-history only: filter query by these minor types.')
    parser.add_argument("--minutes", type=int, default=15, help="alarm-history only: lookback window in minutes")
    args = parser.parse_args()

    host = os.environ.get("MEGVII_HOST", "192.168.1.100")
    user = os.environ.get("MEGVII_USER")
    pw = os.environ.get("MEGVII_PASSWORD")
    if not user or not pw:
        sys.exit("Set MEGVII_USER and MEGVII_PASSWORD environment variables first.")

    client = MegviiClient(host, user, pw)
    client.login()
    print(f"Logged in. session_id={client.session_id[:12]}...")

    try:
        if args.command == "cap":
            print(client.get_intelli_cap())
        elif args.command == "list":
            for m in client.list_monitors():
                cp = m["common_param"]
                print(cp["monitor_id"], cp["monitor_name"], cp["alg_type"], "device_id=", cp["device_id"])
        elif args.command == "add-rule":
            if args.device_id is None:
                sys.exit("--device-id is required (run `list` first to see existing device_id values).")
            points = args.points or [{"x": 0, "y": 0}, {"x": 0, "y": 1}, {"x": 1, "y": 1}, {"x": 1, "y": 0}]
            result = client.add_rule(
                device_id=args.device_id,
                event_type=args.event_type,
                points=points,
                channel_id=args.channel_id,
                area_type=args.area_type,
                threshold=args.threshold,
            )
            print(result)
        elif args.command == "configure-push":
            if not args.server_path:
                sys.exit('--server-path is required, e.g. --server-path 192.168.1.3:8788')
            result = client.configure_alarm_push(
                server_path=args.server_path,
                minor_types=args.minor_types,
                link_type=args.link_type,
                enable=not args.disable_push,
            )
            print(result)
        elif args.command == "alarm-history":
            data = client.query_alarm_history(minutes=args.minutes, minor_types=args.minor_types)
            records = data.get("list", [])
            print(f"total_count={data.get('total_count')} return_count={data.get('return_count')} (last {args.minutes} min)")
            for rec in records:
                print(rec)
    finally:
        client.logout()


if __name__ == "__main__":
    main()
