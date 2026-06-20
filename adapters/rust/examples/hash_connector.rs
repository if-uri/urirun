// Reference urirun connector in Rust: prints a urirun.bindings.v2 document.
use urirun::Connector;

fn main() {
    let mut c = Connector::new("hash", "hash");
    c.command(
        "sha256/command/file",
        r#"{"type":"object","additionalProperties":false,"required":["path"],"properties":{"path":{"type":"string"}}}"#,
        r#"["sha256sum","{path}"]"#,
    );
    println!("{}", c.bindings_json());
}
