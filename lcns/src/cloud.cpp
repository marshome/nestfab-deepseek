// lcns/cloud.cpp
#include "lcns/cloud.hpp"
#include "lcns/recovery.hpp"

#include "lcns/io.hpp"

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <random>
#include <sstream>
#include <thread>

#if defined(_WIN32)
#  ifndef WIN32_LEAN_AND_MEAN
#    define WIN32_LEAN_AND_MEAN
#  endif
#  include <winsock2.h>
#  include <ws2tcpip.h>
#  include <windows.h>
using socket_t = SOCKET;
#  define LCNS_INVALID_SOCKET INVALID_SOCKET
#else
#  include <arpa/inet.h>
#  include <netdb.h>
#  include <netinet/in.h>
#  include <sys/socket.h>
#  include <sys/time.h>
#  include <unistd.h>
using socket_t = int;
#  define LCNS_INVALID_SOCKET (-1)
#  define closesocket close
#endif

LCNS_STRUCTURAL(module.cloud);
namespace lcns {
namespace cloud {
namespace {

constexpr const char* kCrLf = "\r\n";

void parseResponse(const std::string& raw, HttpResponse& out) {
    const std::size_t headEnd = raw.find("\r\n\r\n");
    const std::string head = headEnd == std::string::npos ? raw : raw.substr(0, headEnd);
    std::string body = headEnd == std::string::npos ? std::string() : raw.substr(headEnd + 4);

    // state line: HTTP/1.1 200 OK
    if (head.rfind("HTTP/", 0) == 0) {
        const std::size_t sp = head.find(' ');
        if (sp != std::string::npos) {
            out.status = std::atoi(head.c_str() + sp + 1);
        }
    }

    // Transfer-Encoding: chunked
    const bool chunked = head.find("chunked") != std::string::npos ||
                         head.find("Chunked") != std::string::npos;
    if (chunked) {
        std::string decoded;
        std::size_t i = 0;
        while (i < body.size()) {
            const std::size_t eol = body.find("\r\n", i);
            if (eol == std::string::npos) break;
            const std::string lenStr = body.substr(i, eol - i);
            const std::size_t size = static_cast<std::size_t>(std::strtoul(lenStr.c_str(), nullptr, 16));
            if (size == 0) break;
            const std::size_t start = eol + 2;
            if (start + size > body.size()) break;
            decoded.append(body, start, size);
            i = start + size + 2;
        }
        body = decoded;
    }
    out.body = body;
    out.networkOk = true;
}

}  // namespace

// ---------------------------------------------------------------------------
std::vector<std::string> splitServerList(const std::string& semicolonSeparated) {
    std::vector<std::string> out;
    std::string cur;
    for (char c : semicolonSeparated) {
        if (c == ';' || c == ',') {
            if (!cur.empty()) out.push_back(cur);
            cur.clear();
        } else if (c != ' ' && c != '\t') {
            cur.push_back(c);
        }
    }
    if (!cur.empty()) out.push_back(cur);
    return out;
}

std::string buildGetRequest(const std::string& host, const std::string& path) {
    // RE 0x6DA1F0
    std::ostringstream os;
    os << "GET " << path << " HTTP/1.1" << kCrLf
       << "Host: " << host << kCrLf
       << "Accept: */*" << kCrLf
       << "Connection: close" << kCrLf << kCrLf;
    return os.str();
}

LCNS_NOT_REVERSED(cloud.payload_schema);
std::string buildPutRequest(const std::string& host, const std::string& path,
                            const std::string& body) {
    // RE 0x6DBD40
    std::ostringstream os;
    os << "PUT " << path << " HTTP/1.1" << kCrLf
       << "Host: " << host << kCrLf
       << "Accept: */*" << kCrLf
       << "Connection: close" << kCrLf
       << "Content-Length: " << body.size() << kCrLf
       << "Content-Type: text/plain" << kCrLf << kCrLf
       << body;
    return os.str();
}

std::string makeRequestId(std::uint32_t seed) {
    // RE: std::mt19937 seeded 5489 mixed with CryptGenRandom, formatted as a UUIDv4 with the
    // version and variant bits forced.
    std::mt19937 gen(seed);
    std::random_device rd;
    auto byte = [&]() -> unsigned {
        const unsigned a = gen() & 0xFFu;
        const unsigned b = rd() & 0xFFu;   // stands in for CryptGenRandom
        return (a ^ b) & 0xFFu;
    };
    unsigned char b[16];
    for (auto& v : b) v = static_cast<unsigned char>(byte());
    b[6] = static_cast<unsigned char>((b[6] & 0x0F) | 0x40);  // version 4
    b[8] = static_cast<unsigned char>((b[8] & 0x3F) | 0x80);  // variant 10
    char out[40];
    std::snprintf(out, sizeof(out),
                  "%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x", b[0],
                  b[1], b[2], b[3], b[4], b[5], b[6], b[7], b[8], b[9], b[10], b[11], b[12], b[13],
                  b[14], b[15]);
    return std::string(out);
}

// ---------------------------------------------------------------------------
SocketHttpClient::SocketHttpClient() {
#if defined(_WIN32)
    WSADATA wsa{};
    WSAStartup(MAKEWORD(2, 2), &wsa);
#endif
}

SocketHttpClient::~SocketHttpClient() {
#if defined(_WIN32)
    WSACleanup();
#endif
}

namespace {

HttpResponse exchange(const std::string& host, int port, const std::string& request,
                      double timeoutSeconds) {
    HttpResponse out;
    addrinfo hints{};
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    addrinfo* res = nullptr;
    char portStr[16];
    std::snprintf(portStr, sizeof(portStr), "%d", port);
    if (getaddrinfo(host.c_str(), portStr, &hints, &res) != 0 || !res) {
        out.error = "cannot resolve " + host;   // RE Utils::ResolveException
        return out;
    }
    socket_t s = LCNS_INVALID_SOCKET;
    for (addrinfo* ai = res; ai; ai = ai->ai_next) {
        s = ::socket(ai->ai_family, ai->ai_socktype, ai->ai_protocol);
        if (s == LCNS_INVALID_SOCKET) continue;
#if defined(_WIN32)
        DWORD tv = static_cast<DWORD>(std::max(1.0, timeoutSeconds) * 1000.0);
        setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, reinterpret_cast<const char*>(&tv), sizeof(tv));
        setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, reinterpret_cast<const char*>(&tv), sizeof(tv));
#else
        timeval tv{};
        tv.tv_sec = static_cast<long>(timeoutSeconds);
        tv.tv_usec = static_cast<long>((timeoutSeconds - static_cast<double>(tv.tv_sec)) * 1e6);
        setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
        setsockopt(s, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
#endif
        if (::connect(s, ai->ai_addr, static_cast<int>(ai->ai_addrlen)) == 0) break;
        closesocket(s);
        s = LCNS_INVALID_SOCKET;
    }
    freeaddrinfo(res);
    if (s == LCNS_INVALID_SOCKET) {
        out.error = "cannot connect to " + host;   // RE Utils::ConnectException
        return out;
    }

    std::size_t sent = 0;
    while (sent < request.size()) {
        const int n = ::send(s, request.data() + sent, static_cast<int>(request.size() - sent), 0);
        if (n <= 0) {
            out.error = "send failed";
            closesocket(s);
            return out;
        }
        sent += static_cast<std::size_t>(n);
    }

    std::string raw;
    char buf[4096];
    for (;;) {
        const int n = ::recv(s, buf, sizeof(buf), 0);
        if (n <= 0) break;
        raw.append(buf, static_cast<std::size_t>(n));
        if (n < static_cast<int>(sizeof(buf))) break;
    }
    closesocket(s);
    if (raw.empty()) {
        out.error = "timeout or empty response";  // RE Utils::TimeoutException
        return out;
    }
    parseResponse(raw, out);
    if (out.status == 0) out.error = "bad response";   // RE Utils::BadResponseException
    return out;
}

}  // namespace

HttpResponse SocketHttpClient::get(const std::string& host, int port, const std::string& path,
                                   double timeoutSeconds) {
    return exchange(host, port, buildGetRequest(host, path), timeoutSeconds);
}

HttpResponse SocketHttpClient::put(const std::string& host, int port, const std::string& path,
                                   const std::string& body, double timeoutSeconds) {
    return exchange(host, port, buildPutRequest(host, path, body), timeoutSeconds);
}

// ---------------------------------------------------------------------------
void FakeHttpClient::setResponse(const std::string& path, int status, const std::string& body) {
    responses_[path] = {status, body};
}

void FakeHttpClient::pushSolution(const std::string& body) { solutions_.push_back(body); }

HttpResponse FakeHttpClient::get(const std::string& host, int port, const std::string& path,
                                 double timeoutSeconds) {
    (void)host;
    (void)port;
    (void)timeoutSeconds;
    gets.push_back(path);
    HttpResponse r;
    auto it = responses_.find(path);
    if (it != responses_.end()) {
        r.status = it->second.first;
        r.body = it->second.second;
        r.networkOk = true;
        return r;
    }
    if (!solutions_.empty()) {
        const std::size_t i = std::min(solutionIndex_, solutions_.size() - 1);
        // once the queue is exhausted the last entry keeps repeating, and the final one
        // carries the "end" marker the recovered code looks for
        if (solutionIndex_ + 1 < solutions_.size()) ++solutionIndex_;
        r.status = 200;
        r.body = solutions_[i];
        r.networkOk = true;
        return r;
    }
    r.status = 404;
    r.networkOk = true;
    return r;
}

HttpResponse FakeHttpClient::put(const std::string& host, int port, const std::string& path,
                                 const std::string& body, double timeoutSeconds) {
    (void)host;
    (void)port;
    (void)timeoutSeconds;
    puts.emplace_back(path, body);
    HttpResponse r;
    if (failPuts_) {
        r.networkOk = false;
        r.error = "connect refused (test)";
        return r;
    }
    r.status = 200;
    r.networkOk = true;
    r.body = "ok";
    return r;
}

// ---------------------------------------------------------------------------
CloudEngine::CloudEngine(HttpClient& client, Config config) : client_(client), cfg_(std::move(config)) {}

HttpResponse CloudEngine::tryServers(const std::string& method, const std::string& path,
                                     const std::string& body, double timeoutSeconds,
                                     std::string* hostUsed) {
    HttpResponse last;
    for (const auto& host : cfg_.servers) {
        const HttpResponse r = (method == "PUT")
                                   ? client_.put(host, cfg_.port, path, body, timeoutSeconds)
                                   : client_.get(host, cfg_.port, path, timeoutSeconds);
        if (r.ok()) {
            if (hostUsed) *hostUsed = host;
            return r;
        }
        last = r;
    }
    return last;
}

CloudResult CloudEngine::run(const Order& order, double timeLimitSeconds) {
    CloudResult res;
    const std::string id = makeRequestId();
    res.computationId = id;
    const std::string problem = serializeProblem(order);

    const double submitTime =
        std::max(cfg_.submitTimeFloor, timeLimitSeconds - cfg_.submitTimeReduction);
    res.log.push_back("PUT /pb/" + id + " (timeout " + std::to_string(cfg_.putTimeoutSeconds) +
                      " s, engine budget " + std::to_string(submitTime) + " s)");
    std::string host;
    const HttpResponse put =
        tryServers("PUT", "/pb/" + id, problem, cfg_.putTimeoutSeconds, &host);
    res.putStatus = put.status;
    if (!put.ok()) {
        res.log.push_back("PUT failed: " + put.error);
        return res;
    }

    // deadline = 2*t + 30 (RE 0x9AE9B8)
    const auto start = std::chrono::steady_clock::now();
    const double deadline = 2.0 * timeLimitSeconds + cfg_.overallSlackSeconds;
    double bestFill = -1.0;

    for (int poll = 0; poll < cfg_.maxPolls; ++poll) {
        if (std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count() >
            deadline) {
            res.log.push_back("deadline reached");
            break;
        }
        // Ask for the running solution; the body "end" means the computation finished and the
        // best solution lives under /best_sol/ (RE 0x2893F compares the body with "end").
        const HttpResponse probe =
            tryServers("GET", "/sol/" + id, std::string(), cfg_.pollWindowSeconds, &host);
        res.getStatus = probe.status;
        if (!probe.ok()) {
            res.log.push_back("GET /sol/ failed: " + probe.error);
            break;
        }

        if (probe.body == "end") {
            const HttpResponse got = tryServers("GET", "/best_sol/" + id, std::string(),
                                                cfg_.pollWindowSeconds, &host);
            res.getStatus = got.status;
            res.label = "final";
            res.log.push_back("GET /best_sol/" + id + " -> " + std::to_string(got.status) + " (" +
                              std::to_string(got.body.size()) + " bytes, final)");
            if (got.ok() && !got.body.empty() && got.body != "end") {
                Solution parsed;
                std::string err;
                if (deserializeSolution(got.body, order, parsed, &err)) {
                    res.solution = parsed;
                    res.ok = true;
                } else {
                    res.log.push_back("solution parse error: " + err);
                }
            }
            break;
        }

        res.label = "intermediate";
        res.log.push_back("GET /sol/" + id + " -> " + std::to_string(probe.status) + " (" +
                          std::to_string(probe.body.size()) + " bytes, intermediate)");
        if (!probe.body.empty()) {
            Solution parsed;
            std::string err;
            if (deserializeSolution(probe.body, order, parsed, &err)) {
                const double fill = parsed.fillRatio();
                if (fill > bestFill) {
                    bestFill = fill;
                    res.solution = parsed;
                    res.ok = true;
                }
            } else {
                res.log.push_back("solution parse error: " + err);
            }
        }
        if (cfg_.pollIntervalMs > 0) {
            std::this_thread::sleep_for(std::chrono::milliseconds(cfg_.pollIntervalMs));
        }
    }
    if (res.label.empty()) res.label = "intermediate";
    return res;
}

CloudResult CloudEngine::runWithFallback(const Order& order, double timeLimitSeconds,
                                        const EngineParams& localParams) {
    CloudResult res = run(order, timeLimitSeconds);
    if (res.ok) return res;

    // RE: LaunchComputation and LaunchLocalComputation call each other, so the cloud path can
    // fall back to the local engine.
    res.log.push_back("cloud unavailable, falling back to the local engine");
    Engine engine;
    EngineParams p = localParams;
    p.timeLimitSeconds = timeLimitSeconds;
    const EngineResult local = engine.run(order, p);
    res.solution = local.solution;
    res.ok = true;
    res.usedLocalFallback = true;
    res.label = "final";
    return res;
}

// ---------------------------------------------------------------------------
std::string serializeProblem(const Order& order) { return saveProblem(order, false); }

bool deserializeSolution(const std::string& payload, const Order& order, Solution& out,
                         std::string* error) {
    return loadSolution(payload, order, out, error);
}

}  // namespace cloud
}  // namespace lcns
