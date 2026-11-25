// strata/platform/aux_cpus.hpp - where the engine's OTHER threads run.
//
// The pool pins its workers (one logical CPU per physical core) and the host thread pins itself to the pool's reserved
// core.  Every thread the host creates afterwards inherits the host's single CPU (the adaptive tier's job thread, the
// prefill helpers, the router lookahead ...), and the threads the CUDA driver creates float over every CPU, the pool
// workers' included.  Measured on a 16-worker box: while the adaptive tier was busy the host thread was preempted 5x
// as often and the per-layer wait for the host's flag was 60-155 us instead of 8.
//
// `--aux-cpus LIST|auto|off` (STRATA_AUX_CPUS) puts every thread that is neither a pool worker nor the host thread on
// a small set of CPUs no worker uses:
//   * threads the engine creates call `pin_current_thread()` first thing (a no-op while the feature is off);
//   * threads somebody else created (the CUDA driver's) are caught by `sweep()` over /proc/self/task, run after the
//     start-up and at every request.
// `auto` takes the SMT siblings of the host's core, then every CPU of a physical core no worker is pinned to.  It
// never takes a CPU that shares a core with a worker (that would steal the worker's cycles): with nothing spare the
// feature does nothing.  A list (`--aux-cpus 24,26`) is taken as given, minus the host's CPU and the workers' CPUs.
//
// Linux only (the other systems get empty functions).  Header-only on purpose: the callers sit in four libraries that
// do not link each other.  No output of the engine depends on where a thread runs.
#pragma once

#include "strata/platform/thread_name.hpp"
#include <algorithm>
#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <mutex>
#include <set>
#include <string>
#include <vector>

#if defined(__linux__)
#include <dirent.h>
#include <sched.h>
#include <sys/syscall.h>
#include <unistd.h>
#elif defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <tlhelp32.h>
#include <cstddef>
#endif

namespace strata::aux_cpus {

/// One logical CPU the process may use and the physical core it belongs to (-1: unknown).
struct LogicalCpu {
    int cpu = -1;
    long pkg = -1;
    long core = -1;
};

/// "24,26,30-31" -> {24, 26, 30, 31} (sorted, no duplicates).  False for anything else (empty items, letters,
/// reversed ranges, negative numbers); `out` is then empty.
inline bool parse_cpu_list(const std::string& text, std::vector<int>& out) {
    out.clear();
    if (text.empty()) return false;
    size_t i = 0;
    auto number = [&](long& v) {
        if (i >= text.size() || text[i] < '0' || text[i] > '9') return false;
        v = 0;
        while (i < text.size() && text[i] >= '0' && text[i] <= '9') {
            v = v * 10 + (text[i] - '0');
            if (v > 100000) return false;
            ++i;
        }
        return true;
    };
    for (;;) {
        long lo = 0, hi = 0;
        if (!number(lo)) { out.clear(); return false; }
        hi = lo;
        if (i < text.size() && text[i] == '-') {
            ++i;
            if (!number(hi) || hi < lo) { out.clear(); return false; }
        }
        for (long c = lo; c <= hi; ++c) out.push_back((int) c);
        if (i == text.size()) break;
        if (text[i] != ',') { out.clear(); return false; }
        ++i;
    }
    std::sort(out.begin(), out.end());
    out.erase(std::unique(out.begin(), out.end()), out.end());
    return true;
}

/// The CPUs `auto` gives to the aux threads, in order: the SMT siblings of the host's physical core first, then every
/// CPU of a physical core that has no worker and is not the host's.  A CPU that shares a core with a worker is never
/// returned, and neither is one whose core is unknown (no sysfs): it might be a worker's sibling.
inline std::vector<int> derive(const std::vector<LogicalCpu>& allowed, int host_cpu, const std::vector<int>& worker_cpus) {
    using Key = std::pair<long, long>;
    auto key_of = [&](int cpu, Key& k) {
        for (const LogicalCpu& c : allowed)
            if (c.cpu == cpu) { k = {c.pkg, c.core}; return c.pkg >= 0 && c.core >= 0; }
        return false;
    };
    std::vector<Key> worker_keys;
    for (int w : worker_cpus) {
        Key k;
        if (key_of(w, k)) worker_keys.push_back(k);
    }
    Key host_key;
    const bool host_known = host_cpu >= 0 && key_of(host_cpu, host_key);
    std::vector<int> siblings, free_cores;
    for (const LogicalCpu& c : allowed) {
        if (c.cpu == host_cpu || c.pkg < 0 || c.core < 0) continue;
        if (std::find(worker_cpus.begin(), worker_cpus.end(), c.cpu) != worker_cpus.end()) continue;
        const Key k{c.pkg, c.core};
        if (host_known && k == host_key) {
            siblings.push_back(c.cpu);
        } else if (std::find(worker_keys.begin(), worker_keys.end(), k) == worker_keys.end()) {
            free_cores.push_back(c.cpu);
        }
    }
    std::sort(siblings.begin(), siblings.end());
    std::sort(free_cores.begin(), free_cores.end());
    siblings.insert(siblings.end(), free_cores.begin(), free_cores.end());
    return siblings;
}

/// The CPUs for I/O-bound background threads (DirectFile NVMe/SSD readers, ColdStore streamers,
/// async PrefetchVirtualMemory workers): starts with `derive()` (host SMT sibling + worker-free cores),
/// then appends the SMT siblings of worker physical cores so a 6C/12T CPU keeps all 6 primary threads
/// dedicated to AVX2/GPU compute while utilizing the 6 SMT secondary threads for asynchronous I/O and DMA.
/// Never includes `host_cpu` or any CPU in `worker_cpus`.
inline std::vector<int> derive_io_smt(const std::vector<LogicalCpu>& allowed, int host_cpu,
                                      const std::vector<int>& worker_cpus) {
    std::vector<int> out = derive(allowed, host_cpu, worker_cpus);
    std::vector<int> worker_siblings;
    for (const LogicalCpu& c : allowed) {
        if (c.cpu == host_cpu || c.pkg < 0 || c.core < 0) continue;
        if (std::find(worker_cpus.begin(), worker_cpus.end(), c.cpu) != worker_cpus.end()) continue;
        if (std::find(out.begin(), out.end(), c.cpu) != out.end()) continue;
        worker_siblings.push_back(c.cpu);
    }
    std::sort(worker_siblings.begin(), worker_siblings.end());
    out.insert(out.end(), worker_siblings.begin(), worker_siblings.end());
    return out;
}

/// An explicit list, restricted to CPUs the process may use, without the host's CPU and the workers' CPUs.
inline std::vector<int> restrict_list(const std::vector<int>& list, const std::vector<LogicalCpu>& allowed, int host_cpu,
                                      const std::vector<int>& worker_cpus) {
    std::vector<int> out;
    for (int c : list) {
        if (c == host_cpu || std::find(worker_cpus.begin(), worker_cpus.end(), c) != worker_cpus.end()) continue;
        const bool ok = std::any_of(allowed.begin(), allowed.end(), [&](const LogicalCpu& a) { return a.cpu == c; });
        if (ok) out.push_back(c);
    }
    return out;
}

/// What `--aux-cpus` / STRATA_AUX_CPUS said.  `on`: placed from the start-up; `use_list`: the list, not `auto`.
struct Config {
    bool on = false;
    bool use_list = false;
    std::vector<int> list;
};

/// "" and "off": off at start (a request can still turn it on with `auto`); "auto"; or a CPU list.
inline bool parse_spec(const std::string& spec, Config& cfg, std::string& err) {
    cfg = Config{};
    if (spec.empty() || spec == "off") return true;
    if (spec == "auto") { cfg.on = true; return true; }
    if (!parse_cpu_list(spec, cfg.list)) {
        err = "--aux-cpus takes off, auto or a CPU list such as 24,26 or 24-27 (got '" + spec + "')";
        return false;
    }
    cfg.on = true;
    cfg.use_list = true;
    return true;
}

#if defined(__linux__)

namespace detail {

struct State {
    std::mutex mu;
    Config cfg;
    std::atomic<bool> enabled{false};
    std::atomic<bool> have_plan{false};
    std::vector<int> allowed;                     ///< the process's CPUs, snapshotted before any thread is pinned
    std::vector<int> plan;                        ///< the aux CPUs (empty: nothing to do)
    std::vector<int> io_plan;                     ///< aux + worker SMT sibling CPUs for I/O-bound threads
    std::vector<int> workers;                     ///< the pool's CPUs: their threads are never touched
    int host_cpu = -1;                            ///< the CPU the host thread is pinned to (-1: unknown)
    cpu_set_t target;
    cpu_set_t io_target;
    std::set<int> owned;                          ///< tids of pool workers and host threads
    std::map<int, cpu_set_t> original;            ///< tid -> the mask it had before this module moved it
    State() { CPU_ZERO(&target); CPU_ZERO(&io_target); }
};

inline State& state() {
    static State s;
    return s;
}

inline int self_tid() { return (int) syscall(SYS_gettid); }

inline bool same_mask(const cpu_set_t& a, const cpu_set_t& b) { return CPU_EQUAL(&a, &b) != 0; }

/// Moves `tid` to the aux set.  Caller holds `mu`.  Returns true if the thread's mask changed.
inline bool move_locked(State& s, int tid) {
    cpu_set_t now;
    CPU_ZERO(&now);
    if (sched_getaffinity(tid, sizeof now, &now) != 0) return false;
    if (same_mask(now, s.target)) return false;
    if (CPU_COUNT(&now) == 1) {                    // pinned to one CPU of a worker by somebody: not ours
        for (int w : s.workers)
            if (CPU_ISSET(w, &now)) return false;
    }
    if (sched_setaffinity(tid, sizeof s.target, &s.target) != 0) return false;
    s.original.emplace(tid, now);                 // the first mask only: a second move keeps the real original
    return true;
}

inline bool alive(int tid) {
    char path[48];
    std::snprintf(path, sizeof path, "/proc/self/task/%d", tid);
    return access(path, F_OK) == 0;
}

inline std::vector<int> task_ids() {
    std::vector<int> ids;
    if (DIR* d = opendir("/proc/self/task")) {
        while (const dirent* e = readdir(d))
            if (e->d_name[0] >= '0' && e->d_name[0] <= '9') ids.push_back(std::atoi(e->d_name));
        closedir(d);
    }
    return ids;
}

/// Forgets the threads that have ended (their tids may come back for another thread).  Caller holds `mu`.
inline void purge_locked(State& s) {
    for (auto it = s.original.begin(); it != s.original.end();) it = alive(it->first) ? std::next(it) : s.original.erase(it);
    for (auto it = s.owned.begin(); it != s.owned.end();) it = alive(*it) ? std::next(it) : s.owned.erase(it);
}

}  // namespace detail

/// Reads the CPUs the calling thread may use and the spec.  Call once, early, on the thread that has not been pinned
/// yet (the engine's main thread, before the pool exists).  The main thread counts as the host.
inline bool configure(const std::string& spec, std::string& err) {
    detail::State& s = detail::state();
    Config cfg;
    if (!parse_spec(spec, cfg, err)) return false;
    std::lock_guard<std::mutex> lk(s.mu);
    s.cfg = cfg;
    s.allowed.clear();
    cpu_set_t now;
    CPU_ZERO(&now);
    if (sched_getaffinity(0, sizeof now, &now) == 0)
        for (int c = 0; c < CPU_SETSIZE; ++c)
            if (CPU_ISSET(c, &now)) s.allowed.push_back(c);
    s.owned.insert(detail::self_tid());
    return true;
}

/// The calling thread belongs to the pool or is the host: the sweep leaves it alone.
inline void note_owned_thread() {
    detail::State& s = detail::state();
    std::lock_guard<std::mutex> lk(s.mu);
    s.owned.insert(detail::self_tid());
}

/// Moves every thread of the process that is not owned to the aux set (or, with the feature off, does nothing).
/// Returns the number of threads whose placement changed.
inline int sweep() {
    detail::State& s = detail::state();
    if (!s.enabled.load(std::memory_order_acquire)) return 0;
    std::lock_guard<std::mutex> lk(s.mu);
    detail::purge_locked(s);
    int n = 0;
    for (int tid : detail::task_ids())
        if (s.owned.find(tid) == s.owned.end() && detail::move_locked(s, tid)) ++n;
    return n;
}

/// First thing a thread the engine creates does: it goes to the aux set while the feature is on.  Cheap when off.
inline void pin_current_thread() {
    detail::State& s = detail::state();
    if (!s.enabled.load(std::memory_order_acquire)) return;
    std::lock_guard<std::mutex> lk(s.mu);
    const int tid = detail::self_tid();
    if (s.owned.find(tid) == s.owned.end()) detail::move_locked(s, tid);
}

/// Pin an I/O-bound thread (DirectFile / ColdStore / async prefetcher) onto the SMT secondary / aux CPU set
/// so storage I/O and background DMA never steal primary compute cores.
inline void pin_io_thread() {
    detail::State& s = detail::state();
    if (!s.have_plan.load(std::memory_order_acquire)) return;
    const char* off_env = std::getenv("STRATA_AUX_IO_SMT");
    if (off_env && off_env[0] == '0') {
        pin_current_thread();
        return;
    }
    std::lock_guard<std::mutex> lk(s.mu);
    const int tid = detail::self_tid();
    if (s.owned.find(tid) != s.owned.end() || s.io_plan.empty()) return;
    (void) sched_setaffinity(tid, sizeof s.io_target, &s.io_target);
}

/// Puts back the placement every moved thread had.  Returns how many were restored.
inline int restore() {
    detail::State& s = detail::state();
    std::lock_guard<std::mutex> lk(s.mu);
    int n = 0;
    for (const auto& [tid, mask] : s.original)
        if (detail::alive(tid) && sched_setaffinity(tid, sizeof mask, &mask) == 0) ++n;
    s.original.clear();
    return n;
}

/// Turns the placement on (sweeping at once) or off (restoring the moved threads).  A no-op without a plan.
inline void set_enabled(bool on) {
    detail::State& s = detail::state();
    if (on) {
        if (!s.have_plan.load(std::memory_order_acquire)) return;
        s.enabled.store(true, std::memory_order_release);
        (void) sweep();
    } else {
        s.enabled.store(false, std::memory_order_release);
        (void) restore();
    }
}

inline bool enabled() { return detail::state().enabled.load(std::memory_order_acquire); }

namespace detail {
/// The CPUs a thread that must not share the host's core runs on: every CPU the process may use but the host's and
/// the pool workers' (on an SMT machine with the default pool, the idle sibling threads); without such CPUs, every CPU
/// but the host's; failing that, every CPU.  Caller holds `mu`.  False when `configure` saw no CPUs.
inline bool off_host_target_locked(const State& s, cpu_set_t& out) {
    if (s.allowed.empty()) return false;
    auto build = [&](bool skip_workers) {
        CPU_ZERO(&out);
        int n = 0;
        for (int c : s.allowed) {
            if (c == s.host_cpu) continue;
            if (skip_workers && std::find(s.workers.begin(), s.workers.end(), c) != s.workers.end()) continue;
            CPU_SET(c, &out);
            ++n;
        }
        return n;
    };
    if (build(true) > 0 || build(false) > 0) return true;
    CPU_ZERO(&out);
    for (int c : s.allowed) CPU_SET(c, &out);
    return true;
}
}  // namespace detail

/// Puts the calling thread off the host's core and off the pool workers' CPUs (see off_host_target_locked).  A thread
/// the host creates inherits the host's single CPU; one that must not share that core (the concurrent prompt read's
/// thread and its doorbell thread, STRATA_PIPED_CONCURRENT) calls this first.  False when nothing changed.
inline bool place_off_host() {
    detail::State& s = detail::state();
    std::lock_guard<std::mutex> lk(s.mu);
    cpu_set_t to;
    if (!detail::off_host_target_locked(s, to)) return false;
    return sched_setaffinity(0, sizeof to, &to) == 0;
}

/// Called on the host thread: every other thread that runs on exactly the host's CPUs (it inherited them: the prefill
/// copy threads started by the first prompt, a helper the host started) goes where place_off_host puts a thread.  The
/// pool's workers and the host threads are never moved.  Returns how many moved.
inline int release_host_inheritors() {
    detail::State& s = detail::state();
    std::lock_guard<std::mutex> lk(s.mu);
    cpu_set_t host, all, to;
    CPU_ZERO(&host);
    CPU_ZERO(&all);
    if (!detail::off_host_target_locked(s, to) || sched_getaffinity(0, sizeof host, &host) != 0) return 0;
    for (int c : s.allowed) CPU_SET(c, &all);
    if (detail::same_mask(host, all)) return 0;   // the host is not pinned: nothing inherited a single core
    detail::purge_locked(s);
    const int self = detail::self_tid();
    int n = 0;
    for (int tid : detail::task_ids()) {
        if (tid == self || s.owned.find(tid) != s.owned.end()) continue;
        cpu_set_t m;
        CPU_ZERO(&m);
        if (sched_getaffinity(tid, sizeof m, &m) != 0 || !detail::same_mask(m, host)) continue;
        if (sched_setaffinity(tid, sizeof to, &to) == 0) ++n;
    }
    return n;
}

/// The aux CPUs of the plan ({} when there is none).
inline std::vector<int> plan() {
    detail::State& s = detail::state();
    std::lock_guard<std::mutex> lk(s.mu);
    return s.plan;
}

/// The SMT/aux CPUs planned for I/O-bound threads ({} when there is none).
inline std::vector<int> io_plan() {
    detail::State& s = detail::state();
    std::lock_guard<std::mutex> lk(s.mu);
    return s.io_plan;
}

/// Reads sysfs for the cores of the process's CPUs.  `cpus` empty: every CPU `configure` saw.
inline std::vector<LogicalCpu> read_topology(const std::vector<int>& cpus) {
    auto read_id = [](int cpu, const char* what) -> long {
        char path[96];
        std::snprintf(path, sizeof path, "/sys/devices/system/cpu/cpu%d/topology/%s", cpu, what);
        long v = -1;
        if (std::FILE* f = std::fopen(path, "r")) {
            if (std::fscanf(f, "%ld", &v) != 1) v = -1;
            std::fclose(f);
        }
        return v;
    };
    std::vector<LogicalCpu> out;
    for (int c : cpus) out.push_back({c, read_id(c, "physical_package_id"), read_id(c, "core_id")});
    return out;
}

/// Works the plan out once the pool exists: `host_cpu` is the CPU the host thread is pinned to (-1: unknown) and
/// `worker_cpus` the CPUs of the pool's workers.  With the start-up setting on, the placement starts now.  Returns one
/// line for the log.
inline std::string set_topology(int host_cpu, const std::vector<int>& worker_cpus) {
    detail::State& s = detail::state();
    std::vector<int> plan;
    std::string note;
    {
        std::lock_guard<std::mutex> lk(s.mu);
        const std::vector<LogicalCpu> allowed = read_topology(s.allowed);
        plan = s.cfg.use_list ? restrict_list(s.cfg.list, allowed, host_cpu, worker_cpus)
                              : derive(allowed, host_cpu, worker_cpus);
        const std::vector<int> iop = s.cfg.use_list ? plan : derive_io_smt(allowed, host_cpu, worker_cpus);
        s.plan = plan;
        s.io_plan = iop;
        s.workers = worker_cpus;
        s.host_cpu = host_cpu;
        CPU_ZERO(&s.target);
        for (int c : plan) CPU_SET(c, &s.target);
        CPU_ZERO(&s.io_target);
        for (int c : iop) CPU_SET(c, &s.io_target);
        s.have_plan.store(!plan.empty() || !iop.empty(), std::memory_order_release);
        for (size_t i = 0; i < plan.size(); ++i) note += (i ? "," : "") + std::to_string(plan[i]);
    }
    if (plan.empty()) note = "none spare (every CPU is the host's, a worker's or shares a core with a worker or has no known core)";
    if (s.cfg.on && !plan.empty()) set_enabled(true);
    long moved;
    {
        std::lock_guard<std::mutex> lk(s.mu);
        moved = (long) s.original.size();
    }
    return "strata aux cpus: threads that are neither pool workers nor the host go to CPUs " + note +
           (!s.cfg.on ? " (off at start; a request's aux_cpus=1 turns it on)"
            : plan.empty() ? " (nothing to do)" : " (on; " + std::to_string(moved) + " threads placed so far)");
}

#elif defined(_WIN32)

namespace detail {

struct State {
    std::mutex mu;
    Config cfg;
    std::atomic<bool> enabled{false};
    std::atomic<bool> have_plan{false};
    std::vector<int> allowed;                     ///< encoded CPUs (group * 64 + bit) the process may use
    std::vector<int> plan;                        ///< aux CPUs (host SMT sibling + free physical cores, or explicit list)
    std::vector<int> io_plan;                     ///< aux + worker SMT secondary threads for async SSD/DMA I/O
    std::vector<int> workers;                     ///< pool worker CPUs: never touched
    int host_cpu = -1;                            ///< host thread CPU (-1: unknown)
    std::vector<ULONG> target_sets;               ///< Windows CPU Set IDs for `plan`
    std::vector<ULONG> io_target_sets;            ///< Windows CPU Set IDs for `io_plan`
    std::set<DWORD> owned;                        ///< Win32 TIDs of pool workers and host thread
    std::map<DWORD, std::vector<ULONG>> original; ///< tid -> CPU Sets before move
};

inline State& state() {
    static State s;
    return s;
}

inline DWORD self_tid() { return GetCurrentThreadId(); }

inline std::vector<LogicalCpu> read_topology_win(const std::vector<int>& filter) {
    std::vector<LogicalCpu> out;
    DWORD len = 0;
    GetLogicalProcessorInformationEx(RelationProcessorCore, nullptr, &len);
    if (len == 0) return out;
    std::vector<char> buf(len);
    if (!GetLogicalProcessorInformationEx(RelationProcessorCore,
                                          reinterpret_cast<PSYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX>(buf.data()), &len))
        return out;
    DWORD_PTR proc_mask = 0, sys_mask = 0;
    const bool limited =
        GetActiveProcessorGroupCount() == 1 && GetProcessAffinityMask(GetCurrentProcess(), &proc_mask, &sys_mask);
    long core = 0;
    for (DWORD off = 0; off < len;) {
        const auto* e = reinterpret_cast<const SYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX*>(buf.data() + off);
        if (e->Size == 0 || off + e->Size > len) break;
        if (e->Relationship == RelationProcessorCore) {
            for (WORD gi = 0; gi < e->Processor.GroupCount; ++gi) {
                const GROUP_AFFINITY& g = e->Processor.GroupMask[gi];
                for (int bit = 0; bit < 64; ++bit) {
                    if (!(g.Mask & (KAFFINITY(1) << bit))) continue;
                    if (limited && !(proc_mask & (DWORD_PTR(1) << bit))) continue;
                    const int cpu = (int) g.Group * 64 + bit;
                    if (!filter.empty() && std::find(filter.begin(), filter.end(), cpu) == filter.end()) continue;
                    out.push_back({cpu, (long) g.Group, core});
                }
            }
            ++core;
        }
        off += e->Size;
    }
    return out;
}

inline std::vector<ULONG> cpu_sets_for_cpus(const std::vector<int>& cpus) {
    std::vector<ULONG> ids;
    if (cpus.empty()) return ids;
    ULONG bytes = 0;
    if (!GetSystemCpuSetInformation(nullptr, 0, &bytes, GetCurrentProcess(), 0) &&
        GetLastError() != ERROR_INSUFFICIENT_BUFFER)
        return ids;
    if (bytes == 0) return ids;
    std::vector<unsigned char> buf(bytes);
    if (!GetSystemCpuSetInformation(reinterpret_cast<PSYSTEM_CPU_SET_INFORMATION>(buf.data()), bytes, &bytes,
                                    GetCurrentProcess(), 0))
        return ids;
    constexpr size_t hdr = offsetof(SYSTEM_CPU_SET_INFORMATION, CpuSet);
    for (size_t off = 0; off + hdr <= bytes;) {
        const auto* info = reinterpret_cast<const SYSTEM_CPU_SET_INFORMATION*>(buf.data() + off);
        if (info->Size < hdr || info->Size > bytes - off) break;
        if (info->Type == CpuSetInformation && info->Size >= sizeof(SYSTEM_CPU_SET_INFORMATION) &&
            (!info->CpuSet.Allocated || info->CpuSet.AllocatedToTargetProcess)) {
            const int enc = (int) info->CpuSet.Group * 64 + (int) info->CpuSet.LogicalProcessorIndex;
            if (std::find(cpus.begin(), cpus.end(), enc) != cpus.end()) ids.push_back(info->CpuSet.Id);
        }
        off += info->Size;
    }
    return ids;
}

inline bool get_sets_for_handle(HANDLE th, std::vector<ULONG>& ids) {
    ULONG count = 0;
    if (!GetThreadSelectedCpuSets(th, nullptr, 0, &count) && GetLastError() != ERROR_INSUFFICIENT_BUFFER) return false;
    ids.resize(count);
    if (count == 0) return true;
    if (!GetThreadSelectedCpuSets(th, ids.data(), count, &count)) return false;
    ids.resize(count);
    return true;
}

inline bool set_sets_for_handle(HANDLE th, const std::vector<ULONG>& ids) {
    return SetThreadSelectedCpuSets(th, ids.empty() ? nullptr : ids.data(), (ULONG) ids.size()) != FALSE;
}

inline std::vector<DWORD> process_tids() {
    std::vector<DWORD> tids;
    const DWORD pid = GetCurrentProcessId();
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (snap == INVALID_HANDLE_VALUE) return tids;
    THREADENTRY32 te{};
    te.dwSize = sizeof(te);
    if (Thread32First(snap, &te)) {
        do {
            if (te.dwSize >= offsetof(THREADENTRY32, th32OwnerProcessID) + sizeof(te.th32OwnerProcessID) &&
                te.th32OwnerProcessID == pid) {
                tids.push_back(te.th32ThreadID);
            }
            te.dwSize = sizeof(te);
        } while (Thread32Next(snap, &te));
    }
    CloseHandle(snap);
    return tids;
}

inline bool move_locked(State& s, DWORD tid, const std::vector<ULONG>& dest_sets) {
    if (dest_sets.empty()) return false;
    const bool is_self = (tid == self_tid());
    HANDLE th = is_self ? GetCurrentThread()
                        : OpenThread(THREAD_SET_LIMITED_INFORMATION | THREAD_QUERY_LIMITED_INFORMATION, FALSE, tid);
    if (th == nullptr) return false;
    std::vector<ULONG> now;
    bool changed = false;
    if (get_sets_for_handle(th, now) && now != dest_sets) {
        // Respect threads explicitly single-pinned to a worker CPU by another subsystem.
        bool pinned_to_worker = false;
        if (now.size() == 1) {
            const std::vector<ULONG> wsets = cpu_sets_for_cpus(s.workers);
            pinned_to_worker = std::find(wsets.begin(), wsets.end(), now[0]) != wsets.end();
        }
        if (!pinned_to_worker && set_sets_for_handle(th, dest_sets)) {
            s.original.emplace(tid, std::move(now));
            changed = true;
        }
    }
    if (!is_self) CloseHandle(th);
    return changed;
}

inline void purge_locked(State& s) {
    const std::vector<DWORD> live = process_tids();
    auto is_alive = [&](DWORD tid) { return std::find(live.begin(), live.end(), tid) != live.end(); };
    for (auto it = s.original.begin(); it != s.original.end();)
        it = is_alive(it->first) ? std::next(it) : s.original.erase(it);
    for (auto it = s.owned.begin(); it != s.owned.end();)
        it = is_alive(*it) ? std::next(it) : s.owned.erase(it);
}

}  // namespace detail

inline bool configure(const std::string& spec, std::string& err) {
    detail::State& s = detail::state();
    Config cfg;
    if (!parse_spec(spec, cfg, err)) return false;
    std::lock_guard<std::mutex> lk(s.mu);
    s.cfg = cfg;
    s.allowed.clear();
    for (const LogicalCpu& c : detail::read_topology_win({})) s.allowed.push_back(c.cpu);
    s.owned.insert(detail::self_tid());
    return true;
}

inline void note_owned_thread() {
    detail::State& s = detail::state();
    std::lock_guard<std::mutex> lk(s.mu);
    s.owned.insert(detail::self_tid());
}

inline int sweep() {
    detail::State& s = detail::state();
    if (!s.enabled.load(std::memory_order_acquire)) return 0;
    std::lock_guard<std::mutex> lk(s.mu);
    detail::purge_locked(s);
    int n = 0;
    for (DWORD tid : detail::process_tids())
        if (s.owned.find(tid) == s.owned.end() && detail::move_locked(s, tid, s.target_sets)) ++n;
    return n;
}

inline void pin_current_thread() {
    detail::State& s = detail::state();
    if (!s.enabled.load(std::memory_order_acquire)) return;
    std::lock_guard<std::mutex> lk(s.mu);
    const DWORD tid = detail::self_tid();
    if (s.owned.find(tid) == s.owned.end()) (void) detail::move_locked(s, tid, s.target_sets);
}

/// Pin an I/O-bound thread (DirectFile / ColdStore / async SSD prefetcher) onto the SMT secondary CPU set
/// (e.g. logical CPUs 1,3,5,7,9,11 on a 6C/12T Ryzen) so NVMe/SSD I/O overlaps AVX2 compute with zero contention.
inline void pin_io_thread() {
    detail::State& s = detail::state();
    if (!s.have_plan.load(std::memory_order_acquire)) return;
    char off_env[16] = {};
    if (GetEnvironmentVariableA("STRATA_AUX_IO_SMT", off_env, (DWORD) sizeof off_env) > 0 && off_env[0] == '0') {
        pin_current_thread();
        return;
    }
    std::lock_guard<std::mutex> lk(s.mu);
    const DWORD tid = detail::self_tid();
    if (s.owned.find(tid) != s.owned.end()) return;
    const auto& dest = !s.io_target_sets.empty() ? s.io_target_sets : s.target_sets;
    if (!dest.empty()) (void) detail::set_sets_for_handle(GetCurrentThread(), dest);
}

inline int restore() {
    detail::State& s = detail::state();
    std::lock_guard<std::mutex> lk(s.mu);
    int n = 0;
    for (const auto& [tid, orig] : s.original) {
        const bool is_self = (tid == detail::self_tid());
        HANDLE th = is_self ? GetCurrentThread()
                            : OpenThread(THREAD_SET_LIMITED_INFORMATION | THREAD_QUERY_LIMITED_INFORMATION, FALSE, tid);
        if (th == nullptr) continue;
        if (detail::set_sets_for_handle(th, orig)) ++n;
        if (!is_self) CloseHandle(th);
    }
    s.original.clear();
    return n;
}

inline void set_enabled(bool on) {
    detail::State& s = detail::state();
    if (on) {
        if (!s.have_plan.load(std::memory_order_acquire)) return;
        s.enabled.store(true, std::memory_order_release);
        (void) sweep();
    } else {
        s.enabled.store(false, std::memory_order_release);
        (void) restore();
    }
}

inline bool enabled() { return detail::state().enabled.load(std::memory_order_acquire); }

inline bool place_off_host() {
    detail::State& s = detail::state();
    std::lock_guard<std::mutex> lk(s.mu);
    if (s.allowed.empty()) return false;
    std::vector<int> dest;
    for (int c : s.allowed) {
        if (c == s.host_cpu) continue;
        if (std::find(s.workers.begin(), s.workers.end(), c) != s.workers.end()) continue;
        dest.push_back(c);
    }
    if (dest.empty()) {
        for (int c : s.allowed)
            if (c != s.host_cpu) dest.push_back(c);
    }
    const std::vector<ULONG> sets = detail::cpu_sets_for_cpus(dest);
    return !sets.empty() && detail::set_sets_for_handle(GetCurrentThread(), sets);
}

inline int release_host_inheritors() { return 0; }   // Windows threads do not inherit CPU Sets

inline std::vector<int> plan() {
    detail::State& s = detail::state();
    std::lock_guard<std::mutex> lk(s.mu);
    return s.plan;
}

inline std::vector<int> io_plan() {
    detail::State& s = detail::state();
    std::lock_guard<std::mutex> lk(s.mu);
    return s.io_plan;
}

inline std::string set_topology(int host_cpu, const std::vector<int>& worker_cpus) {
    detail::State& s = detail::state();
    std::vector<int> pl, iop;
    std::string note, io_note;
    {
        std::lock_guard<std::mutex> lk(s.mu);
        if (s.allowed.empty()) {
            for (const LogicalCpu& c : detail::read_topology_win({})) s.allowed.push_back(c.cpu);
            s.owned.insert(detail::self_tid());
        }
        const std::vector<LogicalCpu> allowed = detail::read_topology_win(s.allowed);
        pl = s.cfg.use_list ? restrict_list(s.cfg.list, allowed, host_cpu, worker_cpus)
                            : derive(allowed, host_cpu, worker_cpus);
        iop = s.cfg.use_list ? pl : derive_io_smt(allowed, host_cpu, worker_cpus);
        s.plan = pl;
        s.io_plan = iop;
        s.workers = worker_cpus;
        s.host_cpu = host_cpu;
        s.target_sets = detail::cpu_sets_for_cpus(pl);
        s.io_target_sets = detail::cpu_sets_for_cpus(iop);
        s.have_plan.store(!s.target_sets.empty() || !s.io_target_sets.empty(), std::memory_order_release);
        for (size_t i = 0; i < pl.size(); ++i) note += (i ? "," : "") + std::to_string(pl[i]);
        for (size_t i = 0; i < iop.size(); ++i) io_note += (i ? "," : "") + std::to_string(iop[i]);
    }
    if (pl.empty()) note = "none spare";
    if (s.cfg.on && !pl.empty()) set_enabled(true);
    long moved = 0;
    {
        std::lock_guard<std::mutex> lk(s.mu);
        moved = (long) s.original.size();
    }
    return "strata aux cpus (Windows): aux=[" + note + "] io_smt=[" + (io_note.empty() ? "none" : io_note) + "]" +
           (!s.cfg.on ? " (aux sweep off; io_smt active)"
            : pl.empty() ? " (nothing to sweep)"
                         : " (on; " + std::to_string(moved) + " threads placed so far)");
}

#else  // other OSes: the same names, doing nothing

inline bool configure(const std::string& spec, std::string& err) {
    Config cfg;
    return parse_spec(spec, cfg, err);
}
inline void note_owned_thread() {}
inline int sweep() { return 0; }
inline void pin_current_thread() {}
inline void pin_io_thread() {}
inline int restore() { return 0; }
inline void set_enabled(bool) {}
inline bool enabled() { return false; }
inline bool place_off_host() { return false; }
inline int release_host_inheritors() { return 0; }
inline std::vector<int> plan() { return {}; }
inline std::vector<int> io_plan() { return {}; }
inline std::string set_topology(int, const std::vector<int>&) { return "strata aux cpus: not available on this system"; }

#endif

}  // namespace strata::aux_cpus
