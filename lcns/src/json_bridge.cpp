// lcns/json_bridge.cpp -- the JsonCpp bridge (goal round 210).
//
// This file also compiles when JsonCpp is absent: then every entry point forwards to the in-house implementation
// in io.cpp and available() reports false, so the substitution is stated rather than hidden.
#include "lcns/json_backend.hpp"

#ifdef LCNS_HAS_JSONCPP
#include <json/json.h>
#endif

#include <sstream>

namespace lcns {
namespace json_backend {

#ifdef LCNS_HAS_JSONCPP
namespace {

Json::Value toJsonCpp(const json::Value& v) {
    switch (v.type()) {
        case json::Type::Null:
            return Json::Value(Json::nullValue);
        case json::Type::Bool:
            return Json::Value(v.asBool());
        case json::Type::Number:
            return Json::Value(v.asNumber());
        case json::Type::String:
            return Json::Value(v.asString());
        case json::Type::Array: {
            Json::Value out(Json::arrayValue);
            for (const json::Value& item : v.items()) {
                out.append(toJsonCpp(item));
            }
            return out;
        }
        case json::Type::Object: {
            Json::Value out(Json::objectValue);
            // members() is insertion ordered, so the recovered key order is preserved in the output.
            for (const auto& kv : v.members()) {
                out[kv.first] = toJsonCpp(kv.second);
            }
            return out;
        }
    }
    return Json::Value(Json::nullValue);
}

json::Value fromJsonCpp(const Json::Value& v) {
    switch (v.type()) {
        case Json::nullValue:
            return json::Value(nullptr);
        case Json::booleanValue:
            return json::Value(v.asBool());
        case Json::intValue:
        case Json::uintValue:
        case Json::realValue:
            return json::Value(v.asDouble());
        case Json::stringValue:
            return json::Value(v.asString());
        case Json::arrayValue: {
            json::Value out = json::Value::array();
            for (const Json::Value& item : v) {
                out.push(fromJsonCpp(item));
            }
            return out;
        }
        case Json::objectValue: {
            json::Value out = json::Value::object();
            for (const auto& name : v.getMemberNames()) {
                out.set(name, fromJsonCpp(v[name]));
            }
            return out;
        }
    }
    return json::Value(nullptr);
}

}  // namespace
#endif  // LCNS_HAS_JSONCPP

bool available() {
#ifdef LCNS_HAS_JSONCPP
    return true;
#else
    return false;
#endif
}

const char* backendName() {
#ifdef LCNS_HAS_JSONCPP
    return "JsonCpp 1.9.5";
#else
    return "in-house";
#endif
}

std::string write(const json::Value& v, bool pretty) {
#ifdef LCNS_HAS_JSONCPP
    Json::StreamWriterBuilder builder;
    builder["indentation"] = pretty ? "  " : "";
    builder["precision"] = 17;                 // the in-house writer also prints 17 significant digits
    const Json::Value root = toJsonCpp(v);
    std::unique_ptr<Json::StreamWriter> writer(builder.newStreamWriter());
    std::ostringstream os;
    writer->write(root, &os);
    std::string text = os.str();
    if (!pretty) {
        while (!text.empty() && (text.back() == '\n' || text.back() == '\r')) {
            text.pop_back();                   // JsonCpp appends a newline; the in-house writer does not
        }
    }
    return text;
#else
    return json::write(v, pretty);
#endif
}

json::Value parse(const std::string& text, std::string* error) {
#ifdef LCNS_HAS_JSONCPP
    Json::CharReaderBuilder builder;
    std::unique_ptr<Json::CharReader> reader(builder.newCharReader());
    Json::Value root;
    std::string errors;
    const bool ok = reader->parse(text.data(), text.data() + text.size(), &root, &errors);
    if (!ok) {
        if (error != nullptr) {
            *error = errors;
        }
        return json::Value(nullptr);
    }
    if (error != nullptr) {
        error->clear();
    }
    return fromJsonCpp(root);
#else
    return json::parse(text, error);
#endif
}

}  // namespace json_backend
}  // namespace lcns
