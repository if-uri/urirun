//! urirun — Rust SDK for building `urirun.bindings.v2` documents (no dependencies).
//!
//! The caller passes already-valid JSON fragments for the input schema and the
//! argv array, and the SDK assembles the standardized document.

pub const BINDINGS_VERSION: &str = "urirun.bindings.v2";

/// Connector accumulates URI command bindings for one scheme.
pub struct Connector {
    id: String,
    scheme: String,
    target: String,
    members: Vec<String>,
}

impl Connector {
    pub fn new(id: &str, scheme: &str) -> Self {
        Connector { id: id.into(), scheme: scheme.into(), target: "host".into(), members: Vec::new() }
    }

    pub fn target(mut self, target: &str) -> Self {
        self.target = target.into();
        self
    }

    /// Declare a route. `schema_json` and `argv_json` must be valid JSON.
    pub fn command(&mut self, route: &str, schema_json: &str, argv_json: &str) -> &mut Self {
        let uri = format!("{}://{}/{}", self.scheme, self.target, route);
        self.members.push(format!(
            r#""{u}":{{"uri":"{u}","kind":"command","adapter":"argv-template","inputSchema":{s},"argv":{a},"meta":{{"connector":"{c}"}},"policy":{{"allowExecute":true}}}}"#,
            u = uri, s = schema_json, a = argv_json, c = self.id
        ));
        self
    }

    pub fn bindings_json(&self) -> String {
        format!(r#"{{"version":"{}","bindings":{{{}}}}}"#, BINDINGS_VERSION, self.members.join(","))
    }
}
