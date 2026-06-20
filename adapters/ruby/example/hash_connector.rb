# Reference urirun connector in Ruby: prints a urirun.bindings.v2 document.
require_relative "../urirun"

c = Urirun::Connector.new("hash", "hash")
c.command("sha256/command/file",
          { required: ["path"], properties: { "path" => { "type" => "string" } } },
          ["sha256sum", "{path}"])
puts c.bindings_json
