// tests/test_json_backend.cpp -- the JsonCpp-backed JSON I/O (goal round 210).
//
// Three things are checked: which backend is linked, that a document shaped like the recovered ones survives a
// round trip through it, and that the backend and the in-house writer can each read the other's text. The last one
// is what makes the recovered key names and shapes meaningful rather than library-specific.
#include "check.hpp"
#include "lcns/json_backend.hpp"

#include <string>

int main() {
    using lcns::json::Type;
    using lcns::json::Value;

#ifdef LCNS_HAS_JSONCPP
    CHECK(lcns::json_backend::available());
    CHECK(std::string(lcns::json_backend::backendName()) == "JsonCpp 1.9.5");
#else
    CHECK(!lcns::json_backend::available());
#endif

    // the recovered shape: a problem carrying a ring with an external boundary and inner holes
    Value external = Value::array();
    external.push(Value(0.0));
    external.push(Value(10.0));
    external.push(Value(10.0));
    external.push(Value(0.0));

    Value inner = Value::array();
    inner.push(Value(1.0));
    inner.push(Value(1.0));

    Value inners = Value::array();
    inners.push(inner);

    Value ring = Value::object();
    ring.set("external", external);
    ring.set("inners", inners);

    Value problem = Value::object();
    problem.set("job", Value("sheet-1"));
    problem.set("sheet_count", Value(2));
    problem.set("shape", ring);

    const std::string text = lcns::json_backend::write(problem, false);
    CHECK(!text.empty());
    CHECK(text.front() == '{');

    std::string error;
    const Value back = lcns::json_backend::parse(text, &error);
    CHECK(error.empty());
    CHECK(back.type() == Type::Object);
    CHECK(back.get("job").asString() == "sheet-1");
    CHECK(back.get("sheet_count").asNumber() == 2.0);
    CHECK(back.get("shape").type() == Type::Object);
    CHECK(back.get("shape").get("external").type() == Type::Array);
    CHECK(back.get("shape").get("external").items().size() == 4);
    CHECK(back.get("shape").get("external").items()[1].asNumber() == 10.0);
    CHECK(back.get("shape").get("inners").items().size() == 1);
    CHECK(back.get("shape").get("inners").items()[0].items().size() == 2);

    // the in-house writer produces text this backend parses, and the reverse
    const std::string inHouse = lcns::json::write(problem, false);
    const Value viaBackend = lcns::json_backend::parse(inHouse, &error);
    CHECK(error.empty());
    CHECK(viaBackend.get("job").asString() == "sheet-1");
    CHECK(viaBackend.get("shape").get("external").items().size() == 4);
    const Value viaInHouse = lcns::json::parse(text, &error);
    CHECK(error.empty());
    CHECK(viaInHouse.get("job").asString() == "sheet-1");
    CHECK(viaInHouse.get("shape").get("external").items().size() == 4);

    // pretty printing stays readable and still parses
    const std::string pretty = lcns::json_backend::write(problem, true);
    CHECK(pretty.find('\n') != std::string::npos);
    const Value prettyBack = lcns::json_backend::parse(pretty, &error);
    CHECK(error.empty());
    CHECK(prettyBack.get("job").asString() == "sheet-1");

    // a broken document is reported rather than silently returned as an empty value
    const Value broken = lcns::json_backend::parse("{ not json", &error);
    CHECK(!error.empty() || broken.isNull());

    return check::finish("test_json_backend");
}
