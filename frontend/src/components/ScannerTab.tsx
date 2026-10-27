import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import {
  Play,
  RotateCcw,
  Copy,
  Check,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  Clock,
  Cpu,
  Info,
  ChevronDown,
  Sparkles,
} from 'lucide-react';
import type { ModelDetails, ScanResponse } from '../types/api';
import { ApiService } from '../services/api';

interface ScannerTabProps {
  models: ModelDetails[];
  defaultModelId: string;
}

const PRESET_TEMPLATES: Record<string, { title: string; code: string; cwe: string; description: string }> = {
  buffer_overflow: {
    title: 'Buffer Overflow (CWE-120)',
    cwe: 'CWE-120',
    description: 'Classic stack-based buffer overflow using unbounded strcpy into a fixed 16-byte buffer.',
    code: `/* Classic CWE-120: Buffer Overflow via unbounded strcpy */
#include <stdio.h>
#include <string.h>

void process_client_packet(const char *user_input) {
    char internal_buffer[16];
    
    // Unsafe string copy without bounds check
    strcpy(internal_buffer, user_input);
    printf("Processed input: %s\\n", internal_buffer);
}
`,
  },
  command_injection: {
    title: 'Command Injection (CWE-78)',
    cwe: 'CWE-78',
    description: 'Executing system commands directly with unsanitized user-supplied parameters.',
    code: `/* CWE-78: OS Command Injection via system() */
#include <stdlib.h>
#include <stdio.h>

void execute_ping(const char *host_ip) {
    char command[256];
    
    // Insecure command concatenation with user input
    sprintf(command, "ping -c 3 %s", host_ip);
    system(command);
}
`,
  },
  double_free: {
    title: 'Double Free (CWE-415)',
    cwe: 'CWE-415',
    description: 'Deallocating the same heap memory buffer twice, creating memory corruption vulnerabilities.',
    code: `/* CWE-415: Double Free vulnerability */
#include <stdlib.h>

void cleanup_session_data(char *session_token, int error_flag) {
    free(session_token);
    
    if (error_flag) {
        // Redundant deallocation of the same pointer
        free(session_token);
    }
}
`,
  },
  safe_bounds_checked: {
    title: 'Safe Bounds-Checked (Safe / Non-Vulnerable)',
    cwe: 'Non-Vulnerable',
    description: 'Safe memory copy with explicit bounds limiting and zero-byte termination check.',
    code: `/* Secure function: Bounds-checked string formatting */
#include <stdio.h>
#include <string.h>

int safe_format_log(char *destination, size_t dest_size, const char *msg) {
    if (destination == NULL || msg == NULL || dest_size == 0) {
        return -1;
    }
    
    // Bounds-checked formatting preventing buffer overflow
    int written = snprintf(destination, dest_size, "[AUDIT] %s", msg);
    if (written < 0 || (size_t)written >= dest_size) {
        destination[dest_size - 1] = '\\0';
        return -1;
    }
    
    return 0;
}
`,
  },
  ai_generated_socket: {
    title: 'AI-Generated Socket Handler (LLMVul Style)',
    cwe: 'CWE-119',
    description: 'LLM-generated code snippet that reads network bytes with subtle size mismatch.',
    code: `/* AI-Assisted Code: Network Socket Payload Handler */
#include <sys/socket.h>
#include <unistd.h>
#include <string.h>

int handle_network_request(int client_fd) {
    char packet_cache[64];
    int bytes_received = recv(client_fd, packet_cache, 128, 0);
    
    if (bytes_received > 0) {
        // Buffer is only 64 bytes, but up to 128 bytes read
        packet_cache[bytes_received] = '\\0';
        return 1;
    }
    return 0;
}
`,
  },
};

export const ScannerTab: React.FC<ScannerTabProps> = ({ models, defaultModelId }) => {
  const [selectedModel, setSelectedModel] = useState<string>(defaultModelId || 'tfidf_logistic_regression');
  const [code, setCode] = useState<string>(PRESET_TEMPLATES.buffer_overflow.code);
  const [selectedTemplateKey, setSelectedTemplateKey] = useState<string>('buffer_overflow');
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const handleTemplateChange = (key: string) => {
    setSelectedTemplateKey(key);
    if (PRESET_TEMPLATES[key]) {
      setCode(PRESET_TEMPLATES[key].code);
      setScanResult(null);
      setErrorMessage(null);
    }
  };

  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Ignore clipboard write failures
    }
  };

  const handleScan = async () => {
    if (!code || !code.trim()) {
      setErrorMessage('Please provide source code to analyze.');
      return;
    }

    setIsScanning(true);
    setErrorMessage(null);

    try {
      const response = await ApiService.scanCode({
        code,
        model_id: selectedModel,
        language: 'c',
      });
      setScanResult(response);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error occurred while scanning code.');
      setScanResult(null);
    } finally {
      setIsScanning(false);
    }
  };

  const currentModelMeta = models.find((m) => m.id === selectedModel);

  return (
    <div className="space-y-6">
      {/* Top Banner / Template Selector */}
      <div className="glass-panel p-4 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-sky-400" />
          <span className="text-sm font-semibold text-slate-200">Preset Vulnerability Templates:</span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {Object.entries(PRESET_TEMPLATES).map(([key, template]) => (
            <button
              key={key}
              onClick={() => handleTemplateChange(key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                selectedTemplateKey === key
                  ? 'bg-sky-500/20 text-sky-300 border border-sky-400/50 shadow-sm'
                  : 'bg-slate-800/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-700/60'
              }`}
            >
              {template.title.split('(')[0].trim()}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Editor on Left, Results on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Monaco Editor (7 cols on lg) */}
        <div className="lg:col-span-7 flex flex-col space-y-3">
          <div className="glass-panel rounded-2xl overflow-hidden border border-slate-800 flex flex-col h-[580px]">
            {/* Editor Toolbar */}
            <div className="bg-slate-900/90 px-4 py-2.5 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-800 text-sky-400 border border-slate-700">
                  C / C++
                </span>
                <span className="text-xs text-slate-400">
                  {code.split('\n').length} lines &bull; {code.length} chars
                </span>
              </div>

              {/* Model Selection Dropdown */}
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-400 hidden sm:inline">Model:</label>
                <div className="relative">
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="bg-slate-800 text-xs text-slate-200 pl-3 pr-8 py-1.5 rounded-lg border border-slate-700 focus:outline-none focus:border-sky-500 appearance-none font-medium cursor-pointer"
                  >
                    {models.map((m) => (
                      <option key={m.id} value={m.id} disabled={m.status !== 'ready'}>
                        {m.name} {m.status === 'ready' ? '✓' : '(Missing Weights)'}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-2 pointer-events-none" />
                </div>

                <button
                  onClick={handleCopyCode}
                  title="Copy code to clipboard"
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>

                <button
                  onClick={() => setCode('')}
                  title="Clear editor"
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Monaco Editor Container */}
            <div className="flex-1 w-full bg-[#1e1e1e]">
              <Editor
                height="100%"
                defaultLanguage="c"
                theme="vs-dark"
                value={code}
                onChange={(value) => setCode(value || '')}
                options={{
                  fontSize: 13,
                  fontFamily: '"Fira Code", monospace',
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  lineNumbers: 'on',
                  automaticLayout: true,
                  padding: { top: 12, bottom: 12 },
                  renderLineHighlight: 'all',
                  tabSize: 4,
                }}
              />
            </div>

            {/* Editor Action Bar */}
            <div className="bg-slate-900/90 px-4 py-3 border-t border-slate-800 flex items-center justify-between">
              <span className="text-xs text-slate-400">
                Active Model:{' '}
                <strong className="text-slate-200">
                  {currentModelMeta?.name || selectedModel}
                </strong>
              </span>

              <button
                onClick={handleScan}
                disabled={isScanning}
                className={`flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-semibold transition-all shadow-lg ${
                  isScanning
                    ? 'bg-slate-800 text-slate-400 cursor-not-allowed'
                    : 'bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white shadow-sky-500/25'
                }`}
              >
                {isScanning ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    <span>Analyzing AST & Tokens...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-white" />
                    <span>Scan Code for Vulnerabilities</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Scan Results Panel (5 cols on lg) */}
        <div className="lg:col-span-5 flex flex-col space-y-4">
          {errorMessage && (
            <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <strong className="font-semibold block">Scan Error:</strong>
                <span>{errorMessage}</span>
              </div>
            </div>
          )}

          {scanResult ? (
            <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-5 animate-in fade-in duration-300">
              {/* Threat Status Banner */}
              <div
                className={`p-5 rounded-xl border flex items-center justify-between ${
                  scanResult.is_vulnerable
                    ? 'bg-gradient-to-r from-rose-950/70 to-red-900/50 border-rose-600/60 shadow-glow-vuln'
                    : 'bg-gradient-to-r from-emerald-950/70 to-teal-900/50 border-emerald-500/60 shadow-glow-safe'
                }`}
              >
                <div className="flex items-center gap-3.5">
                  <div
                    className={`p-3 rounded-xl ${
                      scanResult.is_vulnerable
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                        : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                    }`}
                  >
                    {scanResult.is_vulnerable ? (
                      <ShieldAlert className="w-7 h-7" />
                    ) : (
                      <ShieldCheck className="w-7 h-7" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white tracking-wide">
                      {scanResult.is_vulnerable ? 'VULNERABLE (Class 1)' : 'SAFE / NON-VULNERABLE (Class 0)'}
                    </h3>
                    <p className="text-xs text-slate-300">
                      {scanResult.is_vulnerable
                        ? 'High probability of exploitable security vulnerability detected.'
                        : 'No classical buffer or memory vulnerability detected.'}
                    </p>
                  </div>
                </div>

                <div className="text-right hidden sm:block">
                  <span className="text-xs text-slate-400 uppercase tracking-wider block">Decision</span>
                  <span
                    className={`text-xl font-black ${
                      scanResult.is_vulnerable ? 'text-rose-400 glow-text-vuln' : 'text-emerald-400 glow-text-safe'
                    }`}
                  >
                    {(scanResult.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Class Probability Distribution Gauge */}
              <div className="space-y-2 bg-slate-900/80 p-4 rounded-xl border border-slate-800">
                <div className="flex justify-between items-center text-xs font-semibold">
                  <span className="text-emerald-400 flex items-center gap-1.5">
                    Safe (0): {(scanResult.probabilities.safe * 100).toFixed(2)}%
                  </span>
                  <span className="text-rose-400 flex items-center gap-1.5">
                    Vulnerable (1): {(scanResult.probabilities.vulnerable * 100).toFixed(2)}%
                  </span>
                </div>

                {/* Dual Progress Bar */}
                <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden flex">
                  <div
                    className="bg-emerald-500 h-full transition-all duration-500"
                    style={{ width: `${scanResult.probabilities.safe * 100}%` }}
                    title={`Safe Probability: ${(scanResult.probabilities.safe * 100).toFixed(1)}%`}
                  />
                  <div
                    className="bg-rose-500 h-full transition-all duration-500"
                    style={{ width: `${scanResult.probabilities.vulnerable * 100}%` }}
                    title={`Vulnerable Probability: ${(scanResult.probabilities.vulnerable * 100).toFixed(1)}%`}
                  />
                </div>
              </div>

              {/* Metadata Badges (Latency, Model Type, Dataset) */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-2.5">
                  <Clock className="w-4 h-4 text-sky-400 shrink-0" />
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Inference Latency</span>
                    <span className="text-sm font-semibold text-slate-200">
                      {scanResult.inference_time_ms.toFixed(2)} ms
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-2.5">
                  <Cpu className="w-4 h-4 text-purple-400 shrink-0" />
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Model Architecture</span>
                    <span className="text-sm font-semibold text-slate-200 capitalize">
                      {scanResult.model_type}
                    </span>
                  </div>
                </div>
              </div>

              {/* Remediation & Insights */}
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-2">
                <strong className="text-slate-200 flex items-center gap-1.5 font-semibold">
                  <Info className="w-3.5 h-3.5 text-sky-400" />
                  <span>Security Recommendations:</span>
                </strong>
                <ul className="list-disc pl-4 space-y-1 text-slate-400">
                  {scanResult.is_vulnerable ? (
                    <>
                      <li>Replace unbounded memory operations (<code className="text-rose-300">strcpy</code>, <code className="text-rose-300">gets</code>, <code className="text-rose-300">sprintf</code>) with bounds-checked variants (<code className="text-sky-300">snprintf</code>, <code className="text-sky-300">strncpy</code>).</li>
                      <li>Validate input buffer length against destination array bounds prior to writing.</li>
                      <li>Ensure single-ownership memory semantics to eliminate double-free conditions.</li>
                    </>
                  ) : (
                    <>
                      <li>No classic vulnerability patterns detected by this model's vocabulary.</li>
                      <li>Always pair ML classification with formal static analysis (Clang Static Analyzer, AddressSanitizer).</li>
                    </>
                  )}
                </ul>
              </div>

              {/* Research Disclaimer */}
              <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-200/90 leading-relaxed">
                <strong>ML Research Disclaimer:</strong> {scanResult.disclaimer}
              </div>
            </div>
          ) : (
            /* Empty State / Standby Card */
            <div className="glass-panel p-8 rounded-2xl border border-slate-800 flex flex-col items-center justify-center text-center h-[580px] space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-slate-800/80 border border-slate-700 flex items-center justify-center text-slate-400 shadow-inner">
                <Play className="w-8 h-8 ml-1 text-sky-400" />
              </div>
              <div className="max-w-xs space-y-1">
                <h4 className="text-base font-semibold text-white">Scanner Standby</h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Select a template or paste C/C++ source code into the editor, then click{' '}
                  <span className="text-sky-400 font-medium">"Scan Code"</span> to evaluate security vulnerabilities.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
