# urirun — Ruby SDK for building urirun.bindings.v2 documents.
require "json"

module Urirun
  BINDINGS_VERSION = "urirun.bindings.v2"

  # Connector accumulates URI command bindings for one scheme.
  class Connector
    def initialize(id, scheme, target: "host")
      @id = id
      @scheme = scheme
      @target = target
      @bindings = {}
    end

    # Declare a route as an argv template filled from the validated payload.
    def command(route, schema, argv)
      uri = "#{@scheme}://#{@target}/#{route}"
      input = { "type" => "object", "additionalProperties" => false,
                "properties" => (schema[:properties] || {}) }
      req = schema[:required]
      input["required"] = req if req && !req.empty?
      @bindings[uri] = {
        "uri" => uri, "kind" => "command", "adapter" => "argv-template",
        "inputSchema" => input, "argv" => argv,
        "meta" => { "connector" => @id }, "policy" => { "allowExecute" => true }
      }
      self
    end

    def bindings
      { "version" => BINDINGS_VERSION, "bindings" => @bindings }
    end

    def bindings_json
      JSON.pretty_generate(bindings)
    end
  end
end
