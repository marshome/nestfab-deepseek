// lcns/io.cpp
#include "lcns/io.hpp"
#include "lcns/recovery.hpp"

#include "lcns/boolean.hpp"

#include <cmath>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <sstream>

LCNS_STRUCTURAL(module.io);
namespace lcns {
namespace json {
namespace {

const Value& nullValue() {
    static const Value v;
    return v;
}

void escapeInto(std::ostringstream& os, const std::string& s) {
    os << '"';
    for (char c : s) {
        switch (c) {
            case '"': os << "\\\""; break;
            case '\\': os << "\\\\"; break;
            case '\n': os << "\\n"; break;
            case '\r': os << "\\r"; break;
            case '\t': os << "\\t"; break;
            default:
                if (static_cast<unsigned char>(c) < 0x20) {
                    char buf[8];
                    std::snprintf(buf, sizeof(buf), "\\u%04x", c);
                    os << buf;
                } else {
                    os << c;
                }
        }
    }
    os << '"';
}

void writeInto(std::ostringstream& os, const Value& v, bool pretty, int depth) {
    const auto indent = [&](int d) {
        if (!pretty) return;
        os << '\n';
        for (int i = 0; i < d; ++i) os << "  ";
    };
    switch (v.type()) {
        case Type::Null: os << "null"; break;
        case Type::Bool: os << (v.asBool() ? "true" : "false"); break;
        case Type::Number: {
            const double d = v.asNumber();
            if (std::fabs(d - std::floor(d)) < 1e-12 && std::fabs(d) < 1e15) {
                os << static_cast<long long>(d);
            } else {
                char buf[64];
                std::snprintf(buf, sizeof(buf), "%.17g", d);
                os << buf;
            }
            break;
        }
        case Type::String: escapeInto(os, v.asString()); break;
        case Type::Array: {
            if (v.items().empty()) {
                os << "[]";
                break;
            }
            os << '[';
            for (std::size_t i = 0; i < v.items().size(); ++i) {
                if (i) os << ',';
                indent(depth + 1);
                writeInto(os, v.items()[i], pretty, depth + 1);
            }
            indent(depth);
            os << ']';
            break;
        }
        case Type::Object: {
            if (v.members().empty()) {
                os << "{}";
                break;
            }
            os << '{';
            for (std::size_t i = 0; i < v.members().size(); ++i) {
                if (i) os << ',';
                indent(depth + 1);
                escapeInto(os, v.members()[i].first);
                os << (pretty ? ": " : ":");
                writeInto(os, v.members()[i].second, pretty, depth + 1);
            }
            indent(depth);
            os << '}';
            break;
        }
    }
}

// ---------------------------------------------------------------------------
// recursive descent parser
// ---------------------------------------------------------------------------
struct Parser {
    const std::string& s;
    std::size_t i = 0;
    std::string err;

    explicit Parser(const std::string& text) : s(text) {}

    void skip() {
        while (i < s.size() && (s[i] == ' ' || s[i] == '\t' || s[i] == '\n' || s[i] == '\r')) ++i;
    }
    bool fail(const char* what) {
        if (err.empty()) {
            err = std::string(what) + " at offset " + std::to_string(i);
        }
        return false;
    }
    bool literal(const char* lit) {
        const std::size_t n = std::strlen(lit);
        if (s.compare(i, n, lit) != 0) return false;
        i += n;
        return true;
    }

    bool parseString(std::string& out) {
        if (i >= s.size() || s[i] != '"') return false;
        ++i;
        out.clear();
        while (i < s.size()) {
            const char c = s[i++];
            if (c == '"') return true;
            if (c != '\\') {
                out.push_back(c);
                continue;
            }
            if (i >= s.size()) return false;
            const char e = s[i++];
            switch (e) {
                case '"': out.push_back('"'); break;
                case '\\': out.push_back('\\'); break;
                case '/': out.push_back('/'); break;
                case 'b': out.push_back('\b'); break;
                case 'f': out.push_back('\f'); break;
                case 'n': out.push_back('\n'); break;
                case 'r': out.push_back('\r'); break;
                case 't': out.push_back('\t'); break;
                case 'u': {
                    if (i + 4 > s.size()) return false;
                    unsigned code = 0;
                    for (int k = 0; k < 4; ++k) {
                        const char h = s[i + static_cast<std::size_t>(k)];
                        code <<= 4;
                        if (h >= '0' && h <= '9') code |= static_cast<unsigned>(h - '0');
                        else if (h >= 'a' && h <= 'f') code |= static_cast<unsigned>(h - 'a' + 10);
                        else if (h >= 'A' && h <= 'F') code |= static_cast<unsigned>(h - 'A' + 10);
                        else return false;
                    }
                    i += 4;
                    // UTF-8 encode the BMP code point
                    if (code < 0x80) {
                        out.push_back(static_cast<char>(code));
                    } else if (code < 0x800) {
                        out.push_back(static_cast<char>(0xC0 | (code >> 6)));
                        out.push_back(static_cast<char>(0x80 | (code & 0x3F)));
                    } else {
                        out.push_back(static_cast<char>(0xE0 | (code >> 12)));
                        out.push_back(static_cast<char>(0x80 | ((code >> 6) & 0x3F)));
                        out.push_back(static_cast<char>(0x80 | (code & 0x3F)));
                    }
                    break;
                }
                default: return false;
            }
        }
        return false;
    }

    bool parseValue(Value& out) {
        skip();
        if (i >= s.size()) return fail("unexpected end of input");
        const char c = s[i];
        if (c == '{') {
            ++i;
            Value object = Value::object();
            skip();
            if (i < s.size() && s[i] == '}') {
                ++i;
                out = std::move(object);   // {} is an empty object, not a null
                return true;
            }
            while (true) {
                skip();
                std::string key;
                if (!parseString(key)) return fail("expected object key");
                skip();
                if (i >= s.size() || s[i] != ':') return fail("expected ':'");
                ++i;
                Value v;
                if (!parseValue(v)) return false;
                object.set(key, std::move(v));
                skip();
                if (i < s.size() && s[i] == ',') {
                    ++i;
                    continue;
                }
                if (i < s.size() && s[i] == '}') {
                    ++i;
                    break;
                }
                return fail("expected ',' or '}'");
            }
            out = std::move(object);
            return true;
        }
        if (c == '[') {
            ++i;
            Value arr = Value::array();
            skip();
            if (i < s.size() && s[i] == ']') {
                ++i;
                out = std::move(arr);
                return true;
            }
            while (true) {
                Value v;
                if (!parseValue(v)) return false;
                arr.push(std::move(v));
                skip();
                if (i < s.size() && s[i] == ',') {
                    ++i;
                    continue;
                }
                if (i < s.size() && s[i] == ']') {
                    ++i;
                    break;
                }
                return fail("expected ',' or ']'");
            }
            out = std::move(arr);
            return true;
        }
        if (c == '"') {
            std::string str;
            if (!parseString(str)) return fail("bad string");
            out = Value(str);
            return true;
        }
        if (literal("true")) {
            out = Value(true);
            return true;
        }
        if (literal("false")) {
            out = Value(false);
            return true;
        }
        if (literal("null")) {
            out = Value();
            return true;
        }
        // number
        const std::size_t start = i;
        if (i < s.size() && (s[i] == '-' || s[i] == '+')) ++i;
        bool digits = false;
        while (i < s.size() && ((s[i] >= '0' && s[i] <= '9') || s[i] == '.' || s[i] == 'e' ||
                                s[i] == 'E' || s[i] == '+' || s[i] == '-')) {
            if (s[i] >= '0' && s[i] <= '9') digits = true;
            ++i;
        }
        if (!digits) return fail("expected a value");
        out = Value(std::strtod(s.substr(start, i - start).c_str(), nullptr));
        return true;
    }
};

}  // namespace

const Value& Value::at(std::size_t i) const {
    if (type_ != Type::Array || i >= arr_.size()) return nullValue();
    return arr_[i];
}

void Value::set(const std::string& key, Value v) {
    type_ = Type::Object;
    for (auto& kv : obj_) {
        if (kv.first == key) {
            kv.second = std::move(v);
            return;
        }
    }
    obj_.emplace_back(key, std::move(v));
}

bool Value::has(const std::string& key) const {
    if (type_ != Type::Object) return false;
    for (const auto& kv : obj_) {
        if (kv.first == key) return true;
    }
    return false;
}

const Value& Value::get(const std::string& key) const {
    if (type_ == Type::Object) {
        for (const auto& kv : obj_) {
            if (kv.first == key) return kv.second;
        }
    }
    return nullValue();
}

Value parse(const std::string& text, std::string* error) {
    Parser p(text);
    Value v;
    if (!p.parseValue(v)) {
        if (error) *error = p.err.empty() ? "parse error" : p.err;
        return Value();
    }
    p.skip();
    if (p.i != text.size()) {
        if (error) *error = "trailing characters";
        return Value();
    }
    if (error) error->clear();
    return v;
}

std::string write(const Value& v, bool pretty) {
    std::ostringstream os;
    writeInto(os, v, pretty, 0);
    return os.str();
}

}  // namespace json

// ---------------------------------------------------------------------------
namespace {

using json::Value;

const char* kSourceVersion = "5.0 - 68e2d90e72b4 5449 default";  // RE GetBuildVersion

Value ringToJson(const geom::Ring& r) {
    Value a = Value::array();
    for (const auto& p : r) {
        Value pt;
        pt.push(Value(geom::toDouble(p.x)));
        pt.push(Value(geom::toDouble(p.y)));
        a.push(std::move(pt));
    }
    return a;
}

bool jsonToRing(const Value& v, geom::Ring& out) {
    if (!v.isArray()) return false;
    out.clear();
    for (const auto& pt : v.items()) {
        if (!pt.isArray() || pt.items().size() < 2) return false;
        out.push_back(geom::FPoint{geom::toFixed(pt.items()[0].asNumber()),
                                  geom::toFixed(pt.items()[1].asNumber())});
    }
    return true;
}

Value multiToJson(const geom::MultiPolygon& mp) {
    Value arr = Value::array();
    for (const auto& poly : mp) {
        Value o;
        o.set("external", ringToJson(poly.external));
        Value inners = Value::array();
        for (const auto& h : poly.inners) inners.push(ringToJson(h));
        o.set("inners", std::move(inners));
        arr.push(std::move(o));
    }
    return arr;
}

bool jsonToMulti(const Value& v, geom::MultiPolygon& out) {
    if (!v.isArray()) return false;
    out.clear();
    for (const auto& item : v.items()) {
        geom::Polygon poly;
        if (!jsonToRing(item.get("external"), poly.external)) continue;
        for (const auto& h : item.get("inners").items()) {
            geom::Ring r;
            if (jsonToRing(h, r)) poly.inners.push_back(std::move(r));
        }
        out.push_back(std::move(poly));
    }
    return true;
}

void dxfPolyline(std::ostringstream& os, const geom::Ring& r, const std::string& layer) {
    if (r.size() < 3) return;
    os << "0\nPOLYLINE\n8\n" << layer << "\n66\n1\n70\n1\n";
    for (const auto& p : r) {
        os << "0\nVERTEX\n8\n" << layer << "\n10\n"
           << geom::toDouble(p.x) << "\n20\n" << geom::toDouble(p.y) << "\n30\n0\n";
    }
    os << "0\nSEQEND\n8\n" << layer << "\n";
}

}  // namespace

// ---------------------------------------------------------------------------
std::string saveProblem(const Order& order, bool pretty) {
    Value root;
    root.set("source_version", Value(kSourceVersion));
    root.set("objective", Value(static_cast<int>(order.objective)));
    root.set("nesting_origin", Value(static_cast<int>(order.origin)));
    root.set("interpart_gap", Value(order.interpartGap));
    root.set("defect_gap", Value(order.defectGap));
    root.set("shear", Value(order.shear));
    root.set("shear_gap", Value(order.shearGap));
    root.set("shear_corner", Value(order.shearCorner));
    root.set("shear_repulse_from_borders", Value(order.shearRepulseFromBorders));
    root.set("automatic_stop", Value(order.automaticStop));
    root.set("evaluate_intermediate_nestings_as_last",
             Value(order.evaluateIntermediateNestingsAsLast));
    root.set("try_biggest_part_in_corner", Value(order.reorganizeBiggestPartNearOrigin));
    root.set("try_longest_part_in_corner", Value(order.reorganizeLongestPartNearOrigin));
    root.set("common_cut_mode", Value(order.commonCutModeA));
    root.set("common_cut_mode_tag", Value(order.commonCutModeTag));
    root.set("common_cut_safety_preference", Value(order.commonCutSafetyFlag));
    root.set("common_cut_preset", Value(order.commonCutPresetIndex2));
    root.set("common_cut_objective_num", Value(order.commonCutObjectiveNum));
    root.set("common_cut_objective_den", Value(order.commonCutObjectiveDen));
    root.set("multitorch_mode_tag", Value(order.multitorchModeTag));
    root.set("multitorch_nb_torches", Value(order.multitorchNbTorches));
    root.set("multitorch_min_distance", Value(order.multitorchMinDistance));
    root.set("multitorch_max_distance", Value(order.multitorchMaxDistance));
    root.set("multitorch_allowed", Value(order.multitorchAllowed));
    root.set("row_enable", Value(order.rowMode));
    root.set("pipe_enable", Value(order.pipeMode));
    root.set("mark_mode", Value(order.markMode));
    root.set("leather_mode", Value(order.leatherMode));
    root.set("local_engine", Value(order.localEngine));
    root.set("local_max_threads", Value(order.maxThreads));
    root.set("local_max_iterations", Value(order.maxIterations));
    root.set("licence_key_1", Value(order.licenseKey1));
    root.set("licence_key_2", Value(order.licenseKey2));

    Value parts = Value::array();
    for (const auto& p : order.parts) {
        Value j;
        j.set("id", Value(p.id));
        j.set("multiplicity", Value(p.multiplicity));
        j.set("priority", Value(p.priority));
        j.set("user_string", Value(p.userString));
        j.set("variant_user_string", Value(p.variantUserString));
        j.set("extra_gap", Value(p.extraGap));
        j.set("common_cut_mode", Value(p.commonCutMode));
        j.set("hole_status", Value(p.holeStatus));
        j.set("authorizations", Value(p.authorizations));
        j.set("shape", multiToJson(p.rawShape));
        parts.push(std::move(j));
    }
    root.set("parts", std::move(parts));

    Value sheets = Value::array();
    for (const auto& s : order.sheets) {
        Value j;
        j.set("id", Value(s.id));
        j.set("width", Value(s.width));
        j.set("height", Value(s.height));
        j.set("quantity", Value(s.quantity));
        j.set("price", Value(s.price));
        j.set("priority", Value(s.priority));
        j.set("grain_direction", Value(s.grainDirection));
        j.set("defect_gap", Value(s.defectGap));
        j.set("non_rectangular", Value(s.nonRectangular));
        j.set("reusable", Value(s.reusable));
        j.set("user_string", Value(s.userString));
        j.set("shape", multiToJson(s.shape));
        sheets.push(std::move(j));
    }
    root.set("sheets", std::move(sheets));
    return json::write(root, pretty);
}

bool loadProblem(const std::string& text, Order& out, std::string* error) {
    const Value root = json::parse(text, error);
    if (root.isNull()) return false;

    out = Order();
    out.objective = static_cast<Objective>(root.get("objective").asInt(3));
    out.origin = static_cast<NestingOrigin>(root.get("nesting_origin").asInt(0));
    out.interpartGap = root.get("interpart_gap").asNumber(0.0);
    out.defectGap = root.get("defect_gap").asNumber(0.0);
    out.shear = root.get("shear").asBool(false);
    out.shearGap = root.get("shear_gap").asNumber(0.0);
    out.shearCorner = root.get("shear_corner").asBool(false);
    out.shearRepulseFromBorders = root.get("shear_repulse_from_borders").asBool(false);
    out.automaticStop = root.get("automatic_stop").asBool(false);
    out.evaluateIntermediateNestingsAsLast =
        root.get("evaluate_intermediate_nestings_as_last").asBool(false);
    out.reorganizeBiggestPartNearOrigin = root.get("try_biggest_part_in_corner").asBool(false);
    out.reorganizeLongestPartNearOrigin = root.get("try_longest_part_in_corner").asBool(false);
    out.commonCutModeA = root.get("common_cut_mode").asInt(0);
    out.commonCutModeTag = root.get("common_cut_mode_tag").asInt(0);
    out.commonCutSafetyFlag = root.get("common_cut_safety_preference").asInt(0);
    out.commonCutPresetIndex2 = root.get("common_cut_preset").asInt(0);
    out.commonCutObjectiveNum = root.get("common_cut_objective_num").asNumber(1.0);
    out.commonCutObjectiveDen = root.get("common_cut_objective_den").asNumber(1.0);
    out.multitorchModeTag = root.get("multitorch_mode_tag").asInt(0);
    out.multitorchNbTorches = root.get("multitorch_nb_torches").asInt(0);
    out.multitorchMinDistance = root.get("multitorch_min_distance").asNumber(0.0);
    out.multitorchMaxDistance = root.get("multitorch_max_distance").asNumber(0.0);
    out.multitorchAllowed = root.get("multitorch_allowed").asBool(false);
    out.rowMode = root.get("row_enable").asBool(false);
    out.pipeMode = root.get("pipe_enable").asBool(false);
    out.markMode = root.get("mark_mode").asBool(false);
    out.leatherMode = root.get("leather_mode").asBool(false);
    out.localEngine = root.get("local_engine").asBool(false);
    out.maxThreads = root.get("local_max_threads").asInt(1);
    out.maxIterations = root.get("local_max_iterations").asInt(1000);
    out.licenseKey1 = root.get("licence_key_1").asString();
    out.licenseKey2 = root.get("licence_key_2").asString();

    for (const auto& j : root.get("parts").items()) {
        Part p;
        p.id = j.get("id").asInt(0);
        p.multiplicity = j.get("multiplicity").asInt(1);
        p.priority = j.get("priority").asInt(0);
        p.userString = j.get("user_string").asString();
        p.variantUserString = j.get("variant_user_string").asString();
        p.extraGap = j.get("extra_gap").asNumber(0.0);
        p.commonCutMode = j.get("common_cut_mode").asInt(0);
        p.holeStatus = j.get("hole_status").asInt(0);
        p.authorizations = j.get("authorizations").asInt(0);
        jsonToMulti(j.get("shape"), p.rawShape);
        p.shape = p.rawShape;
        out.parts.push_back(std::move(p));
    }

    for (const auto& j : root.get("sheets").items()) {
        Sheet s;
        s.id = j.get("id").asInt(0);
        s.width = j.get("width").asNumber(0.0);
        s.height = j.get("height").asNumber(0.0);
        s.quantity = j.get("quantity").asInt(1);
        s.price = j.get("price").asNumber(0.0);
        s.priority = j.get("priority").asInt(0);
        s.grainDirection = j.get("grain_direction").asInt(0);
        s.defectGap = j.get("defect_gap").asNumber(0.0);
        s.nonRectangular = j.get("non_rectangular").asBool(false);
        s.reusable = j.get("reusable").asBool(true);
        s.userString = j.get("user_string").asString();
        jsonToMulti(j.get("shape"), s.shape);
        out.sheets.push_back(std::move(s));
    }
    return true;
}

std::string saveSolution(const Solution& solution, const Order& order, bool pretty) {
    Value root;
    root.set("source_version", Value(kSourceVersion));
    root.set("valid", Value(solution.valid));
    root.set("fill_ratio", Value(solution.fillRatio()));
    root.set("used_surface", Value(solution.usedSurface()));
    root.set("nestings_count", Value(static_cast<int>(solution.nestings.size())));

    Value nestings = Value::array();
    for (const auto& n : solution.nestings) {
        Value jn;
        jn.set("sheet", Value(n.sheetIndex));
        jn.set("used_surface", Value(n.usedSurface));
        jn.set("sheet_area", Value(n.sheetArea));
        Value parts = Value::array();
        for (const auto& np : n.parts) {
            Value jp;
            jp.set("part", Value(np.partIndex));
            jp.set("instance", Value(np.instance));
            jp.set("x", Value(np.x));
            jp.set("y", Value(np.y));
            jp.set("angle", Value(np.angle));
            jp.set("flipped", Value(np.flipped));
            if (np.partIndex >= 0 && np.partIndex < static_cast<int>(order.parts.size())) {
                const geom::MultiPolygon placed =
                    placedPolygon(order.parts[static_cast<std::size_t>(np.partIndex)].shape, np);
                jp.set("shape", multiToJson(placed));
            }
            parts.push(std::move(jp));
        }
        jn.set("parts", std::move(parts));
        nestings.push(std::move(jn));
    }
    root.set("nestings", std::move(nestings));
    return json::write(root, pretty);
}

bool loadSolution(const std::string& text, const Order& order, Solution& out, std::string* error) {
    (void)order;
    const Value root = json::parse(text, error);
    if (root.isNull()) return false;
    out = Solution();
    out.valid = root.get("valid").asBool(true);
    for (const auto& jn : root.get("nestings").items()) {
        Nesting n;
        n.sheetIndex = jn.get("sheet").asInt(0);
        n.usedSurface = jn.get("used_surface").asNumber(0.0);
        n.sheetArea = jn.get("sheet_area").asNumber(0.0);
        for (const auto& jp : jn.get("parts").items()) {
            NestedPart np;
            np.partIndex = jp.get("part").asInt(-1);
            np.instance = jp.get("instance").asInt(0);
            np.x = jp.get("x").asNumber(0.0);
            np.y = jp.get("y").asNumber(0.0);
            np.angle = jp.get("angle").asNumber(0.0);
            np.flipped = jp.get("flipped").asBool(false);
            n.parts.push_back(np);
        }
        out.nestings.push_back(std::move(n));
    }
    return true;
}

// ---------------------------------------------------------------------------
LCNS_STRUCTURAL(io.dxf);
std::string toDxf(const Order& order, const Solution& solution) {
    std::ostringstream os;
    os << "0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n0\nENDSEC\n";
    os << "0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLAYER\n70\n3\n";
    for (const char* layer : {"SHEET", "PART", "HOLES"}) {
        os << "0\nLAYER\n2\n" << layer << "\n70\n0\n62\n7\n6\nCONTINUOUS\n";
    }
    os << "0\nENDTAB\n0\nENDSEC\n";
    os << "0\nSECTION\n2\nENTITIES\n";

    // every sheet footprint
    for (const auto& s : order.sheets) {
        dxfPolyline(os, geom::orientCCW(sheetPolygon(s).external), "SHEET");
    }
    // every placed part
    for (const auto& n : solution.nestings) {
        for (const auto& np : n.parts) {
            if (np.partIndex < 0 || np.partIndex >= static_cast<int>(order.parts.size())) continue;
            const Part& part = order.parts[static_cast<std::size_t>(np.partIndex)];
            const geom::MultiPolygon placed = placedPolygon(part.shape, np);
            for (const auto& poly : placed) {
                dxfPolyline(os, geom::orientCCW(poly.external), "PART");
                for (const auto& h : poly.inners) dxfPolyline(os, h, "HOLES");
            }
        }
    }
    os << "0\nENDSEC\n0\nEOF\n";
    return os.str();
}

bool writeDxf(const std::string& path, const Order& order, const Solution& solution) {
    std::ofstream f(path, std::ios::binary);
    if (!f) return false;
    f << toDxf(order, solution);
    return f.good();
}

geom::MultiPolygon offcuts(const Order& order, const Solution& solution) {
    geom::MultiPolygon result;
    for (const auto& n : solution.nestings) {
        if (n.sheetIndex < 0 || n.sheetIndex >= static_cast<int>(order.sheets.size())) continue;
        const Sheet& sheet = order.sheets[static_cast<std::size_t>(n.sheetIndex)];
        geom::MultiPolygon remaining;
        remaining.push_back(sheetPolygon(sheet));
        // subtract every placed part; parts that overlap are handled by the boolean kernel
        for (const auto& np : n.parts) {
            if (np.partIndex < 0 || np.partIndex >= static_cast<int>(order.parts.size())) continue;
            const Part& part = order.parts[static_cast<std::size_t>(np.partIndex)];
            const geom::MultiPolygon placed = placedPolygon(part.shape, np);
            remaining = geom::subtract(remaining, placed);
            if (remaining.empty()) break;
        }
        // keep only offcuts large enough to be worth recovering
        const double minDim = order.usedSurfaceMinOffcutDimension;
        for (auto& poly : remaining) {
            const geom::Box b = geom::bounds(poly.external);
            const double area0 = geom::area(poly.external);
            if (minDim > 0.0 && (b.width() < minDim || b.height() < minDim)) continue;
            if (order.usedSurfaceMinOffcutArea > 0.0 && area0 < order.usedSurfaceMinOffcutArea) {
                continue;
            }
            result.push_back(std::move(poly));
        }
    }
    return result;
}

}  // namespace lcns
