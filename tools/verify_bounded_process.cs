// Loaded by Add-Type. C# 5 syntax supports the inbox PowerShell 5.1 compiler.
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;

namespace StrataValidation
{
    /// <summary>Child exit and guard failure are separate observations.</summary>
    public sealed class RunResult
    {
        public uint? ChildExitCode;
        public string GuardReason, Error;
        public bool ContainedBeforeResume;
        public uint? ActiveProcessesAfterCleanup;
        public long CapturedBytes, OutputBytes, FreeBytes;
    }

    /// <summary>Retain directory handles to prevent evidence path replacement.</summary>
    public sealed class EvidenceScope : IDisposable
    {
        readonly List<IntPtr> locks = new List<IntPtr>();
        public string Root { get; private set; }

        public EvidenceScope(string path)
        {
            string normalized = path.Replace('/', '\\').TrimEnd('\\');
            if (!Regex.IsMatch(normalized, @"^H:\\Strata\\build\\task5a-[a-zA-Z0-9-]+(?:\\[^<>:""/\\|?*\x00-\x1f]+)*$", RegexOptions.IgnoreCase))
                throw new ArgumentException("Expected dedicated H:/Strata/build/task5a-* output root");
            string[] parts = normalized.Substring(3).Split('\\');
            foreach (string part in parts)
                if (part == "." || part == ".." || part.EndsWith(".") || part.EndsWith(" ") ||
                    Regex.IsMatch(part, @"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", RegexOptions.IgnoreCase))
                    throw new ArgumentException("Invalid evidence path component");
            Root = Path.GetFullPath(normalized);
            try
            {
                string current = "H:\\";
                LockDirectory(current);
                foreach (string part in parts)
                {
                    current = Path.Combine(current, part);
                    if (!Directory.Exists(current)) Directory.CreateDirectory(current);
                    LockDirectory(current);
                }
            }
            catch { Dispose(); throw; }
        }

        void LockDirectory(string path)
        {
            IntPtr handle = Native.CreateFile(path, 0, 3, IntPtr.Zero, 3, 0x02200000, IntPtr.Zero);
            Native.Require(handle != new IntPtr(-1), "Open evidence directory");
            locks.Add(handle);
            Native.FileInformation info;
            Native.Require(Native.GetFileInformationByHandle(handle, out info), "Inspect evidence directory");
            if ((info.Attributes & 0x400) != 0 || (info.Attributes & 0x10) == 0)
                throw new IOException("Reparse or non-directory evidence path rejected");
        }

        /// <summary>Never follow a reparse point while counting evidence.</summary>
        public long Measure() { return MeasureDirectory(Root); }

        static long MeasureDirectory(string path)
        {
            long bytes = 0;
            foreach (string entry in Directory.EnumerateFileSystemEntries(path))
            {
                try
                {
                    FileAttributes attributes = File.GetAttributes(entry);
                    if ((attributes & FileAttributes.ReparsePoint) != 0)
                        throw new IOException("Reparse point inside evidence root rejected");
                    bytes = checked(bytes + ((attributes & FileAttributes.Directory) != 0
                        ? MeasureDirectory(entry) : new FileInfo(entry).Length));
                }
                // Compilers routinely remove temporary files between enumeration and stat.
                catch (FileNotFoundException) { }
                catch (DirectoryNotFoundException) { }
            }
            return bytes;
        }

        /// <summary>Read live bytes available to this user on the actual volume.</summary>
        public long FreeBytes()
        {
            ulong available, total, free;
            Native.Require(Native.GetDiskFreeSpaceEx(Root, out available, out total, out free), "Read volume capacity");
            return checked((long)available);
        }

        public void Dispose()
        {
            for (int i = locks.Count - 1; i >= 0; --i) Native.CloseHandle(locks[i]);
            locks.Clear();
        }
    }

    /// <summary>Run one console tool in a private non-breakaway Job Object.</summary>
    public static class BoundedProcess
    {
        const uint GuardExit = 125;

        // CRT quoting preserves empty arguments, embedded quotes and trailing slashes.
        static string Quote(string value)
        {
            if (value == null || value.IndexOf('\0') >= 0) throw new ArgumentException("Invalid argument");
            StringBuilder result = new StringBuilder("\"");
            int slashes = 0;
            foreach (char ch in value)
            {
                if (ch == '\\') { ++slashes; continue; }
                result.Append('\\', ch == '"' ? slashes * 2 + 1 : slashes);
                result.Append(ch);
                slashes = 0;
            }
            return result.Append('\\', slashes * 2).Append('"').ToString();
        }

        static void Close(ref IntPtr handle)
        {
            if (handle != IntPtr.Zero && handle != new IntPtr(-1)) Native.CloseHandle(handle);
            handle = IntPtr.Zero;
        }

        static void DisposeOutput(FileStream stream, RunResult result)
        {
            try { if (stream != null) stream.Dispose(); }
            catch (Exception error)
            {
                result.GuardReason = result.GuardReason ?? "cleanup_error";
                result.Error = (result.Error == null ? "" : result.Error + "; ") + error.Message;
            }
        }

        static uint Active(IntPtr job)
        {
            Native.JobAccounting accounting;
            Native.Require(Native.QueryInformationJobObject(job, 1, out accounting,
                (uint)Marshal.SizeOf(typeof(Native.JobAccounting)), IntPtr.Zero), "Read owned job accounting");
            return accounting.ActiveProcesses;
        }

        static bool Capture(IntPtr pipe, FileStream output, RunResult result, long cap)
        {
            uint available, read;
            if (!Native.PeekNamedPipe(pipe, IntPtr.Zero, 0, IntPtr.Zero, out available, IntPtr.Zero))
            {
                if (Marshal.GetLastWin32Error() == 109) return false;
                throw new Win32Exception(Marshal.GetLastWin32Error(), "Peek child output");
            }
            if (available == 0) return false;
            byte[] buffer = new byte[Math.Min(available, 16384U)];
            Native.Require(Native.ReadFile(pipe, buffer, (uint)buffer.Length, out read, IntPtr.Zero), "Read child output");
            int keep = (int)Math.Min((long)read, Math.Max(0, cap - result.CapturedBytes));
            output.Write(buffer, 0, keep);
            output.Flush();
            result.CapturedBytes += keep;
            if (keep < read) result.GuardReason = "output_limit";
            return true;
        }

        /// <summary>Retain all OS handles, including failed suspended starts, through cleanup.</summary>
        public static RunResult Run(EvidenceScope scope, string label, string executable,
            string[] arguments, string workingDirectory, long reserve, long peak, long cap, int timeoutSeconds)
        {
            RunResult result = new RunResult();
            IntPtr job = IntPtr.Zero, input = IntPtr.Zero, outRead = IntPtr.Zero, outWrite = IntPtr.Zero;
            IntPtr errRead = IntPtr.Zero, errWrite = IntPtr.Zero, attributes = IntPtr.Zero, handles = IntPtr.Zero;
            IntPtr jobList = IntPtr.Zero;
            Native.ProcessInformation process = new Native.ProcessInformation();
            bool assigned = false, attributesInitialized = false;
            FileStream stdout = null, stderr = null;
            try
            {
                if (!Path.IsPathRooted(executable) || !File.Exists(executable) ||
                    !executable.EndsWith(".exe", StringComparison.OrdinalIgnoreCase))
                    throw new ArgumentException("Executable must resolve to an existing native .exe");
                StringBuilder command = new StringBuilder(Quote(executable));
                foreach (string argument in arguments) command.Append(' ').Append(Quote(argument));
                if (command.Length >= 32767) throw new ArgumentException("Command line exceeds Windows limit");
                result.FreeBytes = scope.FreeBytes();
                result.OutputBytes = scope.Measure();
                if (reserve < 10L * 1024 * 1024 * 1024 || peak < cap || cap <= 0 || timeoutSeconds <= 0)
                    throw new ArgumentException("Require reserve >= 10 GiB, peak >= output cap > 0 and a positive timeout");
                if (result.FreeBytes < reserve || peak > result.FreeBytes - reserve)
                { result.GuardReason = "start_capacity"; return result; }
                if (result.OutputBytes > cap)
                { result.GuardReason = "output_limit"; return result; }
                stdout = new FileStream(Path.Combine(scope.Root, label + ".stdout.log"), FileMode.CreateNew, FileAccess.Write, FileShare.Read);
                stderr = new FileStream(Path.Combine(scope.Root, label + ".stderr.log"), FileMode.CreateNew, FileAccess.Write, FileShare.Read);
                job = Native.CreateJobObject(IntPtr.Zero, null);
                Native.Require(job != IntPtr.Zero, "Create private job");
                Native.JobLimits limits = new Native.JobLimits();
                limits.Basic.LimitFlags = 0x2000; // KILL_ON_JOB_CLOSE only, no breakaway flags.
                Native.Require(Native.SetInformationJobObject(job, 9, ref limits,
                    (uint)Marshal.SizeOf(typeof(Native.JobLimits))), "Set private job limits");
                Native.SecurityAttributes security = new Native.SecurityAttributes();
                security.Length = Marshal.SizeOf(typeof(Native.SecurityAttributes));
                security.InheritHandle = 1;
                Native.Require(Native.CreatePipe(out outRead, out outWrite, ref security, 4096), "Create stdout pipe");
                Native.Require(Native.CreatePipe(out errRead, out errWrite, ref security, 4096), "Create stderr pipe");
                Native.Require(Native.SetHandleInformation(outRead, 1, 0), "Protect stdout reader");
                Native.Require(Native.SetHandleInformation(errRead, 1, 0), "Protect stderr reader");
                input = Native.CreateFileInherited("NUL", 0x80000000, 3, ref security, 3, 0, IntPtr.Zero);
                Native.Require(input != new IntPtr(-1), "Open null stdin");
                IntPtr size = IntPtr.Zero;
                Native.InitializeProcThreadAttributeList(IntPtr.Zero, 2, 0, ref size);
                attributes = Marshal.AllocHGlobal(size);
                Native.Require(Native.InitializeProcThreadAttributeList(attributes, 2, 0, ref size), "Initialize attribute list");
                attributesInitialized = true;
                handles = Marshal.AllocHGlobal(3 * IntPtr.Size);
                Marshal.WriteIntPtr(handles, 0, input);
                Marshal.WriteIntPtr(handles, IntPtr.Size, outWrite);
                Marshal.WriteIntPtr(handles, 2 * IntPtr.Size, errWrite);
                Native.Require(Native.UpdateProcThreadAttribute(attributes, 0, new IntPtr(0x20002),
                    handles, new IntPtr(3 * IntPtr.Size), IntPtr.Zero, IntPtr.Zero), "Restrict inherited handles");
                // Windows 10+: atomic assignment closes the host-death gap between
                // CreateProcess(CREATE_SUSPENDED) and AssignProcessToJobObject.
                jobList = Marshal.AllocHGlobal(IntPtr.Size);
                Marshal.WriteIntPtr(jobList, job);
                Native.Require(Native.UpdateProcThreadAttribute(attributes, 0, new IntPtr(0x2000D),
                    jobList, new IntPtr(IntPtr.Size), IntPtr.Zero, IntPtr.Zero), "Assign private job at creation");
                Native.StartupInfoEx startup = new Native.StartupInfoEx();
                startup.Startup.Size = Marshal.SizeOf(typeof(Native.StartupInfoEx));
                startup.Startup.Flags = 0x101; // USESTDHANDLES | USESHOWWINDOW; hidden.
                startup.Startup.Input = input;
                startup.Startup.Output = outWrite;
                startup.Startup.Error = errWrite;
                startup.Attributes = attributes;
                // CREATE_SUSPENDED | EXTENDED_STARTUPINFO_PRESENT | CREATE_NO_WINDOW.
                Native.Require(Native.CreateProcess(executable, command, IntPtr.Zero, IntPtr.Zero, true,
                    0x08080004, IntPtr.Zero, workingDirectory, ref startup, out process), "Create suspended child");
                assigned = true;
                bool inJob;
                Native.Require(Native.IsProcessInJob(process.Process, job, out inJob) && inJob, "Verify suspended child containment");
                result.ContainedBeforeResume = true;
                Close(ref outWrite); Close(ref errWrite); Close(ref input);
                Native.Require(Native.ResumeThread(process.Thread) != UInt32.MaxValue, "Resume contained child");
                Close(ref process.Thread);
                Stopwatch timer = Stopwatch.StartNew();
                while (true)
                {
                    Capture(outRead, stdout, result, cap);
                    Capture(errRead, stderr, result, cap);
                    result.OutputBytes = scope.Measure();
                    result.FreeBytes = scope.FreeBytes();
                    if (result.OutputBytes > cap) result.GuardReason = "output_limit";
                    if (result.FreeBytes < reserve) result.GuardReason = "disk_reserve";
                    if (timer.Elapsed.TotalSeconds >= timeoutSeconds) result.GuardReason = "timeout";
                    uint wait = Native.WaitForSingleObject(process.Process, 0);
                    Native.Require(wait != UInt32.MaxValue, "Wait for owned child");
                    if (wait == 0 || result.GuardReason != null) break;
                    Thread.Sleep(20);
                }
            }
            catch (Exception error)
            {
                result.GuardReason = result.GuardReason ?? "runner_error";
                result.Error = error.Message;
            }
            finally
            {
                try
                {
                    if (process.Process != IntPtr.Zero)
                    {
                        // A retained handle protects against PID reuse; no process rediscovery.
                        if (assigned) Native.Require(Native.TerminateJobObject(job, GuardExit), "Terminate owned job");
                        else Native.Require(Native.TerminateProcess(process.Process, GuardExit), "Terminate unstarted child");
                        Native.Require(Native.WaitForSingleObject(process.Process, 5000) == 0, "Confirm child exit");
                        uint exitCode;
                        Native.Require(Native.GetExitCodeProcess(process.Process, out exitCode), "Read child exit code");
                        result.ChildExitCode = exitCode;
                        if (assigned)
                        {
                            Stopwatch cleanup = Stopwatch.StartNew();
                            while (Active(job) != 0 && cleanup.ElapsedMilliseconds < 5000) Thread.Sleep(10);
                            result.ActiveProcessesAfterCleanup = Active(job);
                            Native.Require(result.ActiveProcessesAfterCleanup == 0, "Confirm descendant exit");
                        }
                        // Writers are dead: drain remaining bounded pipe buffers without waiting.
                        if (stdout != null) while (Capture(outRead, stdout, result, cap)) { }
                        if (stderr != null) while (Capture(errRead, stderr, result, cap)) { }
                    }
                    result.OutputBytes = scope.Measure();
                    result.FreeBytes = scope.FreeBytes();
                    if (result.OutputBytes > cap) result.GuardReason = result.GuardReason ?? "output_limit";
                    if (result.FreeBytes < reserve) result.GuardReason = result.GuardReason ?? "disk_reserve";
                }
                catch (Exception error)
                {
                    result.GuardReason = result.GuardReason ?? "cleanup_error";
                    result.Error = (result.Error == null ? "" : result.Error + "; ") + error.Message;
                }
                finally
                {
                    // Closing the non-inheritable job covers host abort / cleanup failure too.
                    Close(ref job); Close(ref process.Thread); Close(ref process.Process);
                    Close(ref input); Close(ref outWrite); Close(ref errWrite);
                    Close(ref outRead); Close(ref errRead);
                    // A flush failure must not skip releasing the other stream or native buffers.
                    DisposeOutput(stdout, result);
                    DisposeOutput(stderr, result);
                    if (attributesInitialized) Native.DeleteProcThreadAttributeList(attributes);
                    if (attributes != IntPtr.Zero) Marshal.FreeHGlobal(attributes);
                    if (handles != IntPtr.Zero) Marshal.FreeHGlobal(handles);
                    if (jobList != IntPtr.Zero) Marshal.FreeHGlobal(jobList);
                }
            }
            return result;
        }
    }

    internal static class Native
    {
        internal static void Require(bool success, string operation)
        { if (!success) throw new Win32Exception(Marshal.GetLastWin32Error(), operation); }

        [StructLayout(LayoutKind.Sequential)] internal struct SecurityAttributes { public int Length; public IntPtr Descriptor; public int InheritHandle; }
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)] internal struct StartupInfo
        {
            public int Size; public string Reserved, Desktop, Title;
            public uint X, Y, XSize, YSize, XCount, YCount, Fill, Flags;
            public ushort ShowWindow, ReservedSize; public IntPtr ReservedBytes, Input, Output, Error;
        }
        [StructLayout(LayoutKind.Sequential)] internal struct StartupInfoEx { public StartupInfo Startup; public IntPtr Attributes; }
        [StructLayout(LayoutKind.Sequential)] internal struct ProcessInformation { public IntPtr Process, Thread; public uint ProcessId, ThreadId; }
        [StructLayout(LayoutKind.Sequential)] internal struct BasicLimits
        {
            public long ProcessTime, JobTime; public uint LimitFlags; public UIntPtr MinWorking, MaxWorking;
            public uint ActiveLimit; public UIntPtr Affinity; public uint Priority, Scheduling;
        }
        [StructLayout(LayoutKind.Sequential)] internal struct IoCounters { public ulong Read, Write, Other, ReadBytes, WriteBytes, OtherBytes; }
        [StructLayout(LayoutKind.Sequential)] internal struct JobLimits
        { public BasicLimits Basic; public IoCounters Io; public UIntPtr ProcessMemory, JobMemory, PeakProcess, PeakJob; }
        [StructLayout(LayoutKind.Sequential)] internal struct JobAccounting
        { public long User, Kernel, PeriodUser, PeriodKernel; public uint PageFaults, TotalProcesses, ActiveProcesses, Terminated; }
        [StructLayout(LayoutKind.Sequential)] internal struct FileInformation
        { public uint Attributes; public System.Runtime.InteropServices.ComTypes.FILETIME Created, Accessed, Written; public uint Volume, SizeHigh, SizeLow, Links, IndexHigh, IndexLow; }

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)] internal static extern IntPtr CreateJobObject(IntPtr security, string name);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern bool SetInformationJobObject(IntPtr job, int type, ref JobLimits info, uint size);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern bool QueryInformationJobObject(IntPtr job, int type, out JobAccounting info, uint size, IntPtr returned);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern bool IsProcessInJob(IntPtr process, IntPtr job, out bool inJob);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern bool TerminateJobObject(IntPtr job, uint code);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern bool TerminateProcess(IntPtr process, uint code);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern bool CloseHandle(IntPtr handle);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern bool CreatePipe(out IntPtr read, out IntPtr write, ref SecurityAttributes security, uint size);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern bool SetHandleInformation(IntPtr handle, uint mask, uint flags);
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)] internal static extern IntPtr CreateFile(string path, uint access, uint share, IntPtr security, uint mode, uint flags, IntPtr template);
        [DllImport("kernel32.dll", EntryPoint = "CreateFileW", SetLastError = true, CharSet = CharSet.Unicode)] internal static extern IntPtr CreateFileInherited(string path, uint access, uint share, ref SecurityAttributes security, uint mode, uint flags, IntPtr template);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern bool GetFileInformationByHandle(IntPtr file, out FileInformation info);
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)] internal static extern bool GetDiskFreeSpaceEx(string path, out ulong available, out ulong total, out ulong free);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern bool InitializeProcThreadAttributeList(IntPtr list, int count, uint flags, ref IntPtr size);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern bool UpdateProcThreadAttribute(IntPtr list, uint flags, IntPtr attribute, IntPtr value, IntPtr size, IntPtr previous, IntPtr returned);
        [DllImport("kernel32.dll")] internal static extern void DeleteProcThreadAttributeList(IntPtr list);
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)] internal static extern bool CreateProcess(string app, StringBuilder command, IntPtr processSecurity, IntPtr threadSecurity, bool inherit, uint flags, IntPtr environment, string directory, ref StartupInfoEx startup, out ProcessInformation info);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern uint ResumeThread(IntPtr thread);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern bool GetExitCodeProcess(IntPtr process, out uint exitCode);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern bool PeekNamedPipe(IntPtr pipe, IntPtr buffer, uint size, IntPtr read, out uint available, IntPtr remaining);
        [DllImport("kernel32.dll", SetLastError = true)] internal static extern bool ReadFile(IntPtr file, byte[] buffer, uint size, out uint read, IntPtr overlapped);
    }
}
