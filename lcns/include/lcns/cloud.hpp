// lcns/cloud.hpp -- HTTP transport and the cloud engine.
//
// Recovered from the binary (re/findings_cloud_lic.md):
//   * `Engine::CloudEngine::Run` = RVA 0x26A60 is the only business virtual of that class.
//   * `LaunchLocalComputation` (0x2AB0) forwards to `LaunchComputation` (0x6100) with the
//     server list "cns1.optalog.com;cns2.optalog.com" and the option name "cns_force_cloud".
//   * HTTP/1.1 is hand written through boost::asio: request builders at 0x6DA1F0 (GET) and
//     0x6DBD40 (PUT), response parsers at 0x6DAB80 / 0x6DC480, port constant 0x50 = 80,
//     request id is a random UUIDv4 built from std::mt19937 (seed 5489) + CryptGenRandom.
//   * Paths: PUT `/pb/<id>` submits the problem; GET `/sol/<id>` or `/best_sol/<id>` fetches a
//     solution. The choice is made by comparing the response body with "end": body == "end"
//     means `/sol/` with the label "intermediate", otherwise `/best_sol/` with "final".
//   * Timeouts: PUT 120.0 s (0x9AE9B0), overall deadline 2*t + 30.0 (0x9AE9B8), GET poll
//     window 20 s (0x4A817C800 ns), and the engine is given max(t - 5.0, 1.0).
//   * The payload is JSON (JsonCpp in the original, `c:\Temp\cns.pb.json` for debugging).
#pragma once

#include <cstdint>
#include <map>
#include <string>
#include <vector>

#include "lcns/engine.hpp"

namespace lcns {
namespace cloud {

struct Config {
    // RE string "cns1.optalog.com;cns2.optalog.com" is a single semicolon separated value
    std::vector<std::string> servers = {"cns1.optalog.com", "cns2.optalog.com"};
    int port = 80;                                  // RE port constant 0x50
    std::string optionName = "cns_force_cloud";     // RE option key
    double putTimeoutSeconds = 120.0;               // RE double @0x9AE9B0
    double pollWindowSeconds = 20.0;                // RE movabs 0x4A817C800 ns
    double overallSlackSeconds = 30.0;              // RE deadline = 2*t + 30
    double submitTimeReduction = 5.0;               // RE max(t - 5.0, 1.0)
    double submitTimeFloor = 1.0;
    int maxPolls = 4096;
    int pollIntervalMs = 50;   // sleep between polls (the original uses nanosleep backoff)
    bool verbose = false;
};

std::vector<std::string> splitServerList(const std::string& semicolonSeparated);

// Request text builders -- byte for byte the shape the recovered code emits.
std::string buildGetRequest(const std::string& host, const std::string& path);
std::string buildPutRequest(const std::string& host, const std::string& path,
                            const std::string& body);

// RE: a random UUIDv4 is used as the computation id for /pb/, /sol/ and /best_sol/.
std::string makeRequestId(std::uint32_t seed = 5489u);

// ---------------------------------------------------------------------------
struct HttpResponse {
    int status = 0;
    std::string body;
    std::string error;
    bool networkOk = false;
    bool ok() const { return networkOk && status >= 200 && status < 300; }
};

class HttpClient {
public:
    virtual ~HttpClient() = default;
    virtual HttpResponse get(const std::string& host, int port, const std::string& path,
                             double timeoutSeconds) = 0;
    virtual HttpResponse put(const std::string& host, int port, const std::string& path,
                             const std::string& body, double timeoutSeconds) = 0;
};

// Real transport. Winsock on Windows, BSD sockets elsewhere.
class SocketHttpClient : public HttpClient {
public:
    SocketHttpClient();
    ~SocketHttpClient() override;
    HttpResponse get(const std::string& host, int port, const std::string& path,
                     double timeoutSeconds) override;
    HttpResponse put(const std::string& host, int port, const std::string& path,
                     const std::string& body, double timeoutSeconds) override;
};

// In-memory transport used by the tests (and by `--dry-run`).
class FakeHttpClient : public HttpClient {
public:
    // key is the path, e.g. "/pb/abc"
    void setResponse(const std::string& path, int status, const std::string& body);
    // bodies returned by GET in order, then the last one repeats
    void pushSolution(const std::string& body);
    HttpResponse get(const std::string& host, int port, const std::string& path,
                     double timeoutSeconds) override;
    HttpResponse put(const std::string& host, int port, const std::string& path,
                     const std::string& body, double timeoutSeconds) override;

    std::vector<std::pair<std::string, std::string>> puts;   // path, body
    std::vector<std::string> gets;
    void setPutFailure(bool fail) { failPuts_ = fail; }

private:
    std::map<std::string, std::pair<int, std::string>> responses_;
    std::vector<std::string> solutions_;
    std::size_t solutionIndex_ = 0;
    bool failPuts_ = false;
};

// ---------------------------------------------------------------------------
struct CloudResult {
    bool ok = false;
    Solution solution;
    int putStatus = 0;
    int getStatus = 0;
    std::string label;            // "final" or "intermediate"
    std::string computationId;
    std::vector<std::string> log;
    bool usedLocalFallback = false;
};

class CloudEngine {
public:
    CloudEngine(HttpClient& client, Config config);
    const Config& config() const { return cfg_; }

    // Submits the problem to the first reachable server and polls for solutions until the
    // deadline, keeping the best one. Mirrors Engine::CloudEngine::Run.
    CloudResult run(const Order& order, double timeLimitSeconds);

    // Cloud first, local engine when the cloud is unreachable (RE: LaunchComputation and
    // LaunchLocalComputation call each other).
    CloudResult runWithFallback(const Order& order, double timeLimitSeconds,
                               const EngineParams& localParams = {});

private:
    HttpResponse tryServers(const std::string& method, const std::string& path,
                            const std::string& body, double timeoutSeconds, std::string* hostUsed);

    HttpClient& client_;
    Config cfg_;
};

// RE UnSerializeSolution (0x1C5F0) / CreateProblem (0x1EE50)
std::string serializeProblem(const Order& order);
bool deserializeSolution(const std::string& payload, const Order& order, Solution& out,
                         std::string* error = nullptr);

}  // namespace cloud
}  // namespace lcns
