#!/usr/bin/env bash
# Scaffold a starter urirun connector in a chosen language.
#
# Usage: adapters/new-connector.sh --lang LANG <id> [scheme] [out-dir]
#   --lang   go | php | ruby | perl | bash | rust
#            (Python and JS scaffolds live elsewhere)
#   <id>     kebab-case connector id (e.g. weather-now)
#   [scheme] URI scheme (default: id with dashes removed)
#   [out]    output directory (default: ./urirun-connector-<id>-<lang>)
#
# The generated connector emits the same urirun.bindings.v2 contract as every
# other language, so `urirun validate/compile/list` works on its output.
set -euo pipefail

LANG_CHOICE=""
if [ "${1:-}" = "--lang" ]; then LANG_CHOICE="${2:-}"; shift 2; fi
ID="${1:?usage: new-connector.sh --lang go|php|ruby|perl|bash|rust <id> [scheme] [out-dir]}"
SCHEME="${2:-${ID//-/}}"
OUT="${3:-./urirun-connector-${ID}-${LANG_CHOICE}}"
case "$LANG_CHOICE" in
  go|php|ruby|perl|bash|rust) ;;
  *) echo "error: --lang must be one of: go php ruby perl bash rust" >&2; exit 2;;
esac
[ -e "$OUT" ] && { echo "target already exists: $OUT" >&2; exit 1; }
mkdir -p "$OUT"

RUN=""
case "$LANG_CHOICE" in
go)
  RUN="go run ."
  cat > "$OUT/go.mod" <<EOF
module example.com/urirun-connector-${ID}

go 1.21

require github.com/if-uri/urirun/adapters/go v0.0.0
EOF
  cat > "$OUT/main.go" <<EOF
package main

import (
	"fmt"

	urirun "github.com/if-uri/urirun/adapters/go"
)

func main() {
	c := urirun.NewConnector("${ID}", "${SCHEME}")
	c.Command(
		"example/command/run",
		urirun.Schema{
			Required:   []string{"input"},
			Properties: map[string]any{"input": map[string]any{"type": "string"}},
		},
		[]string{"echo", "{input}"},
	)
	fmt.Println(c.BindingsJSON())
}
EOF
  ;;
php)
  RUN="php connector.php"
  cat > "$OUT/connector.php" <<EOF
<?php
declare(strict_types=1);
// require the urirun PHP SDK (composer require if-uri/urirun, or path include)
require __DIR__ . '/Urirun.php';

\$c = new Urirun\\Connector('${ID}', '${SCHEME}');
\$c->command(
    'example/command/run',
    ['required' => ['input'], 'properties' => ['input' => ['type' => 'string']]],
    ['echo', '{input}']
);
echo \$c->bindingsJson();
EOF
  ;;
ruby)
  RUN="ruby connector.rb"
  cat > "$OUT/connector.rb" <<EOF
# require the urirun Ruby SDK (gem 'urirun', or place urirun.rb beside this file)
require_relative "urirun"

c = Urirun::Connector.new("${ID}", "${SCHEME}")
c.command("example/command/run",
          { required: ["input"], properties: { "input" => { "type" => "string" } } },
          ["echo", "{input}"])
puts c.bindings_json
EOF
  ;;
perl)
  RUN="perl connector.pl"
  cat > "$OUT/connector.pl" <<EOF
use strict;
use warnings;
# place Urirun.pm beside this file, or install the urirun Perl SDK
use lib ".";
use Urirun;

my \$c = Urirun->new("${ID}", "${SCHEME}");
\$c->command(
    "example/command/run",
    { required => ["input"], properties => { input => { type => "string" } } },
    ["echo", "{input}"],
);
print \$c->bindings_json;
EOF
  ;;
bash)
  RUN="bash connector.sh"
  cat > "$OUT/connector.sh" <<EOF
#!/usr/bin/env bash
# place urirun.sh beside this file (from adapters/bash)
set -euo pipefail
. "\$(dirname "\$0")/urirun.sh"

schema='{"type":"object","additionalProperties":false,"required":["input"],"properties":{"input":{"type":"string"}}}'
argv='["echo","{input}"]'
member="\$(urirun_command ${SCHEME} host "example/command/run" "\$schema" "\$argv" ${ID})"
urirun_document "\$member"
EOF
  chmod +x "$OUT/connector.sh"
  ;;
rust)
  RUN="cargo run"
  cat > "$OUT/Cargo.toml" <<EOF
[package]
name = "urirun-connector-${ID//-/_}"
version = "0.1.0"
edition = "2021"

# add the urirun Rust SDK (path or git dependency):
# urirun = { git = "https://github.com/if-uri/urirun", package = "urirun" }
EOF
  mkdir -p "$OUT/src"
  cat > "$OUT/src/main.rs" <<EOF
use urirun::Connector;

fn main() {
    let mut c = Connector::new("${ID}", "${SCHEME}");
    c.command(
        "example/command/run",
        r#"{"type":"object","additionalProperties":false,"required":["input"],"properties":{"input":{"type":"string"}}}"#,
        r#"["echo","{input}"]"#,
    );
    println!("{}", c.bindings_json());
}
EOF
  ;;
esac

cat > "$OUT/README.md" <<EOF
# urirun-connector-${ID} (${LANG_CHOICE})

Starter urirun connector. Emit and run its bindings:

\`\`\`bash
${RUN} > bindings.json
urirun validate bindings.json
urirun compile bindings.json --out registry.json
urirun list registry.json
\`\`\`

Wire the urirun ${LANG_CHOICE} SDK from adapters/${LANG_CHOICE}/ (see its README).
Contract: https://docs.ifuri.com/generating-connectors.html
EOF

echo "scaffolded ${LANG_CHOICE} connector '${ID}' (scheme ${SCHEME}://) -> $OUT"
