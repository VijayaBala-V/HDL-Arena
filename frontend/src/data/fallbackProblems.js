/**
 * Comprehensive Fallback Question Catalog for HDL Arena
 * Mirrors backend questions_registry for offline & dev mode resilience.
 */

export const FALLBACK_PROBLEMS = [
  // 1. Beginner - Verilog - Coding
  {
    id: "counter4",
    title: "4-bit Synchronous Binary Counter",
    topic: "Counters and Timers",
    category: "Counters and Timers",
    difficulty: "Beginner",
    language: "verilog",
    type: "coding",
    tags: ["Sequential", "Registers", "Rollover", "Counters"],
    description: (
      "Design a 4-bit synchronous binary up-counter with active-high synchronous reset.\n\n" +
      "Functional Specifications:\n" +
      "• When 'rst' is high on the rising edge of 'clk', 'count' must reset immediately to 4'b0000.\n" +
      "• When 'rst' is low, 'count' increments by 1 on every rising clock edge.\n" +
      "• After reaching 4'd15 (4'b1111), the next increment must wrap around to 4'd0."
    ),
    requirements: [
      "Synchronous active-high reset takes priority over counting.",
      "Counter operates on posedge of clk.",
      "Smooth wrap-around from 15 to 0."
    ],
    constraints: ["Clock period: 10ns (100 MHz)", "Output latency: 1 clock cycle"],
    module_name: "counter4",
    ports: [
      { name: "clk", direction: "input", width: "1-bit", desc: "Master clock" },
      { name: "rst", direction: "input", width: "1-bit", desc: "Synchronous active-high reset" },
      { name: "count", direction: "output", width: "4-bit [3:0]", desc: "4-bit count value" }
    ],
    interface: "module counter4(\n    input  wire       clk,\n    input  wire       rst,\n    output reg  [3:0] count\n);",
    starter_files: {
      "counter4.v": "module counter4(\n    input  wire       clk,\n    input  wire       rst,\n    output reg  [3:0] count\n);\n\n    // TODO: Implement synchronous active-high reset to 4'b0000.\n    // TODO: Implement 4-bit synchronous binary counter increment on posedge clk.\n    // TODO: Ensure smooth wrap-around from 15 (4'b1111) to 0 (4'b0000).\n\nendmodule\n"
    },
    progressive_hints: [
      {
        index: 0,
        cost: 0.0,
        title: "Conceptual Direction",
        text: "Synchronous reset means reset is sampled only inside the clocked always block on the rising edge of clk, not in the sensitivity list."
      },
      {
        index: 1,
        cost: 0.5,
        title: "Implementation Clue",
        text: "Inside always @(posedge clk), write an if (rst) check first. If rst is 1, assign count <= 4'b0000;, otherwise count <= count + 1'b1; using non-blocking assignments."
      },
      {
        index: 2,
        cost: 0.5,
        title: "Corner Case & Rollover Tip",
        text: "Because count is a 4-bit reg, adding 1 to 4'b1111 naturally wraps around to 4'b0000 in binary arithmetic."
      }
    ]
  },

  // 2. Beginner - Verilog - Single Choice MCQ
  {
    id: "mcq_setup_hold",
    title: "Setup and Hold Time Violations",
    topic: "Timing Analysis & STA",
    category: "Timing Analysis & STA",
    difficulty: "Beginner",
    language: "verilog",
    type: "single_choice",
    tags: ["STA", "Timing", "Setup", "Hold", "Flip-Flops"],
    description: "In static timing analysis (STA), what is the fundamental difference between a setup time violation and a hold time violation regarding clock frequency?",
    options: [
      "A. Setup violations can be resolved by lowering the clock frequency, whereas hold violations cannot be fixed by changing the clock frequency.",
      "B. Hold violations can be resolved by lowering the clock frequency, whereas setup violations cannot.",
      "C. Both setup and hold violations can always be resolved simply by reducing the clock frequency.",
      "D. Neither setup nor hold violations depend on data path delay; both are solely determined by clock jitter."
    ],
    progressive_hints: [
      {
        index: 0,
        cost: 0.0,
        title: "Equation Clue",
        text: "Setup check: T_cq + T_data_max + T_setup <= T_period + T_skew. Hold check: T_cq + T_data_min >= T_hold + T_skew. Notice which one contains T_period!"
      }
    ]
  },

  // 3. Beginner - Verilog - Multiple Choice
  {
    id: "mcq_blocking_nonblocking",
    title: "Verilog Assignment Semantics & Guidelines",
    topic: "Verilog Syntax & Simulation",
    category: "Verilog Syntax & Simulation",
    difficulty: "Beginner",
    language: "verilog",
    type: "multiple_choice",
    tags: ["Verilog", "Non-blocking", "Blocking", "Race Conditions"],
    description: "According to standard IEEE Verilog coding guidelines (Cliff Cummings methodology), which of the following statements are TRUE? (Select all that apply)",
    options: [
      "A. Use non-blocking assignments (<=) when modeling sequential clocked always blocks.",
      "B. Use blocking assignments (=) when modeling combinational always blocks.",
      "C. Mixing blocking and non-blocking assignments to the same variable in the same always block is recommended for faster simulation.",
      "D. Never make assignments to the same variable from more than one always block."
    ]
  },

  // 4. Beginner - Python - Coding
  {
    id: "py_parity_check",
    title: "Bitwise Parity and Hamming Weight",
    topic: "Python Fundamentals & Bit Manipulation",
    category: "Software for Hardware Engineers",
    difficulty: "Beginner",
    language: "python",
    type: "coding",
    tags: ["Python", "Bitwise", "Hamming Weight", "Parity"],
    description: "Write a Python function `compute_parity(n: int) -> dict` returning {'ones_count': ..., 'odd_parity': ...} for integer n.",
    starter_files: {
      "solution.py": "def compute_parity(n: int) -> dict:\n    # TODO: Calculate number of set bits and odd parity flag (1 if odd, 0 if even)\n    ones = n.bit_count()\n    return {'ones_count': ones, 'odd_parity': ones % 2}\n"
    }
  },

  // 5. Beginner - C - Coding
  {
    id: "c_bit_reverse",
    title: "32-bit Integer Bit Reversal",
    topic: "Embedded C & Bit Manipulation",
    category: "Software for Hardware Engineers",
    difficulty: "Beginner",
    language: "c",
    type: "coding",
    tags: ["C", "Bit Manipulation", "Embedded", "Bit Reversal"],
    description: "Write a C function `uint32_t reverse_bits(uint32_t n)` that reverses the binary bits of a 32-bit unsigned integer.",
    starter_files: {
      "solution.c": "#include <stdint.h>\n\nuint32_t reverse_bits(uint32_t n) {\n    // TODO: Reverse all 32 bits\n    uint32_t rev = 0;\n    for (int i = 0; i < 32; i++) {\n        rev = (rev << 1) | (n & 1);\n        n >>= 1;\n    }\n    return rev;\n}\n"
    }
  },

  // 6. Intermediate - Verilog - ALU
  {
    id: "alu_4bit",
    title: "4-bit Arithmetic Logic Unit (ALU)",
    topic: "Arithmetic Units and ALUs",
    category: "Arithmetic Units and ALUs",
    difficulty: "Intermediate",
    language: "verilog",
    type: "coding",
    tags: ["Arithmetic", "ALU", "Datapath"],
    description: "Design a 4-bit Arithmetic Logic Unit supporting 6 operations selected by 3-bit opcode (ADD, SUB, AND, OR, XOR, SLL) with carry and zero flag detection.",
    module_name: "alu_4bit",
    starter_files: {
      "alu_4bit.v": "module alu_4bit(\n    input  wire [3:0] a,\n    input  wire [3:0] b,\n    input  wire [2:0] opcode,\n    output reg  [3:0] out,\n    output reg        carry,\n    output wire       zero\n);\n\n    // TODO: Implement 4-bit ALU\n\nendmodule\n"
    }
  },

  // 7. Intermediate - C++ - Coding
  {
    id: "cpp_ring_buffer",
    title: "C++ Circular Ring Buffer for Verification",
    topic: "C++ Data Structures & Verification",
    category: "Software for Hardware Engineers",
    difficulty: "Intermediate",
    language: "cpp",
    type: "coding",
    tags: ["C++", "Ring Buffer", "Circular Queue", "Verification"],
    description: "Implement a fixed-capacity circular ring buffer in C++: RingBuffer<int, 4> with push, pop, is_full, is_empty, size.",
    starter_files: {
      "ring_buffer.hpp": "#pragma once\n#include <cstddef>\n\ntemplate<typename T, size_t Capacity>\nclass RingBuffer {\nprivate:\n    T buffer_[Capacity];\n    size_t head_ = 0;\n    size_t tail_ = 0;\n    size_t count_ = 0;\npublic:\n    bool push(const T& val) {\n        if (is_full()) return false;\n        buffer_[tail_] = val;\n        tail_ = (tail_ + 1) % Capacity;\n        count_++;\n        return true;\n    }\n    bool pop(T& out) {\n        if (is_empty()) return false;\n        out = buffer_[head_];\n        head_ = (head_ + 1) % Capacity;\n        count_--;\n        return true;\n    }\n    bool is_full() const { return count_ == Capacity; }\n    bool is_empty() const { return count_ == 0; }\n    size_t size() const { return count_; }\n};\n"
    }
  },

  // 8. Advanced - Verilog - Multi-Module FIFO
  {
    id: "sync_fifo",
    title: "Synchronous FIFO (Multi-Module: Controller & Memory)",
    topic: "FIFO and Buffer Design",
    category: "FIFO and Buffer Design",
    difficulty: "Advanced",
    language: "verilog",
    type: "coding",
    tags: ["FIFO", "Multi-Module", "Memory", "Pointers", "Backpressure"],
    description: "Design a 4-entry deep, 8-bit wide Synchronous FIFO split across fifo_mem (4x8 RAM array) and sync_fifo (top controller with full/empty flags).",
    module_name: "sync_fifo",
    starter_files: {
      "sync_fifo.v": "module sync_fifo(\n    input  wire       clk,\n    input  wire       rst,\n    input  wire       wr_en,\n    input  wire [7:0] din,\n    input  wire       rd_en,\n    output wire [7:0] dout,\n    output wire       full,\n    output wire       empty,\n    output reg  [2:0] count\n);\n\n    // TODO: Multi-module FIFO implementation\n\nendmodule\n",
      "fifo_mem.v": "module fifo_mem(\n    input  wire       clk,\n    input  wire       wr_en,\n    input  wire [1:0] wr_addr,\n    input  wire [7:0] din,\n    input  wire [1:0] rd_addr,\n    output wire [7:0] dout\n);\n\n    reg [7:0] ram [0:3];\n    always @(posedge clk) begin\n        if (wr_en) ram[wr_addr] <= din;\n    end\n    assign dout = ram[rd_addr];\n\nendmodule\n"
    }
  },

  // 9. Advanced - SystemVerilog - Round Robin Arbiter
  {
    id: "sv_arbiter_rr",
    title: "4-way Round-Robin Arbiter",
    topic: "Arbitration & Scheduling",
    category: "Arbitration & Scheduling",
    difficulty: "Advanced",
    language: "systemverilog",
    type: "coding",
    tags: ["SystemVerilog", "Round-Robin", "Arbiter", "Fairness"],
    description: "Design a 4-channel Round-Robin Arbiter in SystemVerilog. Maintain dynamic priority rotation with one-hot grant.",
    module_name: "arbiter_rr4",
    starter_files: {
      "arbiter_rr4.sv": "module arbiter_rr4(\n    input  logic       clk,\n    input  logic       rst_n,\n    input  logic [3:0] req,\n    output logic [3:0] grant\n);\n\n    // TODO: Implement round-robin priority logic\n\nendmodule\n"
    }
  },

  // 10. Advanced - Interview Scenario
  {
    id: "interview_cdc_fifo",
    title: "Interview Scenario: Multi-Gigabit Asynchronous CDC FIFO Design",
    topic: "Clock Domain Crossing (CDC)",
    category: "Clock Domain Crossing (CDC)",
    difficulty: "Advanced",
    language: "verilog",
    type: "interview_scenario",
    tags: ["CDC", "Gray Code", "Async FIFO", "SystemVerilog", "Interview"],
    description: "Architect an Asynchronous CDC FIFO bridging a 133 MHz Write Domain and a 400 MHz Read Domain. Explain Gray codes, Full condition, Empty condition, and safe pessimism."
  },

  // 11. Expert - Verilog - APB Slave GPIO
  {
    id: "apb_slave_gpio",
    title: "AMBA APB 32-bit Slave GPIO Controller",
    topic: "Bus Protocols such as APB, AXI and AHB",
    category: "Bus Protocols such as APB, AXI and AHB",
    difficulty: "Expert",
    language: "verilog",
    type: "coding",
    tags: ["Bus Protocols", "APB", "AMBA", "Memory-Mapped IO"],
    description: "Design an AMBA Advanced Peripheral Bus (APB) 32-bit slave peripheral with Addr 0x00 (gpio_out R/W) and Addr 0x04 (gpio_in RO).",
    module_name: "apb_slave_gpio",
    starter_files: {
      "apb_slave_gpio.v": "module apb_slave_gpio(\n    input  wire        pclk,\n    input  wire        presetn,\n    input  wire        psel,\n    input  wire        penable,\n    input  wire        pwrite,\n    input  wire [31:0] paddr,\n    input  wire [31:0] pwdata,\n    output reg  [31:0] prdata,\n    output wire        pready,\n    input  wire [31:0] gpio_in,\n    output reg  [31:0] gpio_out\n);\n\n    // TODO: Implement APB Slave\n\nendmodule\n"
    }
  },

  // 12. Expert - Interview Scenario
  {
    id: "interview_axi_interconnect",
    title: "Interview Scenario: AXI4 Interconnect Deadlock & Out-of-Order Hazards",
    topic: "Bus Protocols such as APB, AXI and AHB",
    category: "Bus Protocols such as APB, AXI and AHB",
    difficulty: "Expert",
    language: "verilog",
    type: "interview_scenario",
    tags: ["AXI4", "Deadlock", "Out-of-Order", "Interconnect", "Interview"],
    description: "In an AXI4 interconnect supporting out-of-order responses with ID tagging: Explain circular dependency deadlocks, same-ID ordering rules, multi-master isolation, and head-of-line blocking mitigation."
  },

  // 13. Beginner - Verilog - Gray Code Converter (Imported: Weiyet/MakerCode_RTLChallenge, MIT)
  {
    id: "gray_code_conv",
    title: "4-bit Binary to Gray & Gray to Binary Converter",
    topic: "Digital Logic and Number Systems",
    category: "Combinational Logic",
    difficulty: "Beginner",
    language: "verilog",
    type: "coding",
    tags: ["Gray Code", "CDC", "XOR Logic", "Combinational"],
    description: "Design a 4-bit bidirectional Gray code converter. When mode is 0, convert binary to Gray code (gray[i] = bin[i] ^ bin[i+1]). When mode is 1, convert Gray code to binary.",
    module_name: "gray_code_conv",
    ports: [
      { name: "mode", direction: "input", width: "1-bit", desc: "0 = Bin to Gray, 1 = Gray to Bin" },
      { name: "in_data", direction: "input", width: "4-bit [3:0]", desc: "Input vector" },
      { name: "out_data", direction: "output", width: "4-bit [3:0]", desc: "Converted vector" }
    ],
    interface: "module gray_code_conv(\n    input  wire       mode,\n    input  wire [3:0] in_data,\n    output reg  [3:0] out_data\n);",
    starter_files: {
      "gray_code_conv.v": "module gray_code_conv(\n    input  wire       mode,\n    input  wire [3:0] in_data,\n    output reg  [3:0] out_data\n);\n\n    // TODO: When mode == 0, convert in_data (binary) to out_data (Gray code)\n    // TODO: When mode == 1, convert in_data (Gray code) to out_data (binary)\n\nendmodule\n"
    }
  },

  // 14. Intermediate - Verilog - LFSR (Imported: Weiyet/MakerCode_RTLChallenge, MIT)
  {
    id: "lfsr_fibonacci8",
    title: "8-bit Maximal-Length Fibonacci LFSR",
    topic: "Sequential Circuits and LFSRs",
    category: "Sequential Logic",
    difficulty: "Intermediate",
    language: "verilog",
    type: "coding",
    tags: ["LFSR", "PRBS", "Taps", "Sequential"],
    description: "Design an 8-bit maximal-length Fibonacci LFSR with polynomial x^8 + x^6 + x^5 + x^4 + 1. Preset to 8'h01 on synchronous reset and shift left with XOR feedback at bit 0.",
    module_name: "lfsr_fibonacci8",
    ports: [
      { name: "clk", direction: "input", width: "1-bit", desc: "Clock" },
      { name: "rst", direction: "input", width: "1-bit", desc: "Synchronous active-high reset" },
      { name: "en", direction: "input", width: "1-bit", desc: "Enable shift" },
      { name: "lfsr_out", direction: "output", width: "8-bit [7:0]", desc: "8-bit PRBS state" }
    ],
    interface: "module lfsr_fibonacci8(\n    input  wire       clk,\n    input  wire       rst,\n    input  wire       en,\n    output reg  [7:0] lfsr_out\n);",
    starter_files: {
      "lfsr_fibonacci8.v": "module lfsr_fibonacci8(\n    input  wire       clk,\n    input  wire       rst,\n    input  wire       en,\n    output reg  [7:0] lfsr_out\n);\n\n    // TODO: Preset to 8'h01 on synchronous reset\n    // TODO: Feedback = out[7] ^ out[5] ^ out[4] ^ out[3]\n    // TODO: Shift left with feedback entering bit 0\n\nendmodule\n"
    }
  },

  // 15. Intermediate - Verilog - Debouncer Filter (Imported: Weiyet/MakerCode_RTLChallenge, MIT)
  {
    id: "debounce_filter",
    title: "Push-Button Switch Debouncer & Single-Pulse Generator",
    topic: "Sequential Circuits and Glitch Filtering",
    category: "Sequential Logic",
    difficulty: "Intermediate",
    language: "verilog",
    type: "coding",
    tags: ["Debounce", "Filter", "Single-Pulse", "Metastability"],
    description: "Design an active-high push-button debouncer and single-cycle pulse generator with a 2-stage synchronizer and 4-cycle debounce filter.",
    module_name: "debounce_filter",
    ports: [
      { name: "clk", direction: "input", width: "1-bit", desc: "Clock" },
      { name: "rst", direction: "input", width: "1-bit", desc: "Synchronous reset" },
      { name: "btn_in", direction: "input", width: "1-bit", desc: "Noisy mechanical button input" },
      { name: "btn_debounced", direction: "output", width: "1-bit", desc: "Steady debounced state" },
      { name: "btn_pulse", direction: "output", width: "1-bit", desc: "Single-cycle rising edge pulse" }
    ],
    interface: "module debounce_filter(\n    input  wire clk,\n    input  wire rst,\n    input  wire btn_in,\n    output reg  btn_debounced,\n    output wire btn_pulse\n);",
    starter_files: {
      "debounce_filter.v": "module debounce_filter(\n    input  wire clk,\n    input  wire rst,\n    input  wire btn_in,\n    output reg  btn_debounced,\n    output wire btn_pulse\n);\n\n    // TODO: Implement 2-stage synchronizer\n    // TODO: Implement 3-bit debounce saturation counter\n    // TODO: Emit 1-cycle pulse on rising edge of debounced button\n\nendmodule\n"
    }
  },

  // 16. Beginner - Verilog - Bitwise & Reduction Operators (Original Curriculum)
  {
    id: "bitwise_reduction8",
    title: "8-bit Bitwise & Reduction Operator Engine",
    topic: "Verilog fundamentals and operators",
    category: "Combinational Logic",
    difficulty: "Beginner",
    language: "verilog",
    type: "coding",
    tags: ["Operators", "Reduction", "Bitwise", "Combinational"],
    description: "Design an 8-bit combinational logic unit computing reduction AND (&a), reduction OR (|a), reduction XOR (^a), bitwise NOT (~a), and masked AND (a & mask).",
    module_name: "bitwise_reduction8",
    ports: [
      { name: "a", direction: "input", width: "8-bit [7:0]", desc: "Input vector" },
      { name: "mask", direction: "input", width: "8-bit [7:0]", desc: "Input mask" },
      { name: "red_and", direction: "output", width: "1-bit", desc: "&a" },
      { name: "red_or", direction: "output", width: "1-bit", desc: "|a" },
      { name: "red_xor", direction: "output", width: "1-bit", desc: "^a" },
      { name: "bitwise_inv", direction: "output", width: "8-bit [7:0]", desc: "~a" },
      { name: "masked_b", direction: "output", width: "8-bit [7:0]", desc: "a & mask" }
    ],
    interface: "module bitwise_reduction8(\n    input  wire [7:0] a,\n    input  wire [7:0] mask,\n    output wire       red_and,\n    output wire       red_or,\n    output wire       red_xor,\n    output wire [7:0] bitwise_inv,\n    output wire [7:0] masked_b\n);",
    starter_files: {
      "bitwise_reduction8.v": "module bitwise_reduction8(\n    input  wire [7:0] a,\n    input  wire [7:0] mask,\n    output wire       red_and,\n    output wire       red_or,\n    output wire       red_xor,\n    output wire [7:0] bitwise_inv,\n    output wire [7:0] masked_b\n);\n\n    // TODO: Implement reduction & bitwise assignments\n\nendmodule\n"
    }
  },

  // 17. Beginner - Verilog - 2-to-4 Decoder (Original Curriculum)
  {
    id: "decoder_2to4_en",
    title: "2-to-4 Binary Decoder with Active-High Enable",
    topic: "Muxes, decoders, encoders, combinational logic",
    category: "Combinational Logic",
    difficulty: "Beginner",
    language: "verilog",
    type: "coding",
    tags: ["Decoder", "Address Decoding", "One-Hot", "Combinational"],
    description: "Design a 2-to-4 binary line decoder with an active-high enable input 'en'. When en is 1, output 4-bit one-hot vector (4'b0001 << sel); when en is 0, output 4'b0000.",
    module_name: "decoder_2to4_en",
    ports: [
      { name: "en", direction: "input", width: "1-bit", desc: "Enable" },
      { name: "sel", direction: "input", width: "2-bit [1:0]", desc: "Address index" },
      { name: "y", direction: "output", width: "4-bit [3:0]", desc: "One-hot decoded output" }
    ],
    interface: "module decoder_2to4_en(\n    input  wire       en,\n    input  wire [1:0] sel,\n    output wire [3:0] y\n);",
    starter_files: {
      "decoder_2to4_en.v": "module decoder_2to4_en(\n    input  wire       en,\n    input  wire [1:0] sel,\n    output wire [3:0] y\n);\n\n    // TODO: Implement 2-to-4 one-hot address decode with enable gating\n\nendmodule\n"
    }
  },

  // 18. Intermediate - Verilog - Carry-Lookahead Adder (Original Curriculum)
  {
    id: "cla_adder4",
    title: "4-bit Fast Carry-Lookahead Adder (CLA)",
    topic: "Adders, ALUs, arithmetic",
    category: "Arithmetic Units",
    difficulty: "Intermediate",
    language: "verilog",
    type: "coding",
    tags: ["CLA", "Carry-Lookahead", "Adder", "Fast Arithmetic"],
    description: "Design a 4-bit Carry-Lookahead Adder (CLA) with parallel carry generation terms G=A&B, P=A^B, avoiding sequential ripple delays.",
    module_name: "cla_adder4",
    ports: [
      { name: "a", direction: "input", width: "4-bit [3:0]", desc: "Operand A" },
      { name: "b", direction: "input", width: "4-bit [3:0]", desc: "Operand B" },
      { name: "cin", direction: "input", width: "1-bit", desc: "Carry-in" },
      { name: "sum", direction: "output", width: "4-bit [3:0]", desc: "Sum" },
      { name: "cout", direction: "output", width: "1-bit", desc: "Carry-out" }
    ],
    interface: "module cla_adder4(\n    input  wire [3:0] a,\n    input  wire [3:0] b,\n    input  wire       cin,\n    output wire [3:0] sum,\n    output wire       cout\n);",
    starter_files: {
      "cla_adder4.v": "module cla_adder4(\n    input  wire [3:0] a,\n    input  wire [3:0] b,\n    input  wire       cin,\n    output wire [3:0] sum,\n    output wire       cout\n);\n\n    // TODO: Compute generate (G) and propagate (P) terms\n    // TODO: Compute lookahead carry terms and sum\n\nendmodule\n"
    }
  },

  // 19. Intermediate - Verilog - Johnson Counter (Original Curriculum)
  {
    id: "johnson_counter4",
    title: "4-bit Johnson (Möbius) Ring Counter",
    topic: "Flip-flops, registers, counters",
    category: "Sequential Logic",
    difficulty: "Intermediate",
    language: "verilog",
    type: "coding",
    tags: ["Johnson Counter", "Ring Counter", "Glitchless", "Sequential"],
    description: "Design a 4-bit Johnson (twisted ring / Möbius) counter. Produces an 8-state sequence with single-bit transitions (0000->0001->0011->0111->1111->1110->1100->1000).",
    module_name: "johnson_counter4",
    ports: [
      { name: "clk", direction: "input", width: "1-bit", desc: "Clock" },
      { name: "rst", direction: "input", width: "1-bit", desc: "Synchronous reset to 0000" },
      { name: "en", direction: "input", width: "1-bit", desc: "Enable" },
      { name: "q", direction: "output", width: "4-bit [3:0]", desc: "Johnson state" }
    ],
    interface: "module johnson_counter4(\n    input  wire       clk,\n    input  wire       rst,\n    input  wire       en,\n    output reg  [3:0] q\n);",
    starter_files: {
      "johnson_counter4.v": "module johnson_counter4(\n    input  wire       clk,\n    input  wire       rst,\n    input  wire       en,\n    output reg  [3:0] q\n);\n\n    // TODO: Implement 4-bit Johnson counter with inverted feedback\n\nendmodule\n"
    }
  },

  // 20. Intermediate - Verilog - Vending Machine FSM (Original Curriculum)
  {
    id: "vending_machine_fsm",
    title: "Coin-Operated Beverage Vending Machine FSM",
    topic: "FSMs and control logic",
    category: "Finite State Machines",
    difficulty: "Intermediate",
    language: "verilog",
    type: "coding",
    tags: ["FSM", "Mealy/Moore", "Control Logic", "State Transitions"],
    description: "Design a beverage vending machine FSM for a 15c drink accepting 5c and 10c coins. Dispenses drink at 15c and returns 5c change on 20c.",
    module_name: "vending_machine_fsm",
    ports: [
      { name: "clk", direction: "input", width: "1-bit", desc: "Clock" },
      { name: "rst", direction: "input", width: "1-bit", desc: "Synchronous reset to 0c" },
      { name: "coin_5", direction: "input", width: "1-bit", desc: "5c coin input" },
      { name: "coin_10", direction: "input", width: "1-bit", desc: "10c coin input" },
      { name: "dispense", direction: "output", width: "1-bit", desc: "Dispense beverage" },
      { name: "change_5", direction: "output", width: "1-bit", desc: "5c change returned" }
    ],
    interface: "module vending_machine_fsm(\n    input  wire clk,\n    input  wire rst,\n    input  wire coin_5,\n    input  wire coin_10,\n    output reg  dispense,\n    output reg  change_5\n);",
    starter_files: {
      "vending_machine_fsm.v": "module vending_machine_fsm(\n    input  wire clk,\n    input  wire rst,\n    input  wire coin_5,\n    input  wire coin_10,\n    output reg  dispense,\n    output reg  change_5\n);\n\n    // TODO: Implement 3-state vending machine (S0, S5, S10)\n\nendmodule\n"
    }
  },

  // 21. Intermediate - Verilog - Single-Port SRAM (Original Curriculum)
  {
    id: "single_port_ram64x8",
    title: "Synchronous 64x8 Single-Port SRAM",
    topic: "FIFO, RAM, memory controllers",
    category: "Memory Controllers",
    difficulty: "Intermediate",
    language: "verilog",
    type: "coding",
    tags: ["SRAM", "RAM", "Memory", "Block RAM"],
    description: "Design a 64-word by 8-bit synchronous single-port SRAM with synchronous write and synchronous read-first output when chip enable 'ce' is active.",
    module_name: "single_port_ram64x8",
    ports: [
      { name: "clk", direction: "input", width: "1-bit", desc: "Clock" },
      { name: "ce", direction: "input", width: "1-bit", desc: "Chip enable" },
      { name: "we", direction: "input", width: "1-bit", desc: "Write enable" },
      { name: "addr", direction: "input", width: "6-bit [5:0]", desc: "Address 0-63" },
      { name: "din", direction: "input", width: "8-bit [7:0]", desc: "Data in" },
      { name: "dout", direction: "output", width: "8-bit [7:0]", desc: "Data out" }
    ],
    interface: "module single_port_ram64x8(\n    input  wire       clk,\n    input  wire       ce,\n    input  wire       we,\n    input  wire [5:0] addr,\n    input  wire [7:0] din,\n    output reg  [7:0] dout\n);",
    starter_files: {
      "single_port_ram64x8.v": "module single_port_ram64x8(\n    input  wire       clk,\n    input  wire       ce,\n    input  wire       we,\n    input  wire [5:0] addr,\n    input  wire [7:0] din,\n    output reg  [7:0] dout\n);\n\n    // TODO: Implement 64x8 BRAM array with synchronous write and read\n\nendmodule\n"
    }
  }
];
