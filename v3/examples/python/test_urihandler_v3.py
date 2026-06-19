import re
import unittest

from urihandler_v3 import EXECUTORS, dispatch, hash_uri, parse_uri, resolve_route, translate


def device_led_set(target, args, payload, descriptor):
    return {
        "descriptor": descriptor,
        "ok": True,
        "payload": payload,
        "state": args[0],
        "target": target,
    }


registry = {
    "artifact": {
        "build": {
            "frontend": {
                "adapter": "spawn",
                "config": {"command": ["npm", "run", "build"]},
                "kind": "process",
            }
        }
    },
    "cli": {"git": {"status": {"adapter": "spawn", "config": {"command": ["git", "status"]}, "kind": "cli"}}},
    "device": {"led": {"set": {"adapter": "local-function", "kind": "function", "ref": device_led_set}}},
    "log": {
        "info": {
            "user-created": {
                "adapter": "local-function",
                "kind": "function",
                "ref": lambda target, args, payload, descriptor: {
                    "args": args,
                    "descriptor": descriptor,
                    "event": "user-created",
                    "ok": True,
                    "payload": payload,
                    "sink": target,
                },
            }
        }
    },
    "mqtt": {"publish": {"home": {"adapter": "mqtt-publish", "config": {"topicPrefix": "home"}, "kind": "mqtt"}}},
    "service": {
        "user": {
            "create": {
                "adapter": "fetch",
                "config": {"method": "POST", "url": "http://user-service.local/api/users"},
                "kind": "http",
            }
        }
    },
    "shell": {
        "system": {
            "restart": {
                "adapter": "shell-template",
                "config": {"template": "systemctl restart {0}"},
                "kind": "shell",
            }
        }
    },
}


class UriHandlerV3Tests(unittest.TestCase):
    def test_parse_and_translate(self):
        descriptor = parse_uri("service://api/user/create/basic?trace=1#ops")
        self.assertEqual(translate(descriptor)["route"], ["service", "user", "create"])
        self.assertEqual(translate(descriptor)["args"], ["basic"])

    def test_dispatch_executor_kinds(self):
        self.assertEqual(dispatch("device://device-01/led/set/on", registry, {"source": "test"})["state"], "on")
        self.assertEqual(dispatch("service://api/user/create/basic", registry, {"name": "Ada"})["type"], "http")
        self.assertEqual(dispatch("cli://local/git/status", registry)["command"], ["git", "status"])
        self.assertEqual(dispatch("shell://local/system/restart/nginx", registry)["command"], "systemctl restart nginx")
        self.assertEqual(
            dispatch("mqtt://broker/publish/home/kitchen/light/on", registry, {"on": True})["topic"],
            "home/broker/kitchen/light/on",
        )
        self.assertEqual(dispatch("artifact://runner/build/frontend/release", registry)["command"], ["npm", "run", "build", "release"])

    def test_cache_and_custom_executor(self):
        runtime_cache = {}
        self.assertEqual(dispatch("service://api/user/create/basic", registry, {}, runtime_cache)["type"], "http")
        self.assertEqual(len(runtime_cache), 1)
        route_entry = resolve_route(translate(parse_uri("service://api/user/create/basic")), registry)
        self.assertIs(next(iter(runtime_cache.values())), route_entry)

        custom_executors = {
            **EXECUTORS,
            "fetch": lambda ctx: {
                "adapter": "custom-fetch",
                "args": ctx["args"],
                "payload": ctx["payload"],
                "target": ctx["target"],
                "url": ctx["routeEntry"]["config"]["url"],
            },
        }
        self.assertEqual(
            dispatch("service://api/user/create/basic", registry, {}, {}, custom_executors)["adapter"],
            "custom-fetch",
        )

    def test_invalid_routes_and_executors(self):
        with self.assertRaises(ValueError):
            translate(parse_uri("cli://local/git"))
        with self.assertRaises(KeyError):
            dispatch("device://device-01/motor/set/on", registry)
        with self.assertRaises(ValueError):
            dispatch("device://device-01/led/set/on", registry, {}, {}, {})

    def test_hash_uri(self):
        self.assertRegex(hash_uri("device://device-01/led/set/on"), re.compile(r"^[a-f0-9]{64}$"))


if __name__ == "__main__":
    unittest.main()
