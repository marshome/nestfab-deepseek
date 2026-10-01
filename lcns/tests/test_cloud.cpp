// tests/test_cloud.cpp -- request construction, UUID ids and the cloud engine flow.
#include "check.hpp"
#include "lcns/cloud.hpp"
#include "lcns/io.hpp"

#include <set>

using namespace lcns;
using namespace lcns::cloud;

namespace {

Order makeOrder() {
    Order order;
    Sheet s;
    s.width = 100.0;
    s.height = 100.0;
    order.sheets.push_back(s);
    Part p;
    p.rawShape = makeRectMulti(0, 0, 20, 20);
    p.shape = p.rawShape;
    p.multiplicity = 4;
    order.parts.push_back(p);
    return order;
}

std::string solutionJson(const Order& order, double usedSurface) {
    Solution sol;
    sol.valid = true;
    Nesting n;
    n.sheetIndex = 0;
    n.sheetArea = 10000.0;
    n.usedSurface = usedSurface;
    NestedPart a;
    a.partIndex = 0;
    a.x = 1.0;
    a.y = 1.0;
    n.parts.push_back(a);
    sol.nestings.push_back(n);
    return saveSolution(sol, order, false);
}

}  // namespace

int main() {
    // --- server list parsing (RE string "cns1.optalog.com;cns2.optalog.com") ---
    {
        const auto v = splitServerList("cns1.optalog.com;cns2.optalog.com");
        CHECK(v.size() == 2);
        CHECK(v[0] == "cns1.optalog.com");
        CHECK(v[1] == "cns2.optalog.com");
        CHECK(splitServerList("").empty());
        CHECK(splitServerList("a;b,c").size() == 3);
        CHECK(splitServerList(" a ; b ").size() == 2);
    }

    // --- request text: exactly the shape the recovered builders emit ---
    {
        const std::string get = buildGetRequest("cns1.optalog.com", "/sol/abc");
        CHECK(get == "GET /sol/abc HTTP/1.1\r\nHost: cns1.optalog.com\r\nAccept: */*\r\n"
                      "Connection: close\r\n\r\n");

        const std::string put = buildPutRequest("cns1.optalog.com", "/pb/abc", "{\"a\":1}");
        CHECK(put.rfind("PUT /pb/abc HTTP/1.1\r\n", 0) == 0);
        CHECK(put.find("Host: cns1.optalog.com\r\n") != std::string::npos);
        CHECK(put.find("Content-Length: 7\r\n") != std::string::npos);
        CHECK(put.find("Content-Type: text/plain\r\n") != std::string::npos);
        CHECK(put.find("\r\n\r\n{\"a\":1}") != std::string::npos);
    }

    // --- request ids look like UUIDv4 and do not repeat ---
    {
        std::set<std::string> seen;
        for (int i = 0; i < 64; ++i) {
            const std::string id = makeRequestId(static_cast<std::uint32_t>(5489 + i));
            CHECK(id.size() == 36);
            CHECK(id[8] == '-' && id[13] == '-' && id[18] == '-' && id[23] == '-');
            CHECK(id[14] == '4');                                  // version 4
            const char variant = id[19];
            CHECK(variant == '8' || variant == '9' || variant == 'a' || variant == 'b');
            seen.insert(id);
        }
        CHECK(seen.size() == 64);
    }

    // --- cloud flow: an intermediate solution, then "end" and the best solution ---
    {
        const Order order = makeOrder();
        FakeHttpClient fake;
        Config cfg;
        cfg.servers = {"cns-test.local"};
        cfg.pollIntervalMs = 0;   // no sleeping in tests
        cfg.maxPolls = 8;

        fake.pushSolution(solutionJson(order, 1600.0));   // intermediate
        fake.pushSolution("end");                         // the computation finished
        fake.pushSolution(solutionJson(order, 1600.0));   // /best_sol/ payload

        CloudEngine engine(fake, cfg);
        const CloudResult res = engine.run(order, 3.0);
        CHECK(res.ok);
        CHECK(res.putStatus == 200);
        CHECK(res.label == "final");
        CHECK(!res.computationId.empty());
        CHECK(res.solution.totalNestedParts() == 1);
        CHECK(fake.puts.size() == 1);
        CHECK(fake.puts[0].first == "/pb/" + res.computationId);
        CHECK(fake.puts[0].second.find("source_version") != std::string::npos);
        // two GET /sol/ polls then one GET /best_sol/
        CHECK(fake.gets.size() == 3);
        CHECK(fake.gets[0] == "/sol/" + res.computationId);
        CHECK(fake.gets[1] == "/sol/" + res.computationId);
        CHECK(fake.gets[2] == "/best_sol/" + res.computationId);
        CHECK(!res.log.empty());
    }

    // --- only intermediate solutions: the best one is kept, label stays intermediate ---
    {
        const Order order = makeOrder();
        FakeHttpClient fake;
        Config cfg;
        cfg.servers = {"cns-test.local"};
        cfg.pollIntervalMs = 0;
        cfg.maxPolls = 3;

        fake.pushSolution(solutionJson(order, 400.0));
        fake.pushSolution(solutionJson(order, 800.0));
        fake.pushSolution(solutionJson(order, 600.0));

        CloudEngine engine(fake, cfg);
        const CloudResult res = engine.run(order, 3.0);
        CHECK(res.ok);
        CHECK(res.label == "intermediate");
        CHECK_NEAR(res.solution.usedSurface(), 800.0, 1e-6);   // the best fill ratio wins
    }

    // --- PUT failure falls back to the local engine (RE: the two entry points call each other) ---
    {
        const Order order = makeOrder();
        FakeHttpClient fake;
        fake.setPutFailure(true);
        Config cfg;
        cfg.servers = {"cns-test.local"};
        cfg.pollIntervalMs = 0;

        EngineParams params;
        params.timeLimitSeconds = 0.5;
        params.maxIterations = 8;
        params.beam.maxAngleSteps = 2;

        CloudEngine engine(fake, cfg);
        const CloudResult res = engine.runWithFallback(order, 0.5, params);
        CHECK(res.ok);
        CHECK(res.usedLocalFallback);
        CHECK(res.label == "final");
        CHECK(res.solution.totalNestedParts() >= 1);
        bool sawFallback = false;
        for (const auto& l : res.log) {
            if (l.find("falling back") != std::string::npos) sawFallback = true;
        }
        CHECK(sawFallback);
    }

    // --- a bad payload must not be accepted ---
    {
        const Order order = makeOrder();
        FakeHttpClient fake;
        Config cfg;
        cfg.servers = {"cns-test.local"};
        cfg.pollIntervalMs = 0;
        cfg.maxPolls = 2;
        fake.pushSolution("{ this is not json");
        fake.pushSolution("end");

        CloudEngine engine(fake, cfg);
        const CloudResult res = engine.run(order, 1.0);
        CHECK(!res.ok);
        CHECK(res.label == "final");   // it did reach the end marker
    }

    // --- serialisation helpers ---
    {
        const Order order = makeOrder();
        const std::string pb = serializeProblem(order);
        CHECK(pb.find("parts") != std::string::npos);
        Solution out;
        std::string err;
        CHECK(deserializeSolution(solutionJson(order, 1234.0), order, out, &err));
        CHECK(err.empty());
        CHECK_NEAR(out.usedSurface(), 1234.0, 1e-6);
    }

    return check::finish("test_cloud");
}
