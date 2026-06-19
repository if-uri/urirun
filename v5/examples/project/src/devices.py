from urihandler.v4 import uri_handler


@uri_handler("device://device-01/led/set/on", kind="function", adapter="local-function", ref="devices.led_set")
def led_set(target, args, payload, descriptor):
    return {"ok": True, "target": target, "state": args[0], "payload": payload}
