// tests/test_io.cpp -- JSON reader/writer, problem/solution round trip, DXF, offcuts.
#include "check.hpp"
#include "lcns/boolean.hpp"
#include "lcns/io.hpp"

using namespace lcns;
using namespace lcns::json;

int main() {
    // --- JSON writer ---
    {
        Value root;
        root.set("name", Value("cns"));
        root.set("version", Value(5.0));
        root.set("count", Value(3));
        root.set("enabled", Value(true));
        root.set("nothing", Value());
        Value arr;
        arr.push(Value());
        arr.items().clear();
        arr.push(Value(1));
        arr.push(Value(2.5));
        root.set("values", std::move(arr));
        const std::string compact = write(root, false);
        CHECK(compact.find("\"name\":\"cns\"") != std::string::npos);
        CHECK(compact.find("\"count\":3") != std::string::npos);
        CHECK(compact.find("\"version\":5") != std::string::npos);
        CHECK(compact.find("null") != std::string::npos);
        CHECK(compact.find("[1,2.5]") != std::string::npos);
        const std::string pretty = write(root, true);
        CHECK(pretty.find('\n') != std::string::npos);
        CHECK(pretty.size() > compact.size());
    }

    // --- JSON escapes ---
    {
        Value v;
        v.set("s", Value("quote\" back\\slash\nnewline\ttab"));
        const std::string text = write(v);
        CHECK(text.find("\\\"") != std::string::npos);
        CHECK(text.find("\\\\") != std::string::npos);
        CHECK(text.find("\\n") != std::string::npos);
        std::string err;
        const Value back = parse(text, &err);
        CHECK(err.empty());
        CHECK(back.get("s").asString() == "quote\" back\\slash\nnewline\ttab");
    }

    // --- JSON parser: nesting, numbers, unicode escapes, errors ---
    {
        std::string err;
        const Value v = parse(R"({"a":[1,2,{"b":-3.5e2}],"c":"\u0041","d":false})", &err);
        CHECK(err.empty());
        CHECK(v.isObject());
        CHECK(v.get("a").isArray());
        CHECK(v.get("a").items().size() == 3);
        CHECK_NEAR(v.get("a").items()[2].get("b").asNumber(), -350.0, 1e-9);
        CHECK(v.get("c").asString() == "A");
        CHECK(v.get("d").asBool(true) == false);
        CHECK(v.get("missing").isNull());
        CHECK(v.has("a"));
        CHECK(!v.has("zzz"));

        std::string e1;
        parse("{", &e1);
        CHECK(!e1.empty());
        std::string e2;
        parse("{\"a\":1}trailing", &e2);
        CHECK(!e2.empty());
        std::string e3;
        parse("[1,]", &e3);
        CHECK(!e3.empty());
    }

    // --- empty containers keep their type (regression: `{}` and `[]` used to collapse to null) ---
    {
        std::string err;
        const Value obj = parse("{}", &err);
        CHECK(err.empty());
        CHECK_MSG(obj.isObject(), "an empty object must parse as an object, not null");
        CHECK(!obj.isNull());
        CHECK(obj.members().empty());
        CHECK(!obj.has("anything"));
        CHECK(obj.get("anything").isNull());
        CHECK(write(obj) == "{}");

        const Value arr = parse("[]", &err);
        CHECK(err.empty());
        CHECK_MSG(arr.isArray(), "an empty array must parse as an array, not null");
        CHECK(arr.items().empty());
        CHECK(arr.size() == 0);
        CHECK(write(arr) == "[]");

        // nested empties survive a round trip
        const Value nested = parse(R"({"a":{},"b":[],"c":[{}]})", &err);
        CHECK(err.empty());
        CHECK(nested.get("a").isObject());
        CHECK(nested.get("b").isArray());
        CHECK(nested.get("c").items().size() == 1);
        CHECK(nested.get("c").items()[0].isObject());
        const Value again = parse(write(nested), &err);
        CHECK(err.empty());
        CHECK(again.get("a").isObject());
        CHECK(again.get("b").isArray());

        // the factories are the correct way to start a container
        Value built = Value::object();
        built.set("x", Value(1));
        Value list = Value::array();
        list.push(Value(2));
        CHECK(built.isObject() && built.get("x").asInt() == 1);
        CHECK(list.isArray() && list.size() == 1);
        // set() on a container that was created as an array must not silently become an object
        CHECK(list.isArray());
    }

    // --- problem round trip ---
    {
        Order order;
        order.objective = Objective::MinimizeXThenY;
        order.origin = NestingOrigin::TopRight;
        order.interpartGap = 2.5;
        order.defectGap = 0.5;
        order.shear = true;
        order.shearCorner = true;
        order.shearGap = 1.25;
        order.markMode = true;
        order.leatherMode = true;
        order.localEngine = true;
        order.maxThreads = 4;
        order.maxIterations = 321;
        order.reorganizeBiggestPartNearOrigin = true;
        order.commonCutModeA = 2;
        order.commonCutModeTag = 1;
        order.commonCutObjectiveNum = 3.0;
        order.commonCutObjectiveDen = 4.0;
        order.multitorchAllowed = true;
        order.multitorchNbTorches = 4;
        order.multitorchMinDistance = 12.0;
        order.licenseKey1 = "KEY-1";
        order.licenseKey2 = "KEY-2";

        Sheet s;
        s.id = 7;
        s.width = 300.0;
        s.height = 150.0;
        s.quantity = 2;
        s.price = 12.5;
        s.priority = 3;
        s.grainDirection = 1;
        s.nonRectangular = true;
        s.shape = makeRectMulti(0, 0, 300, 150);
        order.sheets.push_back(s);

        Part p;
        p.id = 3;
        p.multiplicity = 5;
        p.priority = 1;
        p.userString = "frame";
        p.extraGap = 0.25;
        p.holeStatus = 1;
        geom::Polygon poly = rectPolygon(0, 0, 40, 20);
        poly.inners.push_back(geom::reverse(rectPolygon(10, 5, 20, 10).external));
        p.rawShape.push_back(poly);
        p.shape = p.rawShape;
        order.parts.push_back(p);

        const std::string text = saveProblem(order, true);
        CHECK(text.find("source_version") != std::string::npos);
        CHECK(text.find("68e2d90e72b4") != std::string::npos);  // the recovered build id

        Order back;
        std::string err;
        CHECK(loadProblem(text, back, &err));
        CHECK(err.empty());
        CHECK(back.objective == order.objective);
        CHECK(back.origin == order.origin);
        CHECK_NEAR(back.interpartGap, 2.5, 1e-12);
        CHECK_NEAR(back.defectGap, 0.5, 1e-12);
        CHECK(back.shear && back.shearCorner);
        CHECK_NEAR(back.shearGap, 1.25, 1e-12);
        CHECK(back.markMode && back.leatherMode && back.localEngine);
        CHECK(back.maxThreads == 4);
        CHECK(back.maxIterations == 321);
        CHECK(back.commonCutModeA == 2);
        CHECK(back.commonCutModeTag == 1);
        CHECK_NEAR(back.commonCutObjectiveNum, 3.0, 1e-12);
        CHECK(back.multitorchAllowed);
        CHECK(back.multitorchNbTorches == 4);
        CHECK(back.licenseKey1 == "KEY-1");
        CHECK(back.sheets.size() == 1);
        CHECK(back.sheets[0].id == 7);
        CHECK_NEAR(back.sheets[0].width, 300.0, 1e-9);
        CHECK(back.sheets[0].quantity == 2);
        CHECK(back.sheets[0].nonRectangular);
        CHECK(back.sheets[0].shape.size() == 1);
        CHECK(back.parts.size() == 1);
        CHECK(back.parts[0].id == 3);
        CHECK(back.parts[0].multiplicity == 5);
        CHECK(back.parts[0].userString == "frame");
        CHECK(back.parts[0].holeStatus == 1);
        CHECK(back.parts[0].rawShape.size() == 1);
        CHECK(back.parts[0].rawShape[0].inners.size() == 1);
        CHECK_NEAR(geom::area(back.parts[0].rawShape[0].external), 800.0, 1e-6);
    }

    // --- solution round trip ---
    {
        Order order;
        Sheet s;
        s.width = 200.0;
        s.height = 100.0;
        order.sheets.push_back(s);
        Part p;
        p.rawShape = makeRectMulti(0, 0, 20, 20);
        p.shape = p.rawShape;
        p.multiplicity = 2;
        order.parts.push_back(p);

        Solution sol;
        sol.valid = true;
        Nesting n;
        n.sheetIndex = 0;
        n.sheetArea = 20000.0;
        n.usedSurface = 800.0;
        NestedPart a;
        a.partIndex = 0;
        a.x = 5.0;
        a.y = 6.0;
        n.parts.push_back(a);
        NestedPart b;
        b.partIndex = 0;
        b.x = 30.0;
        b.y = 6.0;
        b.angle = 1.5707963267948966;
        b.flipped = true;
        n.parts.push_back(b);
        sol.nestings.push_back(n);

        const std::string text = saveSolution(sol, order, false);
        Solution back;
        std::string err;
        CHECK(loadSolution(text, order, back, &err));
        CHECK(err.empty());
        CHECK(back.valid);
        CHECK(back.nestings.size() == 1);
        CHECK(back.nestings[0].parts.size() == 2);
        CHECK_NEAR(back.nestings[0].parts[0].x, 5.0, 1e-12);
        CHECK_NEAR(back.nestings[0].parts[1].angle, 1.5707963267948966, 1e-12);
        CHECK(back.nestings[0].parts[1].flipped);
        CHECK_NEAR(back.fillRatio(), sol.fillRatio(), 1e-9);
    }

    // --- DXF ---
    {
        Order order;
        Sheet s;
        s.width = 100.0;
        s.height = 50.0;
        order.sheets.push_back(s);
        Part p;
        p.rawShape = makeRectMulti(0, 0, 10, 10);
        p.shape = p.rawShape;
        order.parts.push_back(p);

        Solution sol;
        Nesting n;
        n.sheetIndex = 0;
        NestedPart np;
        np.partIndex = 0;
        n.parts.push_back(np);
        sol.nestings.push_back(n);

        const std::string dxf = toDxf(order, sol);
        CHECK(dxf.rfind("0\nSECTION", 0) == 0);
        CHECK(dxf.find("AC1009") != std::string::npos);
        CHECK(dxf.find("SHEET") != std::string::npos);
        CHECK(dxf.find("PART") != std::string::npos);
        CHECK(dxf.find("POLYLINE") != std::string::npos);
        CHECK(dxf.find("VERTEX") != std::string::npos);
        CHECK(dxf.find("SEQEND") != std::string::npos);
        CHECK(dxf.find("EOF") != std::string::npos);
        // one sheet polyline + one part polyline
        std::size_t count = 0, pos = 0;
        while ((pos = dxf.find("\nPOLYLINE", pos)) != std::string::npos) {
            ++count;
            ++pos;
        }
        CHECK(count == 2);
    }

    // --- offcuts: sheet minus the placed parts, filtered by the offcut thresholds ---
    {
        Order order;
        Sheet s;
        s.width = 100.0;
        s.height = 100.0;
        order.sheets.push_back(s);
        Part p;
        p.rawShape = makeRectMulti(0, 0, 40, 40);
        p.shape = p.rawShape;
        order.parts.push_back(p);

        Solution sol;
        Nesting n;
        n.sheetIndex = 0;
        NestedPart np;
        np.partIndex = 0;
        np.x = 0.0;
        np.y = 0.0;
        n.parts.push_back(np);
        sol.nestings.push_back(n);

        const geom::MultiPolygon off = offcuts(order, sol);
        // 10000 - 1600 = 8400, as a single L shaped remnant
        CHECK(!off.empty());
        CHECK_NEAR(geom::multiArea(off), 8400.0, 1e-3);

        // raising the minimum dimension above the sheet size drops the remnant
        order.usedSurfaceMinOffcutDimension = 110.0;
        const geom::MultiPolygon off2 = offcuts(order, sol);
        CHECK(off2.empty());
    }

    return check::finish("test_io");
}
