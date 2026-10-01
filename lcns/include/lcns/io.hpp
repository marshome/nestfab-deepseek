// lcns/io.hpp -- JSON serialisation (problem/solution) and DXF/SVG export.
//
// The original uses JsonCpp for its problem/solution payloads (`c:\Temp\cns.pb.json`,
// `UnSerializeSolution` 0x1C5F0, `CreateProblem` 0x1EE50) and `DrawDxf` for DXF output
// (GenerateDxfNesting 0xBF70). It also emits SVG through the DrawSVG family and an HTML
// report that references the `cns_solution.css` asset.
//
// This header provides a self contained JSON value type, parser and writer (no third party
// dependency), plus problem/solution (de)serialisation and a DXF writer. The JSON keys used
// for the problem are the ones the reverse engineering recovered from the JSON schema of
// `..\structure\text_io.cpp` (strings at 0x9DA300..0x9DB010).
#pragma once

#include <cstdint>
#include <map>
#include <memory>
#include <string>
#include <vector>

#include "lcns/model.hpp"

namespace lcns {
namespace json {

class Value;
using Array = std::vector<Value>;
using Object = std::vector<std::pair<std::string, Value>>;  // insertion ordered

enum class Type { Null, Bool, Number, String, Array, Object };

class Value {
public:
    Value() = default;
    Value(std::nullptr_t) {}
    Value(bool b) : type_(Type::Bool), bool_(b) {}
    Value(double d) : type_(Type::Number), num_(d) {}
    Value(int i) : type_(Type::Number), num_(static_cast<double>(i)) {}
    Value(std::int64_t i) : type_(Type::Number), num_(static_cast<double>(i)) {}
    Value(std::size_t i) : type_(Type::Number), num_(static_cast<double>(i)) {}
    Value(const char* s) : type_(Type::String), str_(s ? s : "") {}
    Value(std::string s) : type_(Type::String), str_(std::move(s)) {}

    // empty containers with their type already set (a default Value is Null, not an empty
    // object or array, so these are the only correct way to start one)
    static Value array() {
        Value v;
        v.type_ = Type::Array;
        return v;
    }
    static Value object() {
        Value v;
        v.type_ = Type::Object;
        return v;
    }

    Type type() const { return type_; }
    bool isNull() const { return type_ == Type::Null; }
    bool isNumber() const { return type_ == Type::Number; }
    bool isString() const { return type_ == Type::String; }
    bool isArray() const { return type_ == Type::Array; }
    bool isObject() const { return type_ == Type::Object; }

    bool asBool(bool def = false) const { return type_ == Type::Bool ? bool_ : def; }
    double asNumber(double def = 0.0) const { return type_ == Type::Number ? num_ : def; }
    int asInt(int def = 0) const { return type_ == Type::Number ? static_cast<int>(num_) : def; }
    const std::string& asString() const { return str_; }

    // array access
    Array& items() { return arr_; }
    const Array& items() const { return arr_; }
    std::size_t size() const { return type_ == Type::Array ? arr_.size() : obj_.size(); }
    void push(Value v) {
        type_ = Type::Array;
        arr_.push_back(std::move(v));
    }
    const Value& at(std::size_t i) const;

    // object access
    void set(const std::string& key, Value v);
    bool has(const std::string& key) const;
    const Value& get(const std::string& key) const;   // returns a null value when missing
    const Object& members() const { return obj_; }

private:
    Type type_ = Type::Null;
    bool bool_ = false;
    double num_ = 0.0;
    std::string str_;
    Array arr_;
    Object obj_;
};

// Parses `text`. On error returns a null value and fills `error` (when given).
Value parse(const std::string& text, std::string* error = nullptr);
std::string write(const Value& v, bool pretty = false);

}  // namespace json

// ---------------------------------------------------------------------------
// problem / solution (de)serialisation
// ---------------------------------------------------------------------------
// Mirrors the recovered JSON schema: keys such as source_version, parts, sheets,
// incompatible_sheets, hole_status, defect_gap, grain_direction, assembly_group, quality,
// try_biggest_part_in_corner, enable_common_cut_nesting, use_multitorch_tiling, cns_force_cloud.
std::string saveProblem(const Order& order, bool pretty = false);
bool loadProblem(const std::string& text, Order& out, std::string* error = nullptr);

std::string saveSolution(const Solution& solution, const Order& order, bool pretty = false);
bool loadSolution(const std::string& text, const Order& order, Solution& out,
                  std::string* error = nullptr);

// ---------------------------------------------------------------------------
// DXF (RE: GenerateDxfNesting 0xBF70 -> DrawDxf)
// ---------------------------------------------------------------------------
// Writes an ASCII R12 DXF: HEADER, TABLES (one layer per part/sheet class) and ENTITIES
// (closed POLYLINE per ring, with outer rings on layer SHEET/PART and holes on *HOLES).
std::string toDxf(const Order& order, const Solution& solution);
bool writeDxf(const std::string& path, const Order& order, const Solution& solution);

// Offcut / remnant polygons of a nesting (RE SetOffcutEvaluation + the offcut SVG layer).
geom::MultiPolygon offcuts(const Order& order, const Solution& solution);

}  // namespace lcns
