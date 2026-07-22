from urirun_runtime import v2_cmds


def test_start_command_uses_the_exported_handler():
    assert v2_cmds._COMMANDS["start"] is v2_cmds._cmd_start
