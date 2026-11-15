"""
HDL Arena Comprehensive Hardware & Software Interview Question Registry
Scalable question bank supporting:
- 4 Difficulties: Beginner, Intermediate, Advanced, Expert
- 5 Languages: Verilog, SystemVerilog, C, C++, Python
- 8 Question Types:
    1. single_choice (MCQ with one correct choice)
    2. multiple_choice (Multiple select MCQ)
    3. conceptual (Short conceptual answer with rubric evaluation)
    4. predict_output (Predict simulation/program output)
    5. fill_in_code (Fill missing logic/syntax)
    6. coding (Full RTL module or software program)
    7. debugging (Find and fix functional/timing bug)
    8. interview_scenario (Open architectural scenario with multi-point rubric)
"""

QUESTIONS_REGISTRY = {
    # =========================================================================
    # 1. BEGINNER LEVEL
    # =========================================================================

    # Verilog - Coding (Existing 4-bit Counter, upgraded with full metadata & progressive hints)
    "counter4": {
        "id": "counter4",
        "title": "4-bit Synchronous Binary Counter",
        "topic": "Counters and Timers",
        "category": "Counters and Timers",
        "difficulty": "Beginner",
        "language": "verilog",
        "type": "coding",
        "tags": ["Sequential", "Registers", "Rollover", "Counters"],
        "description": (
            "Design a 4-bit synchronous binary up-counter with active-high synchronous reset.\n\n"
            "Functional Specifications:\n"
            "• When 'rst' is high on the rising edge of 'clk', 'count' must reset immediately to 4'b0000.\n"
            "• When 'rst' is low, 'count' increments by 1 on every rising clock edge.\n"
            "• After reaching 4'd15 (4'b1111), the next increment must wrap around to 4'd0."
        ),
        "requirements": [
            "Synchronous active-high reset takes priority over counting.",
            "Counter operates on posedge of clk.",
            "Smooth wrap-around from 15 to 0."
        ],
        "constraints": ["Clock period: 10ns (100 MHz)", "Output latency: 1 clock cycle"],
        "module_name": "counter4",
        "ports": [
            {"name": "clk", "direction": "input", "width": "1-bit", "desc": "Master clock"},
            {"name": "rst", "direction": "input", "width": "1-bit", "desc": "Synchronous active-high reset"},
            {"name": "count", "direction": "output", "width": "4-bit [3:0]", "desc": "4-bit count value"}
        ],
        "interface": (
            "module counter4(\n"
            "    input  wire       clk,\n"
            "    input  wire       rst,\n"
            "    output reg  [3:0] count\n"
            ");"
        ),
        "starter_files": {
            "counter4.v": (
                "module counter4(\n"
                "    input  wire       clk,\n"
                "    input  wire       rst,\n"
                "    output reg  [3:0] count\n"
                ");\n\n"
                "    // TODO: Implement synchronous active-high reset to 4'b0000.\n"
                "    // TODO: Implement 4-bit synchronous binary counter increment on posedge clk.\n"
                "    // TODO: Ensure smooth wrap-around from 15 (4'b1111) to 0 (4'b0000).\n\n"
                "endmodule\n"
            )
        },
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Conceptual Direction",
                "text": "Synchronous reset means reset is sampled only inside the clocked always block on the rising edge of clk, not in the sensitivity list."
            },
            {
                "index": 1,
                "cost": 0.5,
                "title": "Implementation Clue",
                "text": "Inside `always @(posedge clk)`, write an `if (rst)` check first. If rst is 1, assign `count <= 4'b0000;`, otherwise `count <= count + 1'b1;` using non-blocking assignments."
            },
            {
                "index": 2,
                "cost": 0.5,
                "title": "Corner Case & Rollover Tip",
                "text": "Because `count` is a 4-bit reg, adding 1 to 4'b1111 naturally wraps around to 4'b0000 in binary arithmetic without requiring an explicit if (count == 15) condition."
            }
        ],
        "hints": [
            "Synchronous reset means reset is evaluated inside always @(posedge clk).",
            "Use non-blocking assignments (<=) for all register updates.",
            "4-bit reg arithmetic rolls over automatically from 15 to 0."
        ],
        "explanation": "A synchronous counter samples both reset and enable on the active clock edge. Using non-blocking assignments ensures race-free simulation and clean hardware mapping to D flip-flops with synchronous clear.",
        "source_metadata": {
            "source": "HDL Arena Curated Library",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "original_repo": "https://github.com/hdl-arena/core-benchmarks",
            "attribution": "Standard synchronous RTL design benchmark."
        },
        "test_suite_version": "2.1.0",
        "reference_solution_policy": "Full canonical code available for 1.0 VJ Coin.",
        "testbench": r"""
`timescale 1ns/1ps
module tb;
    reg clk = 0;
    reg rst = 0;
    wire [3:0] count;

    counter4 dut (.clk(clk), .rst(rst), .count(count));
    always #5 clk = ~clk;

    task report_test(input [63:0] t_id, input [255:0] t_name, input passed, input [255:0] detail, input [31:0] t_time, input is_hidden);
        begin
            if (passed)
                $display("::TEST::%0s::%0s::PASSED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
            else
                $display("::TEST::%0s::%0s::FAILED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
        end
    endtask

    task log_cycle(input [31:0] t_val, input [127:0] in_str, input [63:0] exp_str, input [63:0] act_str, input match);
        begin
            $display("::CYCLE::time=%0dns::inputs=%0s::expected=%0s::actual=%0s::match=%0d::time_num=%0d",
                     t_val, in_str, exp_str, act_str, match, t_val);
        end
    endtask

    integer pass_count = 0;
    integer total_tests = 4;
    integer i;
    reg sample_mode;

    initial begin
        sample_mode = $test$plusargs("SAMPLE_ONLY");
        if (sample_mode) total_tests = 2;

        $dumpfile("wave.vcd");
        $dumpvars(0, tb);

        // TEST 1: Synchronous Reset Check (Sample)
        rst = 1; @(posedge clk); #1;
        log_cycle($time, "rst=1", "0", count, (count === 4'd0));
        if (count === 4'd0) begin
            report_test("tc_01", "Synchronous Reset Check", 1, "Count cleared to 0 on clk edge", $time, 0);
            pass_count = pass_count + 1;
        end else report_test("tc_01", "Synchronous Reset Check", 0, "Count did not reset to 0", $time, 0);

        // TEST 2: Consecutive Increments (Sample)
        rst = 0;
        begin : inc_loop
            reg ok; ok = 1;
            for (i = 1; i <= 5; i = i + 1) begin
                @(posedge clk); #1;
                log_cycle($time, "rst=0", i, count, (count === i[3:0]));
                if (count !== i[3:0]) ok = 0;
            end
            if (ok) begin
                report_test("tc_02", "Consecutive Increments (1..5)", 1, "All increments accurate", $time, 0);
                pass_count = pass_count + 1;
            end else report_test("tc_02", "Consecutive Increments (1..5)", 0, "Increment mismatch", $time, 0);
        end

        if (sample_mode) begin
            #15; $finish;
        end

        // TEST 3: Rollover from 15 to 0 (Hidden)
        begin : wrap_test
            reg ok; ok = 1;
            for (i = 6; i <= 15; i = i + 1) begin @(posedge clk); #1; end
            log_cycle($time, "count=15", "15", count, (count === 4'd15));
            if (count !== 4'd15) ok = 0;

            @(posedge clk); #1;
            log_cycle($time, "rollover to 0", "0", count, (count === 4'd0));
            if (count !== 4'd0) ok = 0;

            if (ok) begin
                report_test("tc_03", "Rollover 15 back to 0", 1, "Counter rolls over smoothly", $time, 1);
                pass_count = pass_count + 1;
            end else report_test("tc_03", "Rollover 15 back to 0", 0, "Failed wrap-around", $time, 1);
        end

        // TEST 4: Reset Priority Check (Hidden)
        rst = 1; @(posedge clk); #1;
        log_cycle($time, "rst=1 priority", "0", count, (count === 4'd0));
        if (count === 4'd0) begin
            report_test("tc_04", "Reset Priority Check", 1, "Reset dominates over counter increment", $time, 1);
            pass_count = pass_count + 1;
        end else report_test("tc_04", "Reset Priority Check", 0, "Reset did not override increment", $time, 1);

        #15; $finish;
    end
endmodule
""",
        "solution": {
            "cost": 1,
            "title": "Optimal 4-bit Synchronous Binary Counter",
            "overview": (
                "A synchronous 4-bit counter increments its internal register state on every rising edge of 'clk'. "
                "Because 'rst' is synchronous, the evaluation occurs inside the clocked always block under active-high priority. "
                "When the counter reaches 4'b1111 (15), the 4-bit register naturally rolls over to 4'b0000 on the subsequent increment."
            ),
            "timing_behavior": (
                "All state updates are synchronous to the posedge of clk. When rst is asserted, count transitions "
                "to 4'b0000 on the subsequent rising clock edge with exactly 1 cycle latency."
            ),
            "corner_cases": [
                "Wrap-around transition: 4'b1111 to 4'b0000 without glitching.",
                "Reset priority: Active synchronous reset assertion dominates over counting increment logic.",
                "Zero hold: While rst remains asserted across multiple clock cycles, count stays 4'b0000."
            ],
            "synthesis_notes": [
                "Infers 4 positive-edge D flip-flops with synchronous clear and clock enable.",
                "Non-blocking assignments (<=) must be used exclusively to guarantee deterministic cycle-accurate RTL simulation without race conditions."
            ],
            "canonical_code": {
                "counter4.v": (
                    "module counter4(\n"
                    "    input  wire       clk,\n"
                    "    input  wire       rst,\n"
                    "    output reg  [3:0] count\n"
                    ");\n\n"
                    "    always @(posedge clk) begin\n"
                    "        if (rst) begin\n"
                    "            count <= 4'b0000;\n"
                    "        end else begin\n"
                    "            count <= count + 1'b1;\n"
                    "        end\n"
                    "    end\n\n"
                    "endmodule\n"
                )
            }
        }
    },

    # Verilog - Coding (Existing 4-to-1 MUX)
    "mux4": {
        "id": "mux4",
        "title": "4-to-1 Multiplexer",
        "topic": "Combinational Logic",
        "category": "Combinational Logic",
        "difficulty": "Beginner",
        "language": "verilog",
        "type": "coding",
        "tags": ["Combinational", "MUX", "Datapath"],
        "description": (
            "Design a 4-to-1 multiplexer. Given a 4-bit data bus 'in' and a 2-bit select signal 'sel', "
            "steer the selected input bit to the single-bit output 'out':\n"
            "• sel = 2'b00 -> out = in[0]\n"
            "• sel = 2'b01 -> out = in[1]\n"
            "• sel = 2'b10 -> out = in[2]\n"
            "• sel = 2'b11 -> out = in[3]"
        ),
        "requirements": [
            "Pure combinational logic without clock.",
            "Zero registered delay."
        ],
        "constraints": ["Propagation delay should be minimal."],
        "module_name": "mux4",
        "ports": [
            {"name": "in", "direction": "input", "width": "4-bit [3:0]", "desc": "4 input channels"},
            {"name": "sel", "direction": "input", "width": "2-bit [1:0]", "desc": "Channel select line"},
            {"name": "out", "direction": "output", "width": "1-bit", "desc": "Selected output bit"}
        ],
        "interface": (
            "module mux4(\n"
            "    input  wire [3:0] in,\n"
            "    input  wire [1:0] sel,\n"
            "    output wire       out\n"
            ");"
        ),
        "starter_files": {
            "mux4.v": (
                "module mux4(\n"
                "    input  wire [3:0] in,\n"
                "    input  wire [1:0] sel,\n"
                "    output wire       out\n"
                ");\n\n"
                "    // TODO: Implement 4-to-1 multiplexer combinational datapath.\n"
                "    // Steer the selected channel in[sel] to output 'out'.\n\n"
                "endmodule\n"
            )
        },
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Conceptual Direction",
                "text": "In Verilog, array bit selection allows indexing a vector dynamically using another signal as index: `in[sel]`."
            },
            {
                "index": 1,
                "cost": 0.5,
                "title": "Implementation Clue",
                "text": "You can solve this with a single continuous assignment: `assign out = in[sel];`."
            }
        ],
        "hints": [
            "Direct bit indexing `in[sel]` synthesizes into an optimal multiplexer tree.",
            "No clock is needed; keep output purely combinational."
        ],
        "explanation": "Dynamic part selection `assign out = in[sel];` is the most concise continuous assignment in Verilog and maps directly to LUT multiplexers.",
        "source_metadata": {
            "source": "HDL Arena Curated Library",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Standard combinational logic benchmark."
        },
        "test_suite_version": "1.0.0",
        "reference_solution_policy": "Full canonical code available for 1.0 VJ Coin.",
        "testbench": r"""
`timescale 1ns/1ps
module tb;
    reg [3:0] in;
    reg [1:0] sel;
    wire out;

    mux4 dut (.in(in), .sel(sel), .out(out));

    task report_test(input [63:0] t_id, input [255:0] t_name, input passed, input [255:0] detail, input [31:0] t_time, input is_hidden);
        begin
            if (passed)
                $display("::TEST::%0s::%0s::PASSED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
            else
                $display("::TEST::%0s::%0s::FAILED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
        end
    endtask

    task log_cycle(input [31:0] t_val, input [127:0] in_str, input [63:0] exp_str, input [63:0] act_str, input match);
        begin
            $display("::CYCLE::time=%0dns::inputs=%0s::expected=%0s::actual=%0s::match=%0d::time_num=%0d",
                     t_val, in_str, exp_str, act_str, match, t_val);
        end
    endtask

    reg sample_mode;

    initial begin
        sample_mode = $test$plusargs("SAMPLE_ONLY");
        $dumpfile("wave.vcd");
        $dumpvars(0, tb);

        // TEST 1: Channel 0 (Sample)
        in = 4'b1011; sel = 2'b00; #10;
        log_cycle($time, "in=4'b1011,sel=00", "1", out, (out === 1'b1));
        if (out === 1'b1)
            report_test("tc_01", "Select Channel 0 (sel=00)", 1, "Channel 0 correctly steered", $time, 0);
        else report_test("tc_01", "Select Channel 0 (sel=00)", 0, "Channel 0 error", $time, 0);

        // TEST 2: Channel 1 (Sample)
        in = 4'b1010; sel = 2'b01; #10;
        log_cycle($time, "in=4'b1010,sel=01", "1", out, (out === 1'b1));
        if (out === 1'b1)
            report_test("tc_02", "Select Channel 1 (sel=01)", 1, "Channel 1 correctly steered", $time, 0);
        else report_test("tc_02", "Select Channel 1 (sel=01)", 0, "Channel 1 error", $time, 0);

        if (sample_mode) begin
            #10; $finish;
        end

        // TEST 3: Channel 2 (Hidden)
        in = 4'b1100; sel = 2'b10; #10;
        log_cycle($time, "in=4'b1100,sel=10", "1", out, (out === 1'b1));
        if (out === 1'b1)
            report_test("tc_03", "Select Channel 2 (sel=10)", 1, "Channel 2 correctly steered", $time, 1);
        else report_test("tc_03", "Select Channel 2 (sel=10)", 0, "Channel 2 error", $time, 1);

        // TEST 4: Channel 3 (Hidden)
        in = 4'b1000; sel = 2'b11; #10;
        log_cycle($time, "in=4'b1000,sel=11", "1", out, (out === 1'b1));
        if (out === 1'b1)
            report_test("tc_04", "Select Channel 3 (sel=11)", 1, "Channel 3 correctly steered", $time, 1);
        else report_test("tc_04", "Select Channel 3 (sel=11)", 0, "Channel 3 error", $time, 1);

        #10; $finish;
    end
endmodule
""",
        "solution": {
            "cost": 1,
            "title": "Direct Bit-Select 4-to-1 Multiplexer",
            "overview": "A 4-to-1 multiplexer selects one of 4 input lines using a 2-bit select code.",
            "canonical_code": {
                "mux4.v": (
                    "module mux4(\n"
                    "    input  wire [3:0] in,\n"
                    "    input  wire [1:0] sel,\n"
                    "    output wire       out\n"
                    ");\n\n"
                    "    assign out = in[sel];\n\n"
                    "endmodule\n"
                )
            }
        }
    },

    # Digital Logic - Single Choice MCQ
    "mcq_setup_hold": {
        "id": "mcq_setup_hold",
        "title": "Setup and Hold Time Violations",
        "topic": "Timing Analysis & STA",
        "category": "Timing Analysis & STA",
        "difficulty": "Beginner",
        "language": "verilog",
        "type": "single_choice",
        "tags": ["STA", "Timing", "Setup", "Hold", "Flip-Flops"],
        "description": (
            "In static timing analysis (STA), what is the fundamental difference between a setup time violation "
            "and a hold time violation regarding clock frequency?"
        ),
        "options": [
            "A. Setup violations can be resolved by lowering the clock frequency, whereas hold violations cannot be fixed by changing the clock frequency.",
            "B. Hold violations can be resolved by lowering the clock frequency, whereas setup violations cannot.",
            "C. Both setup and hold violations can always be resolved simply by reducing the clock frequency.",
            "D. Neither setup nor hold violations depend on data path delay; both are solely determined by clock jitter."
        ],
        "correct_option": "A",
        "option_explanations": {
            "A": "Correct! Setup time check requires: T_clk >= T_cq + T_comb + T_setup - T_skew. Increasing clock period T_clk (lowering frequency) provides more time for data to arrive. In contrast, hold check: T_cq + T_comb >= T_hold + T_skew is completely independent of the clock period T_clk!",
            "B": "Incorrect. Hold check inequality does not contain T_clk. Slowing the clock has zero effect on hold time.",
            "C": "Incorrect. Hold violations occur when data arrives too fast relative to the clock edge, which clock period changes cannot fix.",
            "D": "Incorrect. Data path delay T_comb directly determines both setup and hold margins."
        },
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Conceptual Direction",
                "text": "Write down the equations for setup and hold checks. Look closely at which equation includes the clock period (T_clk)."
            },
            {
                "index": 1,
                "cost": 0.5,
                "title": "Equation Clue",
                "text": "Setup check: T_cq + T_data_max + T_setup <= T_period + T_skew. Hold check: T_cq + T_data_min >= T_hold + T_skew."
            }
        ],
        "explanation": "Setup timing checks data arrival against the subsequent clock edge (one period later), so increasing the clock period relaxes setup constraints. Hold timing checks data against the same clock edge, making hold checks completely independent of clock frequency.",
        "source_metadata": {
            "source": "HDL Arena Digital Logic Bank",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Foundational VLSI Static Timing Analysis interview question."
        },
        "test_suite_version": "1.0.0",
        "reference_solution_policy": "Full explanation displayed upon answering."
    },

    # Verilog - Multiple Choice
    "mcq_blocking_nonblocking": {
        "id": "mcq_blocking_nonblocking",
        "title": "Verilog Assignment Semantics & Guidelines",
        "topic": "Verilog Syntax & Simulation",
        "category": "Verilog Syntax & Simulation",
        "difficulty": "Beginner",
        "language": "verilog",
        "type": "multiple_choice",
        "tags": ["Verilog", "Non-blocking", "Blocking", "Race Conditions"],
        "description": (
            "According to standard IEEE 1364 / IEEE 1800 Verilog coding guidelines (Cliff Cummings methodology), "
            "which of the following statements are TRUE? (Select all that apply)"
        ),
        "options": [
            "A. Use non-blocking assignments (<=) when modeling sequential clocked always blocks.",
            "B. Use blocking assignments (=) when modeling combinational always blocks.",
            "C. Mixing blocking and non-blocking assignments to the same variable in the same always block is recommended for faster simulation.",
            "D. Never make assignments to the same variable from more than one always block."
        ],
        "correct_options": ["A", "B", "D"],
        "option_explanations": {
            "A": "True! Non-blocking assignments schedule updates into the NBA region, preventing simulation race conditions across synchronous flip-flops.",
            "B": "True! Combinational logic updates immediately in the active region to evaluate immediate data flow.",
            "C": "False! Mixing blocking and non-blocking assignments to the same variable creates hazardous race conditions and synthesis-simulation mismatches.",
            "D": "True! Multiple always blocks driving the same variable infers multi-driver contention (or synthesis errors/X states)."
        },
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Golden Rules of Verilog",
                "text": "Remember Cummings' famous paper: 'Nonblocking Assignments in Verilog Synthesis, Coding Styles That Kill!'"
            }
        ],
        "explanation": "The golden rules are: (1) Clocked always blocks use <=. (2) Combinational always blocks use =. (3) Do not mix = and <= on the same variable. (4) Do not write to the same variable from multiple always blocks.",
        "source_metadata": {
            "source": "HDL Arena Curated Library",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Standard IEEE Verilog synthesis guidelines."
        },
        "test_suite_version": "1.0.0"
    },

    # Predict Output - Two's Complement & Radix
    "pred_num_systems": {
        "id": "pred_num_systems",
        "title": "Predict Output: Verilog Sign Extension & Slicing",
        "topic": "Number Systems & Radix",
        "category": "Number Systems & Radix",
        "difficulty": "Beginner",
        "language": "verilog",
        "type": "predict_output",
        "tags": ["Sign Extension", "Two's Complement", "Bit Slicing"],
        "description": (
            "Analyze the following Verilog code snippet:\n\n"
            "```verilog\n"
            "reg signed [3:0] a = 4'sb1100; // -4 in 4-bit two's complement\n"
            "reg signed [7:0] b;\n"
            "initial begin\n"
            "    b = a;\n"
            "    $display(\"%h\", b);\n"
            "end\n"
            "```\n\n"
            "What hexadecimal value does `$display(\"%h\", b)` print? (Enter the two hex characters, e.g. `fc` or `FC`)"
        ),
        "expected_output": "fc",
        "acceptable_outputs": ["fc", "FC", "8'hfc", "8'hFC", "0xfc", "0xFC"],
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Sign Extension Rule",
                "text": "Because 'a' is declared as 'signed' and expanded to 8 bits, Verilog replicates its MSB (sign bit) across the upper 4 bits."
            },
            {
                "index": 1,
                "cost": 0.5,
                "title": "Bit Calculation",
                "text": "a = 4'b1100 (MSB is 1). Upper 4 bits become 4'b1111. The 8-bit result is 8'b11111100. What is 1111_1100 in hex?"
            }
        ],
        "explanation": "Because `a` is declared `signed`, widening assignment from 4 bits to 8 bits sign-extends the MSB (1'b1), producing 8'b11111100, which in hexadecimal is 8'hFC.",
        "source_metadata": {
            "source": "HDL Arena Curated Library",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Verilog number representation challenge."
        },
        "test_suite_version": "1.0.0"
    },

    # Python - Coding
    "py_parity_check": {
        "id": "py_parity_check",
        "title": "Bitwise Parity and Hamming Weight",
        "topic": "Python Fundamentals & Bit Manipulation",
        "category": "Software for Hardware Engineers",
        "difficulty": "Beginner",
        "language": "python",
        "type": "coding",
        "entry_point": "compute_parity",
        "function_name": "compute_parity",
        "tags": ["Python", "Bitwise", "Hamming Weight", "Parity"],
        "description": (
            "Write a Python function `compute_parity(n: int) -> dict` that takes a non-negative integer `n` "
            "and returns a dictionary with two keys:\n"
            "• `'ones_count'`: The number of set bits (Hamming weight) in `n`.\n"
            "• `'odd_parity'`: `1` if `ones_count` is odd, `0` if `ones_count` is even.\n\n"
            "Example:\n"
            "`compute_parity(13)` -> 13 in binary is `1101` (3 ones) -> `{'ones_count': 3, 'odd_parity': 1}`\n"
            "`compute_parity(0)` -> `{'ones_count': 0, 'odd_parity': 0}`"
        ),
        "starter_files": {
            "solution.py": (
                "def compute_parity(n: int) -> dict:\n"
                "    # TODO: Calculate number of set bits (1s) in binary representation of n\n"
                "    # TODO: Return {'ones_count': ..., 'odd_parity': ...}\n"
                "    pass\n"
            )
        },
        "solution": {
            "cost": 1,
            "title": "Bitwise Parity & Hamming Weight in Python",
            "overview": "Hamming weight calculation via bit counting with odd parity evaluation.",
            "canonical_code": {
                "solution.py": (
                    "def compute_parity(n: int) -> dict:\n"
                    "    ones = bin(n).count('1')\n"
                    "    return {\n"
                    "        'ones_count': ones,\n"
                    "        'odd_parity': ones & 1\n"
                    "    }\n"
                )
            }
        },
        "test_harness": {
            "test_cases": [
                {"input": 0, "expected": {"ones_count": 0, "odd_parity": 0}, "hidden": False},
                {"input": 1, "expected": {"ones_count": 1, "odd_parity": 1}, "hidden": False},
                {"input": 13, "expected": {"ones_count": 3, "odd_parity": 1}, "hidden": False},
                {"input": 15, "expected": {"ones_count": 4, "odd_parity": 0}, "hidden": True},
                {"input": 1023, "expected": {"ones_count": 10, "odd_parity": 0}, "hidden": True},
                {"input": 0xDEADBEEF, "expected": {"ones_count": 24, "odd_parity": 0}, "hidden": True}
            ]
        },
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Python Builtin Clue",
                "text": "In Python, `bin(n).count('1')` or `n.bit_count()` counts set bits in O(1) / O(log N) time."
            },
            {
                "index": 1,
                "cost": 0.5,
                "title": "Parity Calculation",
                "text": "Odd parity is simply `ones_count % 2` (or `ones_count & 1`)."
            }
        ],
        "explanation": "`n.bit_count()` directly computes the Hamming weight of an integer. Parity is then obtained via bitwise modulo `ones_count & 1`.",
        "source_metadata": {
            "source": "HDL Arena Software Bank",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Standard hardware scripting interview question."
        },
        "test_suite_version": "1.0.0"
    },

    # C - Coding
    "c_bit_reverse": {
        "id": "c_bit_reverse",
        "title": "32-bit Integer Bit Reversal",
        "topic": "Embedded C & Bit Manipulation",
        "category": "Software for Hardware Engineers",
        "difficulty": "Beginner",
        "language": "c",
        "type": "coding",
        "entry_point": "reverse_bits",
        "function_name": "reverse_bits",
        "tags": ["C", "Bit Manipulation", "Embedded", "Bit Reversal"],
        "description": (
            "Write a C function `uint32_t reverse_bits(uint32_t n)` that reverses the binary bits of a 32-bit unsigned integer.\n\n"
            "Example:\n"
            "• `n = 0x00000001` (binary 00...01) -> returns `0x80000000` (binary 10...00)\n"
            "• `n = 0x80000000` -> returns `0x00000001`\n"
            "• `n = 0xAAAAAAAA` -> returns `0x55555555`"
        ),
        "starter_files": {
            "solution.c": (
                "#include <stdint.h>\n\n"
                "uint32_t reverse_bits(uint32_t n) {\n"
                "    // TODO: Reverse all 32 bits of n and return the result\n"
                "    return 0;\n"
                "}\n"
            )
        },
        "solution": {
            "cost": 1,
            "title": "32-bit Integer Bit Reversal in C",
            "overview": "Iterative bitwise reversal extracting LSB into left-shifted accumulator.",
            "canonical_code": {
                "solution.c": (
                    "#include <stdint.h>\n\n"
                    "uint32_t reverse_bits(uint32_t n) {\n"
                    "    uint32_t rev = 0;\n"
                    "    for (int i = 0; i < 32; i++) {\n"
                    "        rev = (rev << 1) | (n & 1);\n"
                    "        n >>= 1;\n"
                    "    }\n"
                    "    return rev;\n"
                    "}\n"
                )
            }
        },
        "test_harness": {
            "driver": r"""
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>

extern uint32_t reverse_bits(uint32_t n);

int main() {
    struct { uint32_t in; uint32_t exp; bool hidden; } tests[] = {
        {0x00000001, 0x80000000, false},
        {0x80000000, 0x00000001, false},
        {0xAAAAAAAA, 0x55555555, false},
        {0x12345678, 0x1E6A2C48, true},
        {0xFFFFFFFF, 0xFFFFFFFF, true},
        {0x00000000, 0x00000000, true}
    };
    int total = sizeof(tests)/sizeof(tests[0]);
    int passed = 0;
    for (int i = 0; i < total; i++) {
        uint32_t act = reverse_bits(tests[i].in);
        bool ok = (act == tests[i].exp);
        if (ok) passed++;
        printf("::TEST::tc_%02d::Bit Reverse 0x%08X::%s::act=0x%08X,exp=0x%08X::0ns::%d\n",
               i+1, tests[i].in, ok ? "PASSED" : "FAILED", act, tests[i].exp, tests[i].hidden ? 1 : 0);
    }
    return 0;
}
"""
        },
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Loop Approach",
                "text": "You can loop 32 times: shift result left by 1, OR in the LSB of n (`n & 1`), and shift n right by 1."
            },
            {
                "index": 1,
                "cost": 0.5,
                "title": "Divide-and-Conquer Clue",
                "text": "For O(log N) hardware efficiency, swap adjacent 16 bits, then 8 bits, 4 bits, 2 bits, and 1 bit using masks: `0x55555555`, `0x33333333`, `0x0F0F0F0F`, etc."
            }
        ],
        "explanation": "A 32-iteration loop shifts the accumulator left while pulling LSBs from the input. Alternatively, bitwise divide-and-conquer swap masks execute in 5 operations.",
        "source_metadata": {
            "source": "HDL Arena Software Bank",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Classic embedded firmware & DSP interview challenge."
        },
        "test_suite_version": "1.0.0"
    },

    # Conceptual - Metastability
    "concept_metastability": {
        "id": "concept_metastability",
        "title": "Metastability & Mean Time Between Failures (MTBF)",
        "topic": "Digital Logic Fundamentals",
        "category": "Clock Domain Crossing (CDC)",
        "difficulty": "Beginner",
        "language": "verilog",
        "type": "conceptual",
        "tags": ["Metastability", "MTBF", "Synchronizer", "CDC"],
        "description": (
            "Explain the physical cause of metastability in a D flip-flop, how a 2-stage flip-flop synchronizer "
            "mitigates it, and whether a 2-stage synchronizer can eliminate the probability of failure to absolute zero."
        ),
        "rubric_criteria": [
            {
                "criterion": "Cause of Metastability",
                "points": 30,
                "keywords": ["setup", "hold", "violation", "sampling", "intermediate voltage", "metastable state", "balance"],
                "desc": "Correctly states that violating setup or hold time causes internal bistable nodes to float between logic high and low."
            },
            {
                "criterion": "2-FF Synchronizer Role",
                "points": 40,
                "keywords": ["two", "flip flop", "settle", "exponential", "resolution time", "clock cycle", "mtbf"],
                "desc": "Explains that the first flip-flop captures the asynchronous input and provides a full clock period for metastable decay before the second flip-flop samples."
            },
            {
                "criterion": "Absolute Zero Impossibility",
                "points": 30,
                "keywords": ["exponential", "probability", "never zero", "cannot eliminate", "decay", "infinite"],
                "desc": "Explains that because resolution decay is exponential, probability approaches zero asymptotically but can NEVER reach absolute zero."
            }
        ],
        "model_answer": (
            "Metastability occurs when an input signal transitions inside the setup or hold window of a flip-flop. "
            "The internal feedback latches enter an unstable equilibrium between logic '0' and logic '1' voltages. "
            "A 2-stage flip-flop synchronizer grants the first flip-flop an entire clock cycle (resolution time) to settle "
            "exponentially to a stable valid logic level before the second flip-flop samples it. "
            "However, because the settling probability follows an exponential decay e^(-tr/tau), the failure rate can be made "
            "negligibly small (MTBF in thousands of years), but can NEVER be mathematically reduced to absolute zero."
        ),
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Conceptual Direction",
                "text": "Focus on three key aspects: (1) Setup/hold timing window violation, (2) Resolution settling time in the 1st FF, (3) Exponential decay nature of MTBF."
            }
        ],
        "source_metadata": {
            "source": "HDL Arena Digital Logic Bank",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Standard hardware interview concept."
        },
        "test_suite_version": "1.0.0"
    },

    # =========================================================================
    # 2. INTERMEDIATE LEVEL
    # =========================================================================

    # Verilog - Coding (Existing ALU)
    "alu_4bit": {
        "id": "alu_4bit",
        "title": "4-bit Arithmetic Logic Unit (ALU)",
        "topic": "Arithmetic Units and ALUs",
        "category": "Arithmetic Units and ALUs",
        "difficulty": "Intermediate",
        "language": "verilog",
        "type": "coding",
        "tags": ["Arithmetic", "ALU", "Datapath"],
        "description": (
            "Design a 4-bit Arithmetic Logic Unit supporting 6 operations selected by 3-bit 'opcode':\n"
            "• 3'b000: Addition (out = a + b)\n"
            "• 3'b001: Subtraction (out = a - b)\n"
            "• 3'b010: Bitwise AND (out = a & b)\n"
            "• 3'b011: Bitwise OR (out = a | b)\n"
            "• 3'b100: Bitwise XOR (out = a ^ b)\n"
            "• 3'b101: Logical Shift Left (out = a << 1)\n"
            "• Default: out = 4'b0000\n"
            "Also output 'zero' flag (high when out == 4'b0000) and 'carry' flag (overflow for addition or borrow for subtraction)."
        ),
        "requirements": [
            "Compute 4-bit 'out', 1-bit 'zero', and 1-bit 'carry'.",
            "Zero flag must be high whenever out is 0."
        ],
        "constraints": ["Combinational implementation."],
        "module_name": "alu_4bit",
        "ports": [
            {"name": "a", "direction": "input", "width": "4-bit [3:0]", "desc": "Operand A"},
            {"name": "b", "direction": "input", "width": "4-bit [3:0]", "desc": "Operand B"},
            {"name": "opcode", "direction": "input", "width": "3-bit [2:0]", "desc": "ALU operation code"},
            {"name": "out", "direction": "output", "width": "4-bit [3:0]", "desc": "4-bit ALU result"},
            {"name": "carry", "direction": "output", "width": "1-bit", "desc": "Carry or borrow flag"},
            {"name": "zero", "direction": "output", "width": "1-bit", "desc": "Zero result flag"}
        ],
        "interface": (
            "module alu_4bit(\n"
            "    input  wire [3:0] a,\n"
            "    input  wire [3:0] b,\n"
            "    input  wire [2:0] opcode,\n"
            "    output reg  [3:0] out,\n"
            "    output reg        carry,\n"
            "    output wire       zero\n"
            ");"
        ),
        "starter_files": {
            "alu_4bit.v": (
                "module alu_4bit(\n"
                "    input  wire [3:0] a,\n"
                "    input  wire [3:0] b,\n"
                "    input  wire [2:0] opcode,\n"
                "    output reg  [3:0] out,\n"
                "    output reg        carry,\n"
                "    output wire       zero\n"
                ");\n\n"
                "    // TODO: Implement 4-bit ALU operations:\n"
                "    // 3'b000: Addition (out = a + b, capture carry overflow)\n"
                "    // 3'b001: Subtraction (out = a - b, capture borrow)\n"
                "    // 3'b010: Bitwise AND\n"
                "    // 3'b011: Bitwise OR\n"
                "    // 3'b100: Bitwise XOR\n"
                "    // 3'b101: Logical Shift Left (a << 1)\n"
                "    // Default: out = 4'b0000\n"
                "    // Compute 'zero' flag (high when out == 4'b0000)\n\n"
                "endmodule\n"
            )
        },
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Concatenation Trick",
                "text": "You can capture both carry and 4-bit sum cleanly using concatenation: `{carry, out} = a + b;`."
            },
            {
                "index": 1,
                "cost": 0.5,
                "title": "Zero Flag Implementation",
                "text": "For the zero flag, use continuous assignment: `assign zero = (out == 4'b0000);`."
            }
        ],
        "hints": [
            "Use {carry, out} = a + b to capture carry cleanly.",
            "Always include default in case statement to prevent inferred latches."
        ],
        "explanation": "Concatenation `{carry, out} = a + b;` handles 5-bit addition directly in hardware. Continuous assignment for `zero` avoids latch generation.",
        "source_metadata": {
            "source": "HDL Arena Curated Library",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Standard 4-bit ALU verification challenge."
        },
        "test_suite_version": "1.0.0",
        "reference_solution_policy": "Full canonical code available for 1.0 VJ Coin.",
        "testbench": r"""
`timescale 1ns/1ps
module tb;
    reg [3:0] a, b;
    reg [2:0] opcode;
    wire [3:0] out;
    wire carry, zero;

    alu_4bit dut (.a(a), .b(b), .opcode(opcode), .out(out), .carry(carry), .zero(zero));

    task report_test(input [63:0] t_id, input [255:0] t_name, input passed, input [255:0] detail, input [31:0] t_time, input is_hidden);
        begin
            if (passed)
                $display("::TEST::%0s::%0s::PASSED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
            else
                $display("::TEST::%0s::%0s::FAILED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
        end
    endtask

    task log_cycle(input [31:0] t_val, input [127:0] in_str, input [127:0] exp_str, input [127:0] act_str, input match);
        begin
            $display("::CYCLE::time=%0dns::inputs=%0s::expected=%0s::actual=%0s::match=%0d::time_num=%0d",
                     t_val, in_str, exp_str, act_str, match, t_val);
        end
    endtask

    reg sample_mode;

    initial begin
        sample_mode = $test$plusargs("SAMPLE_ONLY");
        $dumpfile("wave.vcd");
        $dumpvars(0, tb);

        // TEST 1: Addition with Carry (Sample)
        a = 4'd12; b = 4'd5; opcode = 3'b000; #10;
        log_cycle($time, "12+5 (ADD)", "{c=1,out=1}", $sformatf("{c=%0d,out=%0d}", carry, out), (carry === 1'b1 && out === 4'd1));
        if (carry === 1'b1 && out === 4'd1 && zero === 1'b0)
            report_test("tc_01", "ALU Addition with Carry", 1, "12+5 = 17 => carry=1, out=1", $time, 0);
        else report_test("tc_01", "ALU Addition with Carry", 0, "Addition carry mismatch", $time, 0);

        // TEST 2: Subtraction producing Zero (Sample)
        a = 4'd7; b = 4'd7; opcode = 3'b001; #10;
        log_cycle($time, "7-7 (SUB)", "{z=1,out=0}", $sformatf("{z=%0d,out=%0d}", zero, out), (zero === 1'b1 && out === 4'd0));
        if (zero === 1'b1 && out === 4'd0)
            report_test("tc_02", "ALU Subtraction with Zero Flag", 1, "7-7 = 0 => zero=1", $time, 0);
        else report_test("tc_02", "ALU Subtraction with Zero Flag", 0, "Zero flag failed", $time, 0);

        if (sample_mode) begin
            #10; $finish;
        end

        // TEST 3: Bitwise XOR (Hidden)
        a = 4'b1010; b = 4'b0110; opcode = 3'b100; #10;
        log_cycle($time, "1010^0110 (XOR)", "1100", $sformatf("%04b", out), (out === 4'b1100));
        if (out === 4'b1100)
            report_test("tc_03", "ALU Bitwise XOR", 1, "1010 ^ 0110 = 1100 verified", $time, 1);
        else report_test("tc_03", "ALU Bitwise XOR", 0, "XOR mismatch", $time, 1);

        // TEST 4: Logical Shift Left (Hidden)
        a = 4'b0101; b = 4'b0000; opcode = 3'b101; #10;
        log_cycle($time, "0101<<1 (SLL)", "1010", $sformatf("%04b", out), (out === 4'b1010));
        if (out === 4'b1010)
            report_test("tc_04", "ALU Shift Left", 1, "Shift left verified", $time, 1);
        else report_test("tc_04", "ALU Shift Left", 0, "Shift mismatch", $time, 1);

        #10; $finish;
    end
endmodule
""",
        "solution": {
            "cost": 1,
            "title": "4-bit Arithmetic Logic Unit with Combined Carry Concatenation",
            "overview": "This ALU implements arithmetic and logic operations with zero flag detection.",
            "canonical_code": {
                "alu_4bit.v": (
                    "module alu_4bit(\n"
                    "    input  wire [3:0] a,\n"
                    "    input  wire [3:0] b,\n"
                    "    input  wire [2:0] opcode,\n"
                    "    output reg  [3:0] out,\n"
                    "    output reg        carry,\n"
                    "    output wire       zero\n"
                    ");\n\n"
                    "    assign zero = (out == 4'b0000);\n\n"
                    "    always @(*) begin\n"
                    "        carry = 1'b0;\n"
                    "        case (opcode)\n"
                    "            3'b000: {carry, out} = a + b;\n"
                    "            3'b001: {carry, out} = a - b;\n"
                    "            3'b010: out = a & b;\n"
                    "            3'b011: out = a | b;\n"
                    "            3'b100: out = a ^ b;\n"
                    "            3'b101: out = a << 1;\n"
                    "            default: out = 4'b0000;\n"
                    "        endcase\n"
                    "    end\n\n"
                    "endmodule\n"
                )
            }
        }
    },

    # Verilog - Coding (Existing FSM Sequence Detector)
    "fsm_seq101": {
        "id": "fsm_seq101",
        "title": "Sequence Detector (Pattern '101')",
        "topic": "Finite State Machines",
        "category": "Finite State Machines",
        "difficulty": "Intermediate",
        "language": "verilog",
        "type": "coding",
        "tags": ["FSM", "Sequential", "Pattern Matching"],
        "description": (
            "Design a finite state machine to detect the sequence '101' in an incoming bitstream 'in_bit' "
            "synchronous to the rising edge of 'clk'.\n\n"
            "• Active-high synchronous reset 'rst' returns FSM to IDLE state with detected = 0.\n"
            "• 'detected' is asserted for 1 cycle when the preceding 3 bits equal '101'.\n"
            "• Overlapping sequences must be detected: e.g. bitstream '10101' must trigger twice (at cycle 3 and cycle 5)."
        ),
        "requirements": [
            "Synchronous reset active-high.",
            "Overlapping detection required.",
            "Output detected high for exactly one clock cycle per detection."
        ],
        "constraints": ["Clock period: 10ns"],
        "module_name": "fsm_seq101",
        "ports": [
            {"name": "clk", "direction": "input", "width": "1-bit", "desc": "Clock"},
            {"name": "rst", "direction": "input", "width": "1-bit", "desc": "Active-high sync reset"},
            {"name": "in_bit", "direction": "input", "width": "1-bit", "desc": "Serial bitstream"},
            {"name": "detected", "direction": "output", "width": "1-bit", "desc": "Sequence match flag"}
        ],
        "interface": (
            "module fsm_seq101(\n"
            "    input  wire clk,\n"
            "    input  wire rst,\n"
            "    input  wire in_bit,\n"
            "    output reg  detected\n"
            ");"
        ),
        "starter_files": {
            "fsm_seq101.v": (
                "module fsm_seq101(\n"
                "    input  wire clk,\n"
                "    input  wire rst,\n"
                "    input  wire in_bit,\n"
                "    output reg  detected\n"
                ");\n\n"
                "    // TODO: Define FSM state parameters and state registers.\n"
                "    // TODO: Implement synchronous active-high reset to initial state.\n"
                "    // TODO: Detect overlapping pattern '101' in incoming serial in_bit stream.\n"
                "    // TODO: Assert 'detected' flag for 1 clock cycle upon pattern match.\n\n"
                "endmodule\n"
            )
        },
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Mealy State Encoding",
                "text": "Use 3 states: S0 (none / reset), S1 (matched '1'), S2 (matched '10')."
            },
            {
                "index": 1,
                "cost": 0.5,
                "title": "Overlap Transition",
                "text": "When in state S2 and input in_bit is 1, detected=1 and next_state goes back to S1 (not S0!), because the trailing '1' of '101' is also the leading '1' of the next sequence."
            }
        ],
        "hints": [
            "Overlapping detection requires returning to S1 upon match, not IDLE.",
            "Mealy outputs assert in the exact cycle the final bit arrives."
        ],
        "explanation": "A Mealy FSM transitions to state S1 upon matching '101' so that the final '1' immediately acts as the start of any subsequent overlapping sequence.",
        "source_metadata": {
            "source": "HDL Arena Curated Library",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Standard sequence detector interview question."
        },
        "test_suite_version": "1.0.0",
        "reference_solution_policy": "Full canonical code available for 1.0 VJ Coin.",
        "testbench": r"""
`timescale 1ns/1ps
module tb;
    reg clk = 0;
    reg rst = 0;
    reg in_bit = 0;
    wire detected;

    fsm_seq101 dut (.clk(clk), .rst(rst), .in_bit(in_bit), .detected(detected));
    always #5 clk = ~clk;

    task report_test(input [63:0] t_id, input [255:0] t_name, input passed, input [255:0] detail, input [31:0] t_time, input is_hidden);
        begin
            if (passed)
                $display("::TEST::%0s::%0s::PASSED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
            else
                $display("::TEST::%0s::%0s::FAILED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
        end
    endtask

    task log_cycle(input [31:0] t_val, input [127:0] in_str, input [127:0] exp_str, input [127:0] act_str, input match);
        begin
            $display("::CYCLE::time=%0dns::inputs=%0s::expected=%0s::actual=%0s::match=%0d::time_num=%0d",
                     t_val, in_str, exp_str, act_str, match, t_val);
        end
    endtask

    reg sample_mode;

    initial begin
        sample_mode = $test$plusargs("SAMPLE_ONLY");
        $dumpfile("wave.vcd");
        $dumpvars(0, tb);

        // TEST 1: Reset Check (Sample)
        rst = 1; in_bit = 1; @(posedge clk); #1;
        log_cycle($time, "rst=1,in=1", "0", (detected ? "1" : "0"), (detected === 1'b0));
        if (detected === 1'b0)
            report_test("tc_01", "Reset state outputs zero", 1, "No false positive on reset", $time, 0);
        else report_test("tc_01", "Reset state outputs zero", 0, "Spurious detection on reset", $time, 0);

        // TEST 2: Single 101 sequence (Sample)
        rst = 0; in_bit = 1; @(posedge clk); #1;
        log_cycle($time, "bit 1", "0", (detected ? "1" : "0"), (detected === 1'b0));
        in_bit = 0; @(posedge clk); #1;
        log_cycle($time, "bit 0", "0", (detected ? "1" : "0"), (detected === 1'b0));
        in_bit = 1; @(posedge clk); #1;
        log_cycle($time, "bit 1 (match)", "1", (detected ? "1" : "0"), (detected === 1'b1));
        if (detected === 1'b1)
            report_test("tc_02", "Single '101' Pattern Detection", 1, "Asserted accurately on 3rd bit", $time, 0);
        else report_test("tc_02", "Single '101' Pattern Detection", 0, "Failed to detect '101'", $time, 0);

        if (sample_mode) begin
            #10; $finish;
        end

        // TEST 3: Overlapping Sequence (Hidden)
        in_bit = 0; @(posedge clk); #1;
        in_bit = 1; @(posedge clk); #1;
        log_cycle($time, "bit 1 (overlap match)", "1", (detected ? "1" : "0"), (detected === 1'b1));
        if (detected === 1'b1)
            report_test("tc_03", "Overlapping '10101' Detection", 1, "Successfully detected second pattern", $time, 1);
        else report_test("tc_03", "Overlapping '10101' Detection", 0, "Failed overlap detection", $time, 1);

        // TEST 4: Zeros rejection (Hidden)
        in_bit = 0; repeat (3) @(posedge clk); #1;
        log_cycle($time, "zeros stream", "0", (detected ? "1" : "0"), (detected === 1'b0));
        if (detected === 1'b0)
            report_test("tc_04", "Negative Stream (000) Rejection", 1, "No false positive on all zeros", $time, 1);
        else report_test("tc_04", "Negative Stream (000) Rejection", 0, "False positive triggered", $time, 1);

        #10; $finish;
    end
endmodule
""",
        "solution": {
            "cost": 1,
            "title": "Overlapping Sequence Detector '101' (Mealy FSM)",
            "overview": "Mealy state machine detecting '101' with overlap support.",
            "canonical_code": {
                "fsm_seq101.v": (
                    "module fsm_seq101(\n"
                    "    input  wire clk,\n"
                    "    input  wire rst,\n"
                    "    input  wire in_bit,\n"
                    "    output reg  detected\n"
                    ");\n\n"
                    "    localparam S0 = 2'b00, S1 = 2'b01, S2 = 2'b10;\n"
                    "    reg [1:0] state, next_state;\n\n"
                    "    always @(posedge clk) begin\n"
                    "        if (rst) state <= S0;\n"
                    "        else state <= next_state;\n"
                    "    end\n\n"
                    "    always @(*) begin\n"
                    "        next_state = state;\n"
                    "        detected = 1'b0;\n"
                    "        case (state)\n"
                    "            S0: if (in_bit) next_state = S1;\n"
                    "            S1: if (~in_bit) next_state = S2;\n"
                    "            S2: begin\n"
                    "                if (in_bit) begin\n"
                    "                    detected = 1'b1;\n"
                    "                    next_state = S1;\n"
                    "                end else next_state = S0;\n"
                    "            end\n"
                    "        endcase\n"
                    "    end\n\n"
                    "endmodule\n"
                )
            }
        }
    },

    # C++ - Coding
    "cpp_ring_buffer": {
        "id": "cpp_ring_buffer",
        "title": "C++ Circular Ring Buffer for Verification",
        "topic": "C++ Data Structures & Verification",
        "category": "Software for Hardware Engineers",
        "difficulty": "Intermediate",
        "language": "cpp",
        "type": "coding",
        "entry_point": "RingBuffer",
        "class_name": "RingBuffer",
        "tags": ["C++", "Ring Buffer", "Circular Queue", "Verification"],
        "description": (
            "Implement a fixed-capacity circular ring buffer in C++: `RingBuffer<int, 4>`.\n"
            "Must support:\n"
            "• `bool push(int val)`: If full, returns `false`. Otherwise inserts `val` and returns `true`.\n"
            "• `bool pop(int &out)`: If empty, returns `false`. Otherwise extracts oldest item into `out` and returns `true`.\n"
            "• `bool is_full() const`\n"
            "• `bool is_empty() const`\n"
            "• `size_t size() const`"
        ),
        "starter_files": {
            "ring_buffer.hpp": (
                "#pragma once\n"
                "#include <cstddef>\n"
                "#include <stddef.h>\n"
                "using std::size_t;\n\n"
                "template<typename T, size_t Capacity>\n"
                "class RingBuffer {\n"
                "private:\n"
                "    T buffer_[Capacity];\n"
                "    size_t head_ = 0;\n"
                "    size_t tail_ = 0;\n"
                "    size_t count_ = 0;\n"
                "public:\n"
                "    bool push(const T& val) {\n"
                "        // TODO: Implement push\n"
                "        return false;\n"
                "    }\n"
                "    bool pop(T& out) {\n"
                "        // TODO: Implement pop\n"
                "        return false;\n"
                "    }\n"
                "    bool is_full() const { return count_ == Capacity; }\n"
                "    bool is_empty() const { return count_ == 0; }\n"
                "    size_t size() const { return count_; }\n"
                "};\n"
            )
        },
        "solution": {
            "cost": 1,
            "title": "C++ Circular Ring Buffer for Verification",
            "overview": "Template-based circular FIFO queue with modulo pointer wrapping and O(1) push/pop.",
            "canonical_code": {
                "ring_buffer.hpp": (
                    "#pragma once\n"
                    "#include <cstddef>\n"
                    "#include <stddef.h>\n"
                    "using std::size_t;\n\n"
                    "template<typename T, size_t Capacity>\n"
                    "class RingBuffer {\n"
                    "private:\n"
                    "    T buffer_[Capacity];\n"
                    "    size_t head_ = 0;\n"
                    "    size_t tail_ = 0;\n"
                    "    size_t count_ = 0;\n"
                    "public:\n"
                    "    bool push(const T& val) {\n"
                    "        if (is_full()) return false;\n"
                    "        buffer_[tail_] = val;\n"
                    "        tail_ = (tail_ + 1) % Capacity;\n"
                    "        count_++;\n"
                    "        return true;\n"
                    "    }\n"
                    "    bool pop(T& out) {\n"
                    "        if (is_empty()) return false;\n"
                    "        out = buffer_[head_];\n"
                    "        head_ = (head_ + 1) % Capacity;\n"
                    "        count_--;\n"
                    "        return true;\n"
                    "    }\n"
                    "    bool is_full() const { return count_ == Capacity; }\n"
                    "    bool is_empty() const { return count_ == 0; }\n"
                    "    size_t size() const { return count_; }\n"
                    "};\n"
                )
            }
        },
        "test_harness": {
            "driver": r"""
#include <iostream>
#include <cassert>
#include "ring_buffer.hpp"

int main() {
    RingBuffer<int, 4> rb;
    int val = 0;
    int passed = 0;

    // Test 1: Empty on start
    bool t1 = rb.is_empty() && !rb.is_full() && rb.size() == 0;
    if (t1) passed++;
    std::cout << "::TEST::tc_01::Initial Empty State::" << (t1 ? "PASSED" : "FAILED") << "::size=0::0ns::0\n";

    // Test 2: Push 4 items to full
    bool t2 = rb.push(10) && rb.push(20) && rb.push(30) && rb.push(40) && rb.is_full() && !rb.push(50);
    if (t2) passed++;
    std::cout << "::TEST::tc_02::Fill to Capacity::" << (t2 ? "PASSED" : "FAILED") << "::size=4::0ns::0\n";

    // Test 3: FIFO Pop order
    bool t3 = rb.pop(val) && val == 10 && rb.pop(val) && val == 20;
    if (t3) passed++;
    std::cout << "::TEST::tc_03::FIFO Order Pop::" << (t3 ? "PASSED" : "FAILED") << "::popped 10,20::0ns::1\n";

    // Test 4: Wraparound push and drain
    bool t4 = rb.push(60) && rb.push(70) && rb.pop(val) && val == 30 && rb.pop(val) && val == 40 &&
              rb.pop(val) && val == 60 && rb.pop(val) && val == 70 && rb.is_empty();
    if (t4) passed++;
    std::cout << "::TEST::tc_04::Wraparound & Drain::" << (t4 ? "PASSED" : "FAILED") << "::all items drained::0ns::1\n";

    return 0;
}
"""
        },
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Index Wrapping",
                "text": "Advance tail on push: `tail_ = (tail_ + 1) % Capacity;` and advance head on pop: `head_ = (head_ + 1) % Capacity;`."
            }
        ],
        "explanation": "Ring buffers maintain head (read) and tail (write) pointers wrapping modulo Capacity, with count tracking occupancy to differentiate between full and empty conditions.",
        "source_metadata": {
            "source": "HDL Arena Software Bank",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Standard C++ interview question for testbench verification engineers."
        },
        "test_suite_version": "1.0.0"
    },

    # Verilog - Debugging
    "debug_counter_overflow": {
        "id": "debug_counter_overflow",
        "title": "Debug: Off-by-One and Signed Modulo Bug",
        "topic": "RTL Debugging & Defect Isolation",
        "category": "RTL Debugging & Defect Isolation",
        "difficulty": "Intermediate",
        "language": "verilog",
        "type": "debugging",
        "tags": ["Debugging", "Counter", "Off-by-One", "Verilog"],
        "description": (
            "A junior engineer wrote a modulo-10 counter (0 to 9) that rolls over to 0 on the 10th clock.\n"
            "However, simulation shows two bugs:\n"
            "1. The counter counts up to 10 (decimal) before wrapping around instead of wrapping at 9!\n"
            "2. When reset is deasserted, it misses the first increment.\n\n"
            "Inspect the buggy code below, diagnose the flaw, and fix it so `count` ranges strictly from 4'd0 to 4'd9."
        ),
        "module_name": "mod10_counter",
        "starter_files": {
            "mod10_counter.v": (
                "module mod10_counter(\n"
                "    input  wire       clk,\n"
                "    input  wire       rst,\n"
                "    output reg  [3:0] count\n"
                ");\n\n"
                "    // BUGGY IMPLEMENTATION:\n"
                "    // Find and fix the rollover condition and reset logic\n"
                "    always @(posedge clk) begin\n"
                "        if (rst) begin\n"
                "            count <= 4'd1;\n"
                "        end else if (count == 4'd10) begin\n"
                "            count <= 4'd0;\n"
                "        end else begin\n"
                "            count <= count + 1'b1;\n"
                "        end\n"
                "    end\n\n"
                "endmodule\n"
            )
        },
        "testbench": r"""
`timescale 1ns/1ps
module tb;
    reg clk = 0;
    reg rst = 0;
    wire [3:0] count;

    mod10_counter dut (.clk(clk), .rst(rst), .count(count));
    always #5 clk = ~clk;

    task report_test(input [63:0] t_id, input [255:0] t_name, input passed, input [255:0] detail, input [31:0] t_time, input is_hidden);
        begin
            if (passed)
                $display("::TEST::%0s::%0s::PASSED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
            else
                $display("::TEST::%0s::%0s::FAILED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
        end
    endtask

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb);

        // TEST 1: Reset must clear count to 0
        rst = 1; @(posedge clk); #1;
        if (count === 4'd0) report_test("tc_01", "Reset to Zero", 1, "count=0", $time, 0);
        else report_test("tc_01", "Reset to Zero", 0, "count did not reset to 0", $time, 0);

        // TEST 2: Counting 0 through 9
        rst = 0;
        begin : count_loop
            reg ok; ok = 1;
            integer i;
            for (i = 1; i <= 9; i = i + 1) begin
                @(posedge clk); #1;
                if (count !== i[3:0]) ok = 0;
            end
            if (ok) report_test("tc_02", "Count Sequence 1..9", 1, "Clean count sequence", $time, 0);
            else report_test("tc_02", "Count Sequence 1..9", 0, "Sequence mismatch", $time, 0);
        end

        // TEST 3: Rollover from 9 to 0
        @(posedge clk); #1;
        if (count === 4'd0) report_test("tc_03", "Modulo 10 Rollover", 1, "Wrapped 9 -> 0 accurately", $time, 1);
        else report_test("tc_03", "Modulo 10 Rollover", 0, "Did not wrap from 9 to 0", $time, 1);

        #10; $finish;
    end
endmodule
""",
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Reset Bug",
                "text": "Notice what `rst` assigns `count` to in the starter code. It assigns 4'd1 instead of 4'd0!"
            },
            {
                "index": 1,
                "cost": 0.5,
                "title": "Rollover Bug",
                "text": "A modulo-10 counter has 10 states: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9. When `count == 4'd9`, the next clock edge must transition to 4'd0."
            }
        ],
        "explanation": "A decade/modulo-10 counter must reset to 0 and wrap when `count == 4'd9` on the subsequent clock edge.",
        "solution": {
            "cost": 1,
            "title": "Modulo-10 Counter Bug Fix",
            "overview": "Fix synchronous reset to 4'd0 and correct rollover boundary to 4'd9.",
            "canonical_code": {
                "mod10_counter.v": (
                    "module mod10_counter(\n"
                    "    input  wire       clk,\n"
                    "    input  wire       rst,\n"
                    "    output reg  [3:0] count\n"
                    ");\n\n"
                    "    always @(posedge clk) begin\n"
                    "        if (rst) begin\n"
                    "            count <= 4'd0;\n"
                    "        end else if (count == 4'd9) begin\n"
                    "            count <= 4'd0;\n"
                    "        end else begin\n"
                    "            count <= count + 1'b1;\n"
                    "        end\n"
                    "    end\n\n"
                    "endmodule\n"
                )
            }
        },
        "source_metadata": {
            "source": "HDL Arena Debugging Challenges",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Real-world RTL bug isolation exercise."
        },
        "test_suite_version": "1.0.0"
    },

    # Predict Output - Verilog Event Scheduling
    "pred_verilog_scheduling": {
        "id": "pred_verilog_scheduling",
        "title": "Predict Output: Verilog Stratified Event Queue",
        "topic": "Verilog Event Queue Semantics",
        "category": "Verilog Syntax & Simulation",
        "difficulty": "Intermediate",
        "language": "verilog",
        "type": "predict_output",
        "tags": ["Event Queue", "Active", "NBA", "Stratified"],
        "description": (
            "Consider the following Verilog code executing at time 0:\n\n"
            "```verilog\n"
            "reg [7:0] a, b;\n"
            "initial begin\n"
            "    a = 8'd10;\n"
            "    b <= 8'd20;\n"
            "    a = b + 8'd5;\n"
            "    #1;\n"
            "    $display(\"a=%0d,b=%0d\", a, b);\n"
            "end\n"
            "```\n\n"
            "Assume `b` was initialized to `8'd0` before the block executed.\n"
            "What exact string is printed by `$display`? (Format: `a=X,b=Y`)"
        ),
        "expected_output": "a=5,b=20",
        "acceptable_outputs": ["a=5,b=20", "a=5, b=20"],
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "NBA Scheduling Rule",
                "text": "Non-blocking assignment `b <= 8'd20` evaluates its RHS in the Active region, but does NOT update variable `b` until the NBA region!"
            },
            {
                "index": 1,
                "cost": 0.5,
                "title": "Active Execution Order",
                "text": "When `a = b + 8'd5` executes immediately in the Active region, what is the value of `b` at that moment? `b` is still 0! So `a = 0 + 5 = 5`."
            }
        ],
        "explanation": "Because `b <= 20` is non-blocking, `b` remains 0 while subsequent blocking statements in the Active region execute. Therefore `a = 0 + 5 = 5`. At the NBA update, `b` becomes 20.",
        "source_metadata": {
            "source": "HDL Arena Curated Library",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Standard IEEE 1364 simulation event queue interview question."
        },
        "test_suite_version": "1.0.0"
    },

    # =========================================================================
    # 3. ADVANCED LEVEL
    # =========================================================================

    # Verilog - Multi-Module FIFO (Existing Synchronous FIFO)
    "sync_fifo": {
        "id": "sync_fifo",
        "title": "Synchronous FIFO (Multi-Module: Controller & Memory)",
        "topic": "FIFO and Buffer Design",
        "category": "FIFO and Buffer Design",
        "difficulty": "Advanced",
        "language": "verilog",
        "type": "coding",
        "tags": ["FIFO", "Multi-Module", "Memory", "Pointers", "Backpressure"],
        "description": (
            "Design a 4-entry deep, 8-bit wide Synchronous FIFO split across two interacting modules:\n"
            "1. 'fifo_mem' (Memory Array): 4x8 RAM storage with synchronous write and asynchronous read.\n"
            "2. 'sync_fifo' (Top Controller): Generates read/write pointers, occupancy count, and 'full'/'empty' flags.\n\n"
            "Behavior Rules:\n"
            "• Active-high sync reset clears pointers and count to 0 (empty = 1, full = 0).\n"
            "• Simultaneous read and write when neither full nor empty is supported without changing count.\n"
            "• Write ignored when full; Read ignored when empty."
        ),
        "requirements": [
            "Multi-module RTL design: instantiate 'fifo_mem' inside 'sync_fifo'.",
            "Generate accurate 'full' and 'empty' flags.",
            "Count tracks number of valid items (0 to 4)."
        ],
        "constraints": ["Depth = 4 words, Width = 8 bits."],
        "module_name": "sync_fifo",
        "ports": [
            {"name": "clk", "direction": "input", "width": "1-bit", "desc": "Clock"},
            {"name": "rst", "direction": "input", "width": "1-bit", "desc": "Synchronous reset"},
            {"name": "wr_en", "direction": "input", "width": "1-bit", "desc": "Write enable"},
            {"name": "din", "direction": "input", "width": "8-bit [7:0]", "desc": "Data input"},
            {"name": "rd_en", "direction": "input", "width": "1-bit", "desc": "Read enable"},
            {"name": "dout", "direction": "output", "width": "8-bit [7:0]", "desc": "Data output"},
            {"name": "full", "direction": "output", "width": "1-bit", "desc": "FIFO full flag"},
            {"name": "empty", "direction": "output", "width": "1-bit", "desc": "FIFO empty flag"},
            {"name": "count", "direction": "output", "width": "3-bit [2:0]", "desc": "FIFO item count"}
        ],
        "interface": (
            "module sync_fifo(\n"
            "    input  wire       clk,\n"
            "    input  wire       rst,\n"
            "    input  wire       wr_en,\n"
            "    input  wire [7:0] din,\n"
            "    input  wire       rd_en,\n"
            "    output wire [7:0] dout,\n"
            "    output wire       full,\n"
            "    output wire       empty,\n"
            "    output reg  [2:0] count\n"
            ");"
        ),
        "starter_files": {
            "sync_fifo.v": (
                "module sync_fifo(\n"
                "    input  wire       clk,\n"
                "    input  wire       rst,\n"
                "    input  wire       wr_en,\n"
                "    input  wire [7:0] din,\n"
                "    input  wire       rd_en,\n"
                "    output wire [7:0] dout,\n"
                "    output wire       full,\n"
                "    output wire       empty,\n"
                "    output reg  [2:0] count\n"
                ");\n\n"
                "    // TODO: Declare read and write pointer registers\n"
                "    // TODO: Instantiate memory submodule 'fifo_mem'\n"
                "    // TODO: Implement pointer increment and wrap-around logic\n"
                "    // TODO: Track occupancy count (0 to 4 items)\n"
                "    // TODO: Generate full and empty status flags\n\n"
                "endmodule\n"
            ),
            "fifo_mem.v": (
                "module fifo_mem(\n"
                "    input  wire       clk,\n"
                "    input  wire       wr_en,\n"
                "    input  wire [1:0] wr_addr,\n"
                "    input  wire [7:0] din,\n"
                "    input  wire [1:0] rd_addr,\n"
                "    output wire [7:0] dout\n"
                ");\n\n"
                "    // TODO: Declare 4x8-bit internal memory array\n"
                "    // TODO: Synchronous write on posedge clk when wr_en is high\n"
                "    // TODO: Asynchronous/combinational read indexed by rd_addr\n\n"
                "endmodule\n"
            )
        },
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Submodule Partitioning",
                "text": "Instantiate `fifo_mem mem_inst (.clk(clk), .wr_en(actual_wr), .wr_addr(wr_ptr), .din(din), .rd_addr(rd_ptr), .dout(dout));` where `actual_wr = wr_en && !full;`."
            },
            {
                "index": 1,
                "cost": 0.5,
                "title": "Occupancy Counter Handling",
                "text": "When both write and read occur simultaneously (`actual_wr && actual_rd`), occupancy count remains unchanged!"
            }
        ],
        "hints": [
            "Use gated enables actual_wr = wr_en && !full and actual_rd = rd_en && !empty.",
            "Count needs 3 bits to represent values 0 through 4."
        ],
        "explanation": "Partitioning the RAM array into a dedicated submodule allows physical synthesis to map the memory array directly into Block RAM or distributed registers.",
        "source_metadata": {
            "source": "HDL Arena Curated Library",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Production-grade synchronous FIFO architecture."
        },
        "test_suite_version": "1.0.0",
        "reference_solution_policy": "Full canonical multi-module code available for 1.0 VJ Coin.",
        "testbench": r"""
`timescale 1ns/1ps
module tb;
    reg clk = 0;
    reg rst = 0;
    reg wr_en = 0;
    reg rd_en = 0;
    reg [7:0] din = 0;
    wire [7:0] dout;
    wire full, empty;
    wire [2:0] count;

    sync_fifo dut (
        .clk(clk), .rst(rst), .wr_en(wr_en), .din(din),
        .rd_en(rd_en), .dout(dout), .full(full), .empty(empty), .count(count)
    );
    always #5 clk = ~clk;

    task report_test(input [63:0] t_id, input [255:0] t_name, input passed, input [255:0] detail, input [31:0] t_time, input is_hidden);
        begin
            if (passed)
                $display("::TEST::%0s::%0s::PASSED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
            else
                $display("::TEST::%0s::%0s::FAILED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
        end
    endtask

    task log_cycle(input [31:0] t_val, input [127:0] in_str, input [127:0] exp_str, input [127:0] act_str, input match);
        begin
            $display("::CYCLE::time=%0dns::inputs=%0s::expected=%0s::actual=%0s::match=%0d::time_num=%0d",
                     t_val, in_str, exp_str, act_str, match, t_val);
        end
    endtask

    reg sample_mode;

    initial begin
        sample_mode = $test$plusargs("SAMPLE_ONLY");
        $dumpfile("wave.vcd");
        $dumpvars(0, tb);

        // TEST 1: Reset Condition (Sample)
        rst = 1; @(posedge clk); #1;
        log_cycle($time, "rst=1", "{empty=1,full=0,cnt=0}", $sformatf("{empty=%0d,full=%0d,cnt=%0d}", empty, full, count), (empty === 1'b1 && full === 1'b0 && count === 3'd0));
        if (empty === 1'b1 && full === 1'b0 && count === 3'd0)
            report_test("tc_01", "Reset initializes FIFO to Empty", 1, "Count is 0, empty flag high", $time, 0);
        else report_test("tc_01", "Reset initializes FIFO to Empty", 0, "Reset flags error", $time, 0);

        // TEST 2: Write 4 items to Full (Sample)
        rst = 0;
        wr_en = 1; din = 8'hA1; @(posedge clk); #1;
        wr_en = 1; din = 8'hB2; @(posedge clk); #1;
        wr_en = 1; din = 8'hC3; @(posedge clk); #1;
        wr_en = 1; din = 8'hD4; @(posedge clk); #1;
        wr_en = 0;
        log_cycle($time, "wrote 4 items", "{full=1,empty=0,cnt=4}", $sformatf("{full=%0d,empty=%0d,cnt=%0d}", full, empty, count), (full === 1'b1 && count === 3'd4));
        if (full === 1'b1 && count === 3'd4)
            report_test("tc_02", "Write to Full capacity", 1, "Full flag asserted at 4 items", $time, 0);
        else report_test("tc_02", "Write to Full capacity", 0, "Full flag failed", $time, 0);

        if (sample_mode) begin
            #10; $finish;
        end

        // TEST 3: Read back first item (Hidden)
        rd_en = 1; #1;
        log_cycle($time, "read item 1", "dout=0xA1", $sformatf("dout=0x%02X", dout), (dout === 8'hA1));
        if (dout === 8'hA1)
            report_test("tc_03", "Read 1st FIFO Data (FIFO Order)", 1, "First item 0xA1 read accurately", $time, 1);
        else report_test("tc_03", "Read 1st FIFO Data (FIFO Order)", 0, "Data order mismatch", $time, 1);

        // TEST 4: Drain FIFO back to empty (Hidden)
        @(posedge clk); #1;
        @(posedge clk); #1;
        @(posedge clk); #1;
        rd_en = 0; #1;
        log_cycle($time, "drained FIFO", "{empty=1,cnt=0}", $sformatf("{empty=%0d,cnt=%0d}", empty, count), (empty === 1'b1 && count === 3'd0));
        if (empty === 1'b1 && count === 3'd0)
            report_test("tc_04", "Empty state after Drain", 1, "FIFO fully emptied", $time, 1);
        else report_test("tc_04", "Empty state after Drain", 0, "Empty flag failed after read", $time, 1);

        #10; $finish;
    end
endmodule
""",
        "solution": {
            "cost": 1,
            "title": "Modular Synchronous FIFO with Submodule SRAM Array",
            "overview": "A modular synchronous FIFO partitioned into storage array and control logic.",
            "canonical_code": {
                "sync_fifo.v": (
                    "module sync_fifo(\n"
                    "    input  wire       clk,\n"
                    "    input  wire       rst,\n"
                    "    input  wire       wr_en,\n"
                    "    input  wire [7:0] din,\n"
                    "    input  wire       rd_en,\n"
                    "    output wire [7:0] dout,\n"
                    "    output wire       full,\n"
                    "    output wire       empty,\n"
                    "    output reg  [2:0] count\n"
                    ");\n\n"
                    "    reg [1:0] wr_ptr, rd_ptr;\n"
                    "    wire actual_wr = wr_en && !full;\n"
                    "    wire actual_rd = rd_en && !empty;\n\n"
                    "    fifo_mem mem_inst (\n"
                    "        .clk(clk),\n"
                    "        .wr_en(actual_wr),\n"
                    "        .wr_addr(wr_ptr),\n"
                    "        .din(din),\n"
                    "        .rd_addr(rd_ptr),\n"
                    "        .dout(dout)\n"
                    ");\n\n"
                    "    assign full  = (count == 3'd4);\n"
                    "    assign empty = (count == 3'd0);\n\n"
                    "    always @(posedge clk) begin\n"
                    "        if (rst) begin\n"
                    "            wr_ptr <= 2'b00;\n"
                    "            rd_ptr <= 2'b00;\n"
                    "            count  <= 3'd0;\n"
                    "        end else begin\n"
                    "            if (actual_wr) wr_ptr <= wr_ptr + 1'b1;\n"
                    "            if (actual_rd) rd_ptr <= rd_ptr + 1'b1;\n\n"
                    "            case ({actual_wr, actual_rd})\n"
                    "                2'b10: count <= count + 1'b1;\n"
                    "                2'b01: count <= count - 1'b1;\n"
                    "                default: count <= count;\n"
                    "            endcase\n"
                    "        end\n"
                    "    end\n\n"
                    "endmodule\n"
                ),
                "fifo_mem.v": (
                    "module fifo_mem(\n"
                    "    input  wire       clk,\n"
                    "    input  wire       wr_en,\n"
                    "    input  wire [1:0] wr_addr,\n"
                    "    input  wire [7:0] din,\n"
                    "    input  wire [1:0] rd_addr,\n"
                    "    output wire [7:0] dout\n"
                    ");\n\n"
                    "    reg [7:0] ram [0:3];\n\n"
                    "    always @(posedge clk) begin\n"
                    "        if (wr_en) ram[wr_addr] <= din;\n"
                    "    end\n\n"
                    "    assign dout = ram[rd_addr];\n\n"
                    "endmodule\n"
                )
            }
        }
    },

    # Verilog - Pipeline Handshake (Existing Valid/Ready Pipeline)
    "valid_ready_pipe": {
        "id": "valid_ready_pipe",
        "title": "Valid/Ready Handshake Pipeline Stage",
        "topic": "Handshake Protocols",
        "category": "Handshake Protocols",
        "difficulty": "Advanced",
        "language": "verilog",
        "type": "coding",
        "tags": ["Protocols", "Valid/Ready", "Pipelines", "Backpressure"],
        "description": (
            "Design a 1-stage pipeline register with standard Valid/Ready forward and backward handshaking.\n\n"
            "Handshake Rules:\n"
            "• Upstream transaction occurs when 'us_valid && us_ready'.\n"
            "• Downstream transaction occurs when 'ds_valid && ds_ready'.\n"
            "• Pipeline stage can accept new data ('us_ready = 1') if it is empty OR if downstream accepts current data ('ds_ready = 1').\n"
            "• 'dout' updates with 'din' when upstream handshake succeeds."
        ),
        "requirements": [
            "No combinatorial loop between ready and valid signals.",
            "Backpressure propagation: when downstream ready is de-asserted and pipe is full, us_ready must deassert."
        ],
        "constraints": ["Data width: 8-bit [7:0]."],
        "module_name": "valid_ready_pipe",
        "ports": [
            {"name": "clk", "direction": "input", "width": "1-bit", "desc": "Clock"},
            {"name": "rst", "direction": "input", "width": "1-bit", "desc": "Synchronous reset"},
            {"name": "us_valid", "direction": "input", "width": "1-bit", "desc": "Upstream valid"},
            {"name": "us_ready", "direction": "output", "width": "1-bit", "desc": "Upstream ready (backpressure)"},
            {"name": "din", "direction": "input", "width": "8-bit [7:0]", "desc": "Input data"},
            {"name": "ds_valid", "direction": "output", "width": "1-bit", "desc": "Downstream valid"},
            {"name": "ds_ready", "direction": "input", "width": "1-bit", "desc": "Downstream ready"},
            {"name": "dout", "direction": "output", "width": "8-bit [7:0]", "desc": "Output data"}
        ],
        "interface": (
            "module valid_ready_pipe(\n"
            "    input  wire       clk,\n"
            "    input  wire       rst,\n"
            "    input  wire       us_valid,\n"
            "    output wire       us_ready,\n"
            "    input  wire [7:0] din,\n"
            "    output reg        ds_valid,\n"
            "    input  wire       ds_ready,\n"
            "    output reg  [7:0] dout\n"
            ");"
        ),
        "starter_files": {
            "valid_ready_pipe.v": (
                "module valid_ready_pipe(\n"
                "    input  wire       clk,\n"
                "    input  wire       rst,\n"
                "    input  wire       us_valid,\n"
                "    output wire       us_ready,\n"
                "    input  wire [7:0] din,\n"
                "    output reg        ds_valid,\n"
                "    input  wire       ds_ready,\n"
                "    output reg  [7:0] dout\n"
                ");\n\n"
                "    // TODO: Implement forward/backward Valid/Ready handshake logic.\n"
                "    // TODO: Compute upstream ready (us_ready) considering downstream status.\n"
                "    // TODO: Register din into dout on successful upstream transaction.\n"
                "    // TODO: Handle synchronous reset clearing ds_valid.\n\n"
                "endmodule\n"
            )
        },
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Ready Equation",
                "text": "The upstream ready signal is high whenever the pipe is empty (!ds_valid) OR when downstream is simultaneously consuming the current data (ds_ready): `assign us_ready = !ds_valid || ds_ready;`."
            }
        ],
        "hints": [
            "assign us_ready = !ds_valid || ds_ready avoids combinatorial loops.",
            "Update ds_valid with us_valid when us_ready is active."
        ],
        "explanation": "Forward-registered pipeline stages register the data output while computing backward ready combinationally to allow single-cycle backpressure propagation without deadlock.",
        "source_metadata": {
            "source": "HDL Arena Curated Library",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Standard AXI-Stream valid/ready pipeline slice."
        },
        "test_suite_version": "1.0.0",
        "reference_solution_policy": "Full canonical code available for 1.0 VJ Coin.",
        "testbench": r"""
`timescale 1ns/1ps
module tb;
    reg clk = 0;
    reg rst = 0;
    reg us_valid = 0;
    reg ds_ready = 0;
    reg [7:0] din = 0;
    wire us_ready, ds_valid;
    wire [7:0] dout;

    valid_ready_pipe dut (
        .clk(clk), .rst(rst), .us_valid(us_valid), .us_ready(us_ready),
        .din(din), .ds_valid(ds_valid), .ds_ready(ds_ready), .dout(dout)
    );
    always #5 clk = ~clk;

    task report_test(input [63:0] t_id, input [255:0] t_name, input passed, input [255:0] detail, input [31:0] t_time, input is_hidden);
        begin
            if (passed)
                $display("::TEST::%0s::%0s::PASSED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
            else
                $display("::TEST::%0s::%0s::FAILED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
        end
    endtask

    task log_cycle(input [31:0] t_val, input [127:0] in_str, input [63:0] exp_str, input [63:0] act_str, input match);
        begin
            $display("::CYCLE::time=%0dns::inputs=%0s::expected=%0s::actual=%0s::match=%0d::time_num=%0d",
                     t_val, in_str, exp_str, act_str, match, t_val);
        end
    endtask

    reg sample_mode;

    initial begin
        sample_mode = $test$plusargs("SAMPLE_ONLY");
        $dumpfile("wave.vcd");
        $dumpvars(0, tb);

        // TEST 1: Reset Check (Sample)
        rst = 1; @(posedge clk); #1;
        log_cycle($time, "rst=1", "{ds_valid=0,us_ready=1}", {ds_valid, us_ready}, (ds_valid === 1'b0 && us_ready === 1'b1));
        if (ds_valid === 1'b0 && us_ready === 1'b1)
            report_test("tc_01", "Reset Stage Ready Check", 1, "Reset clears downstream valid and asserts ready", $time, 0);
        else report_test("tc_01", "Reset Stage Ready Check", 0, "Reset flags failed", $time, 0);

        // TEST 2: Single beat (Sample)
        rst = 0; us_valid = 1; din = 8'h55; ds_ready = 1;
        @(posedge clk); #1;
        log_cycle($time, "us_valid=1,ds_ready=1", "{ds_valid=1,dout=0x55}", {ds_valid, dout}, (ds_valid === 1'b1 && dout === 8'h55));
        if (ds_valid === 1'b1 && dout === 8'h55)
            report_test("tc_02", "Single Beat Handshake", 1, "Transferred 0x55 successfully", $time, 0);
        else report_test("tc_02", "Single Beat Handshake", 0, "Transfer failed", $time, 0);

        if (sample_mode) begin
            #10; $finish;
        end

        // TEST 3: Backpressure (Hidden)
        us_valid = 1; din = 8'hAA; ds_ready = 0;
        @(posedge clk); #1;
        log_cycle($time, "stall (ds_ready=0)", "us_ready=0", us_ready, (us_ready === 1'b0));
        if (us_ready === 1'b0 && dout === 8'h55)
            report_test("tc_03", "Backpressure Propagation", 1, "us_ready de-asserted and pipe held data", $time, 1);
        else report_test("tc_03", "Backpressure Propagation", 0, "Backpressure failed", $time, 1);

        // TEST 4: Backpressure release (Hidden)
        ds_ready = 1; @(posedge clk); #1;
        log_cycle($time, "release backpressure", "us_ready=1", us_ready, (us_ready === 1'b1));
        if (us_ready === 1'b1)
            report_test("tc_04", "Backpressure Release Resume", 1, "Pipeline resumed transmission", $time, 1);
        else report_test("tc_04", "Backpressure Release Resume", 0, "Failed resume", $time, 1);

        #10; $finish;
    end
endmodule
""",
        "solution": {
            "cost": 1,
            "title": "Forward-Registered Valid/Ready Handshake Pipeline Stage",
            "overview": "A standard 1-stage Valid/Ready pipeline register.",
            "canonical_code": {
                "valid_ready_pipe.v": (
                    "module valid_ready_pipe(\n"
                    "    input  wire       clk,\n"
                    "    input  wire       rst,\n"
                    "    input  wire       us_valid,\n"
                    "    output wire       us_ready,\n"
                    "    input  wire [7:0] din,\n"
                    "    output reg        ds_valid,\n"
                    "    input  wire       ds_ready,\n"
                    "    output reg  [7:0] dout\n"
                    ");\n\n"
                    "    assign us_ready = !ds_valid || ds_ready;\n\n"
                    "    always @(posedge clk) begin\n"
                    "        if (rst) begin\n"
                    "            ds_valid <= 1'b0;\n"
                    "            dout     <= 8'h00;\n"
                    "        end else if (us_ready) begin\n"
                    "            ds_valid <= us_valid;\n"
                    "            if (us_valid) dout <= din;\n"
                    "        end\n"
                    "    end\n\n"
                    "endmodule\n"
                )
            }
        }
    },

    # SystemVerilog - Coding (Round Robin Arbiter with Interfaces)
    "sv_arbiter_rr": {
        "id": "sv_arbiter_rr",
        "title": "4-way Round-Robin Arbiter",
        "topic": "Arbitration & Scheduling",
        "category": "Arbitration & Scheduling",
        "difficulty": "Advanced",
        "language": "systemverilog",
        "type": "coding",
        "tags": ["SystemVerilog", "Round-Robin", "Arbiter", "Fairness"],
        "description": (
            "Design a 4-channel Round-Robin Arbiter in SystemVerilog.\n\n"
            "Specifications:\n"
            "• Inputs: `clk`, `rst_n` (active-low sync reset), `req[3:0]` (request lines).\n"
            "• Output: `grant[3:0]` (one-hot grant line).\n"
            "• When multiple requests are asserted, priority rotates round-robin starting immediately above the last granted agent.\n"
            "• If no requests are asserted, `grant` must be 4'b0000."
        ),
        "module_name": "arbiter_rr4",
        "ports": [
            {"name": "clk", "direction": "input", "width": "1-bit", "desc": "Clock"},
            {"name": "rst_n", "direction": "input", "width": "1-bit", "desc": "Active-low reset"},
            {"name": "req", "direction": "input", "width": "4-bit [3:0]", "desc": "Request lines"},
            {"name": "grant", "direction": "output", "width": "4-bit [3:0]", "desc": "One-hot grant lines"}
        ],
        "interface": (
            "module arbiter_rr4(\n"
            "    input  logic       clk,\n"
            "    input  logic       rst_n,\n"
            "    input  logic [3:0] req,\n"
            "    output logic [3:0] grant\n"
            ");"
        ),
        "starter_files": {
            "arbiter_rr4.sv": (
                "module arbiter_rr4(\n"
                "    input  logic       clk,\n"
                "    input  logic       rst_n,\n"
                "    input  logic [3:0] req,\n"
                "    output logic [3:0] grant\n"
                ");\n\n"
                "    // TODO: Maintain 2-bit or one-hot priority pointer updated on each granted cycle\n"
                "    // TODO: Combinationally arbitrate based on current round-robin priority\n"
                "    // TODO: Output exact one-hot grant vector (or 0000 if no req)\n\n"
                "endmodule\n"
            )
        },
        "testbench": r"""
`timescale 1ns/1ps
module tb;
    logic clk = 0;
    logic rst_n = 0;
    logic [3:0] req = 0;
    logic [3:0] grant;

    arbiter_rr4 dut (.clk(clk), .rst_n(rst_n), .req(req), .grant(grant));
    always #5 clk = ~clk;

    task report_test(input [63:0] t_id, input [255:0] t_name, input passed, input [255:0] detail, input [31:0] t_time, input is_hidden);
        begin
            if (passed)
                $display("::TEST::%0s::%0s::PASSED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
            else
                $display("::TEST::%0s::%0s::FAILED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
        end
    endtask

    initial begin
        $dumpfile("wave.vcd");
        $dumpvars(0, tb);

        // Reset check
        rst_n = 0; @(posedge clk); #1;
        rst_n = 1;
        if (grant === 4'b0000) report_test("tc_01", "Reset State Zero Grant", 1, "grant=0000", $time, 0);
        else report_test("tc_01", "Reset State Zero Grant", 0, "grant not 0", $time, 0);

        // Single request on channel 2
        req = 4'b0100; #2;
        if (grant === 4'b0100) report_test("tc_02", "Single Agent Grant", 1, "grant=0100", $time, 0);
        else report_test("tc_02", "Single Agent Grant", 0, "wrong grant", $time, 0);

        // Advance clock and assert all requests to test round-robin fairness
        @(posedge clk); #1; // channel 2 was granted, next priority starts at channel 3
        req = 4'b1111; #2;
        if (grant === 4'b1000) report_test("tc_03", "RR Rotation to Channel 3", 1, "Channel 3 granted", $time, 1);
        else report_test("tc_03", "RR Rotation to Channel 3", 0, "Wrong rotation", $time, 1);

        @(posedge clk); #1;
        if (grant === 4'b0001) report_test("tc_04", "RR Wraparound to Channel 0", 1, "Channel 0 granted", $time, 1);
        else report_test("tc_04", "RR Wraparound to Channel 0", 0, "Wrong wrap", $time, 1);

        #10; $finish;
    end
endmodule
""",
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Double Priority Trick",
                "text": "A standard hardware arbiter replicates requests `{req, req}` and masks by `{mask, mask}` to achieve O(1) single-cycle round-robin arbitration without loops."
            }
        ],
        "explanation": "Round-robin arbiters maintain a pointer to the highest priority channel. By shifting the request vector by the pointer, standard priority encoder logic can be reused cleanly.",
        "solution": {
            "cost": 1,
            "title": "4-way Round-Robin Arbiter in SystemVerilog",
            "overview": "Round-robin arbiter maintaining rotating priority pointer to ensure starvation-free scheduling.",
            "canonical_code": {
                "arbiter_rr4.sv": (
                    "module arbiter_rr4(\n"
                    "    input  logic       clk,\n"
                    "    input  logic       rst_n,\n"
                    "    input  logic [3:0] req,\n"
                    "    output logic [3:0] grant\n"
                    ");\n\n"
                    "    logic [1:0] ptr;\n\n"
                    "    always_comb begin\n"
                    "        grant = 4'b0000;\n"
                    "        if (req != 4'b0000) begin\n"
                    "            case (ptr)\n"
                    "                2'd0: begin\n"
                    "                    if (req[0])      grant = 4'b0001;\n"
                    "                    else if (req[1]) grant = 4'b0010;\n"
                    "                    else if (req[2]) grant = 4'b0100;\n"
                    "                    else if (req[3]) grant = 4'b1000;\n"
                    "                end\n"
                    "                2'd1: begin\n"
                    "                    if (req[1])      grant = 4'b0010;\n"
                    "                    else if (req[2]) grant = 4'b0100;\n"
                    "                    else if (req[3]) grant = 4'b1000;\n"
                    "                    else if (req[0]) grant = 4'b0001;\n"
                    "                end\n"
                    "                2'd2: begin\n"
                    "                    if (req[2])      grant = 4'b0100;\n"
                    "                    else if (req[3]) grant = 4'b1000;\n"
                    "                    else if (req[0]) grant = 4'b0001;\n"
                    "                    else if (req[1]) grant = 4'b0010;\n"
                    "                end\n"
                    "                2'd3: begin\n"
                    "                    if (req[3])      grant = 4'b1000;\n"
                    "                    else if (req[0]) grant = 4'b0001;\n"
                    "                    else if (req[1]) grant = 4'b0010;\n"
                    "                    else if (req[2]) grant = 4'b0100;\n"
                    "                end\n"
                    "            endcase\n"
                    "        end\n"
                    "    end\n\n"
                    "    always_ff @(posedge clk) begin\n"
                    "        if (!rst_n) begin\n"
                    "            ptr <= 2'd0;\n"
                    "        end else if (|grant) begin\n"
                    "            case (grant)\n"
                    "                4'b0001: ptr <= 2'd1;\n"
                    "                4'b0010: ptr <= 2'd2;\n"
                    "                4'b0100: ptr <= 2'd3;\n"
                    "                4'b1000: ptr <= 2'd0;\n"
                    "                default: ptr <= ptr;\n"
                    "            endcase\n"
                    "        end\n"
                    "    end\n\n"
                    "endmodule\n"
                )
            }
        },
        "source_metadata": {
            "source": "HDL Arena Curated Library",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Standard high-performance on-chip bus arbiter."
        },
        "test_suite_version": "1.0.0"
    },

    # Conceptual / Interview Scenario - CDC FIFO Architecture
    "interview_cdc_fifo": {
        "id": "interview_cdc_fifo",
        "title": "Interview Scenario: Multi-Gigabit Asynchronous CDC FIFO Design",
        "topic": "Clock Domain Crossing (CDC)",
        "category": "Clock Domain Crossing (CDC)",
        "difficulty": "Advanced",
        "language": "verilog",
        "type": "interview_scenario",
        "tags": ["CDC", "Gray Code", "Async FIFO", "SystemVerilog", "Interview"],
        "description": (
            "You are in a Principal Hardware Engineer interview at a high-speed networking semiconductor firm.\n"
            "The interviewer asks:\n"
            "'Architect an Asynchronous CDC FIFO bridging a 133 MHz Write Domain (Memory Controller) and a 400 MHz Read Domain (Packet Engine).\n"
            "Explain:\n"
            "1. Why binary pointers cannot be directly passed across the clock domains and how Gray codes resolve this.\n"
            "2. How the FIFO Full condition is generated in the Write Domain.\n"
            "3. How the FIFO Empty condition is generated in the Read Domain.\n"
            "4. Why pointer synchronization latency causes pessimistic, but safe, full/empty detection.'"
        ),
        "rubric_criteria": [
            {
                "criterion": "Gray Code Pointer Rationale",
                "points": 25,
                "keywords": ["gray code", "single bit", "multi-bit", "metastability", "glitch", "bus skew"],
                "desc": "Explains that multi-bit binary counter transitions flip multiple bits simultaneously (e.g. 0111 -> 1000), which due to wire skew can be sampled as erratic intermediate states; Gray code guarantees only 1 bit flips per transition."
            },
            {
                "criterion": "Full Condition Logic",
                "points": 25,
                "keywords": ["full", "write domain", "msb", "second msb", "inversion", "synchronized read pointer"],
                "desc": "Specifies that Full is computed in the write clock domain when the write pointer catches up to the synchronized read pointer after a complete wraparound (MSB and 2nd MSB inverted, lower bits identical in Gray code)."
            },
            {
                "criterion": "Empty Condition Logic",
                "points": 25,
                "keywords": ["empty", "read domain", "identical", "equal", "synchronized write pointer"],
                "desc": "Specifies that Empty is computed in the read clock domain when the read Gray pointer exactly equals the synchronized write Gray pointer."
            },
            {
                "criterion": "Safe Pessimism Explanation",
                "points": 25,
                "keywords": ["pessimistic", "safe", "latency", "conservative", "underflow", "overflow"],
                "desc": "Clarifies that due to 2-stage synchronizer delay, the write domain sees an older read pointer (FIFO appears fuller than it actually is), and the read domain sees an older write pointer (FIFO appears emptier than it actually is), preventing both overflow and underflow."
            }
        ],
        "model_answer": (
            "1. Gray Code: Binary pointers flip multiple bits concurrently (e.g. 3'b011 to 3'b100 flips 3 bits). "
            "Due to interconnect delay differences, the receiving domain could sample an arbitrary invalid intermediate value. "
            "Gray code ensures exactly one bit changes per clock cycle, so 2-FF synchronizers can never produce multi-bit corrupted values.\n\n"
            "2. Full Condition: Evaluated in the Write Domain. With an (N+1)-bit Gray pointer for depth 2^N, FIFO is Full when "
            "the write pointer wraps around: the top two MSBs are inverted (`wr_gray[N] != rd_gray_sync[N]` and `wr_gray[N-1] != rd_gray_sync[N-1]`) "
            "while all lower bits match (`wr_gray[N-2:0] == rd_gray_sync[N-2:0]`).\n\n"
            "3. Empty Condition: Evaluated in the Read Domain. The FIFO is Empty when the read Gray pointer exactly matches "
            "the synchronized write Gray pointer (`rd_gray == wr_gray_sync`).\n\n"
            "4. Safe Pessimism: The 2-stage synchronizer introduces 2 clock cycles of latency. "
            "The write domain receives read pointer updates late, so the FIFO may report Full even though the reader has already popped data. "
            "Similarly, the read domain receives write pointer updates late, so the FIFO may report Empty even though new data was written. "
            "This conservatism never causes overflow or underflow; it only temporarily limits throughput, making the design robust and fail-safe."
        ),
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Interview Structure",
                "text": "Structure your response into 4 concise headings matching the 4 technical questions."
            }
        ],
        "source_metadata": {
            "source": "HDL Arena Interview Bank",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Foundational VLSI CDC FIFO interview rubric."
        },
        "test_suite_version": "1.0.0"
    },

    # =========================================================================
    # 4. EXPERT LEVEL
    # =========================================================================

    # Verilog - Bus Protocol (Existing APB Slave GPIO)
    "apb_slave_gpio": {
        "id": "apb_slave_gpio",
        "title": "AMBA APB 32-bit Slave GPIO Controller",
        "topic": "Bus Protocols such as APB, AXI and AHB",
        "category": "Bus Protocols such as APB, AXI and AHB",
        "difficulty": "Expert",
        "language": "verilog",
        "type": "coding",
        "tags": ["Bus Protocols", "APB", "AMBA", "Memory-Mapped IO"],
        "description": (
            "Design an AMBA Advanced Peripheral Bus (APB) 32-bit slave peripheral with two 32-bit registers:\n"
            "• Address 32'h00: Data Output Register (R/W) driving 'gpio_out'.\n"
            "• Address 32'h04: Data Input Register (Read-only) reflecting 'gpio_in'.\n\n"
            "APB Handshake Protocol:\n"
            "1. Setup Phase: 'psel' asserted, 'penable' deasserted.\n"
            "2. Access Phase: 'penable' asserted. Complete read or write when 'penable && psel'.\n"
            "3. 'pready' must be asserted (always 1'b1 for 0-wait-state slave).\n"
            "4. For read transactions ('!pwrite'), 'prdata' provides registered data during access phase."
        ),
        "requirements": [
            "Conform strictly to AMBA APB protocol specifications.",
            "Write occurs only when psel && penable && pwrite.",
            "Always return pready = 1."
        ],
        "constraints": ["Data bus: 32 bits, Address bus: 32 bits."],
        "module_name": "apb_slave_gpio",
        "ports": [
            {"name": "pclk", "direction": "input", "width": "1-bit", "desc": "APB clock"},
            {"name": "presetn", "direction": "input", "width": "1-bit", "desc": "Active-low APB reset"},
            {"name": "psel", "direction": "input", "width": "1-bit", "desc": "Peripheral select"},
            {"name": "penable", "direction": "input", "width": "1-bit", "desc": "Transfer strobe"},
            {"name": "pwrite", "direction": "input", "width": "1-bit", "desc": "Write (1) / Read (0)"},
            {"name": "paddr", "direction": "input", "width": "32-bit [31:0]", "desc": "Byte address"},
            {"name": "pwdata", "direction": "input", "width": "32-bit [31:0]", "desc": "Write data"},
            {"name": "prdata", "direction": "output", "width": "32-bit [31:0]", "desc": "Read data"},
            {"name": "pready", "direction": "output", "width": "1-bit", "desc": "Slave ready"},
            {"name": "gpio_in", "direction": "input", "width": "32-bit [31:0]", "desc": "External GPIO inputs"},
            {"name": "gpio_out", "direction": "output", "width": "32-bit [31:0]", "desc": "External GPIO outputs"}
        ],
        "interface": (
            "module apb_slave_gpio(\n"
            "    input  wire        pclk,\n"
            "    input  wire        presetn,\n"
            "    input  wire        psel,\n"
            "    input  wire        penable,\n"
            "    input  wire        pwrite,\n"
            "    input  wire [31:0] paddr,\n"
            "    input  wire [31:0] pwdata,\n"
            "    output reg  [31:0] prdata,\n"
            "    output wire        pready,\n"
            "    input  wire [31:0] gpio_in,\n"
            "    output reg  [31:0] gpio_out\n"
            ");"
        ),
        "starter_files": {
            "apb_slave_gpio.v": (
                "module apb_slave_gpio(\n"
                "    input  wire        pclk,\n"
                "    input  wire        presetn,\n"
                "    input  wire        psel,\n"
                "    input  wire        penable,\n"
                "    input  wire        pwrite,\n"
                "    input  wire [31:0] paddr,\n"
                "    input  wire [31:0] pwdata,\n"
                "    output reg  [31:0] prdata,\n"
                "    output wire        pready,\n"
                "    input  wire [31:0] gpio_in,\n"
                "    output reg  [31:0] gpio_out\n"
                ");\n\n"
                "    // TODO: Tie pready high for zero-wait-state transfers.\n"
                "    // TODO: Handle APB write transfers (psel && penable && pwrite) to Addr 0x00 (gpio_out).\n"
                "    // TODO: Handle APB read transfers (psel && !pwrite) from Addr 0x00 and 0x04 (gpio_in).\n"
                "    // TODO: Handle asynchronous active-low reset on presetn.\n\n"
                "endmodule\n"
            )
        },
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Protocol Phases",
                "text": "Remember that write operations in APB commit on the posedge pclk during the ACCESS phase, which is when `psel && penable && pwrite` are all asserted."
            },
            {
                "index": 1,
                "cost": 0.5,
                "title": "Address Decoding",
                "text": "Decode `paddr[3:0]`: 4'h0 maps to `gpio_out`, and 4'h4 maps to `gpio_in`. Return 32'h0 for all unmapped addresses."
            }
        ],
        "hints": [
            "Tie pready = 1'b1 constantly.",
            "Write commits when psel && penable && pwrite is active."
        ],
        "explanation": "AMBA APB protocol requires 2 phases per transfer. The slave samples write data on posedge pclk when both psel and penable are asserted.",
        "source_metadata": {
            "source": "HDL Arena Curated Library",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Standard AMBA APB protocol slave."
        },
        "test_suite_version": "1.0.0",
        "reference_solution_policy": "Full canonical code available for 1.0 VJ Coin.",
        "testbench": r"""
`timescale 1ns/1ps
module tb;
    reg pclk = 0;
    reg presetn = 0;
    reg psel = 0;
    reg penable = 0;
    reg pwrite = 0;
    reg [31:0] paddr = 0;
    reg [31:0] pwdata = 0;
    wire [31:0] prdata;
    wire pready;
    reg [31:0] gpio_in = 0;
    wire [31:0] gpio_out;

    apb_slave_gpio dut (
        .pclk(pclk), .presetn(presetn), .psel(psel), .penable(penable),
        .pwrite(pwrite), .paddr(paddr), .pwdata(pwdata), .prdata(prdata),
        .pready(pready), .gpio_in(gpio_in), .gpio_out(gpio_out)
    );
    always #5 pclk = ~pclk;

    task report_test(input [63:0] t_id, input [255:0] t_name, input passed, input [255:0] detail, input [31:0] t_time, input is_hidden);
        begin
            if (passed)
                $display("::TEST::%0s::%0s::PASSED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
            else
                $display("::TEST::%0s::%0s::FAILED::%0s::%0dns::%0d", t_id, t_name, detail, t_time, is_hidden);
        end
    endtask

    task log_cycle(input [31:0] t_val, input [127:0] in_str, input [127:0] exp_str, input [127:0] act_str, input match);
        begin
            $display("::CYCLE::time=%0dns::inputs=%0s::expected=%0s::actual=%0s::match=%0d::time_num=%0d",
                     t_val, in_str, exp_str, act_str, match, t_val);
        end
    endtask

    reg sample_mode;

    initial begin
        sample_mode = $test$plusargs("SAMPLE_ONLY");
        $dumpfile("wave.vcd");
        $dumpvars(0, tb);

        // TEST 1: Reset Check (Sample)
        presetn = 0; @(posedge pclk); #1;
        log_cycle($time, "presetn=0", "{gpio_out=0,pready=1}", $sformatf("{gpio_out=%0d,pready=%0d}", gpio_out, pready), (gpio_out === 32'd0 && pready === 1'b1));
        if (gpio_out === 32'd0 && pready === 1'b1)
            report_test("tc_01", "Active-low Reset clears GPIO out", 1, "gpio_out is 0 and pready is high", $time, 0);
        else report_test("tc_01", "Active-low Reset clears GPIO out", 0, "Reset failed", $time, 0);

        // TEST 2: APB Write to GPIO Out Register (Sample)
        presetn = 1;
        @(posedge pclk); #1;
        psel = 1; penable = 0; pwrite = 1; paddr = 32'h00; pwdata = 32'hDEADBEEF;
        @(posedge pclk); #1;
        penable = 1;
        @(posedge pclk); #1;
        psel = 0; penable = 0;
        log_cycle($time, "write 0xDEADBEEF", "gpio_out=0xDEADBEEF", $sformatf("gpio_out=0x%08X", gpio_out), (gpio_out === 32'hDEADBEEF));
        if (gpio_out === 32'hDEADBEEF)
            report_test("tc_02", "APB Register Write (Addr 0x00)", 1, "Data written to gpio_out", $time, 0);
        else report_test("tc_02", "APB Register Write (Addr 0x00)", 0, "Write failed", $time, 0);

        if (sample_mode) begin
            #10; $finish;
        end

        // TEST 3: APB Read from GPIO In (Hidden)
        gpio_in = 32'hCAFE1234;
        @(posedge pclk); #1;
        psel = 1; penable = 0; pwrite = 0; paddr = 32'h04;
        @(posedge pclk); #1;
        penable = 1; #1;
        log_cycle($time, "read Addr 0x04", "prdata=0xCAFE1234", $sformatf("prdata=0x%08X", prdata), (prdata === 32'hCAFE1234));
        if (prdata === 32'hCAFE1234)
            report_test("tc_03", "APB Register Read (Addr 0x04)", 1, "Read external GPIO input accurately", $time, 1);
        else report_test("tc_03", "APB Register Read (Addr 0x04)", 0, "Read failed", $time, 1);

        // TEST 4: Readback of GPIO Out (Hidden)
        @(posedge pclk); #1;
        psel = 1; penable = 0; pwrite = 0; paddr = 32'h00;
        @(posedge pclk); #1;
        penable = 1; #1;
        log_cycle($time, "read Addr 0x00", "prdata=0xDEADBEEF", $sformatf("prdata=0x%08X", prdata), (prdata === 32'hDEADBEEF));
        if (prdata === 32'hDEADBEEF)
            report_test("tc_04", "APB Readback Verification", 1, "Read back written value from Addr 0x00", $time, 1);
        else report_test("tc_04", "APB Readback Verification", 0, "Readback failed", $time, 1);

        #10; $finish;
    end
endmodule
""",
        "solution": {
            "cost": 1,
            "title": "AMBA APB v2.0 Memory-Mapped 32-bit GPIO Controller",
            "overview": "An AMBA APB slave peripheral responding to two 32-bit registers.",
            "canonical_code": {
                "apb_slave_gpio.v": (
                    "module apb_slave_gpio(\n"
                    "    input  wire        pclk,\n"
                    "    input  wire        presetn,\n"
                    "    input  wire        psel,\n"
                    "    input  wire        penable,\n"
                    "    input  wire        pwrite,\n"
                    "    input  wire [31:0] paddr,\n"
                    "    input  wire [31:0] pwdata,\n"
                    "    output reg  [31:0] prdata,\n"
                    "    output wire        pready,\n"
                    "    input  wire [31:0] gpio_in,\n"
                    "    output reg  [31:0] gpio_out\n"
                    ");\n\n"
                    "    assign pready = 1'b1;\n\n"
                    "    always @(posedge pclk or negedge presetn) begin\n"
                    "        if (!presetn) begin\n"
                    "            gpio_out <= 32'h00000000;\n"
                    "        end else if (psel && penable && pwrite && (paddr[3:0] == 4'h0)) begin\n"
                    "            gpio_out <= pwdata;\n"
                    "        end\n"
                    "    end\n\n"
                    "    always @(*) begin\n"
                    "        if (psel && !pwrite) begin\n"
                    "            case (paddr[3:0])\n"
                    "                4'h0: prdata = gpio_out;\n"
                    "                4'h4: prdata = gpio_in;\n"
                    "                default: prdata = 32'h00000000;\n"
                    "            endcase\n"
                    "        end else begin\n"
                    "            prdata = 32'h00000000;\n"
                    "        end\n"
                    "    end\n\n"
                    "endmodule\n"
                )
            }
        }
    },

    # Interview Scenario - AXI Interconnect Deadlock & Out-of-Order Hazards
    "interview_axi_interconnect": {
        "id": "interview_axi_interconnect",
        "title": "Interview Scenario: AXI4 Interconnect Deadlock & Out-of-Order Hazards",
        "topic": "Bus Protocols such as APB, AXI and AHB",
        "category": "Bus Protocols such as APB, AXI and AHB",
        "difficulty": "Expert",
        "language": "verilog",
        "type": "interview_scenario",
        "tags": ["AXI4", "Deadlock", "Out-of-Order", "Interconnect", "Interview"],
        "description": (
            "During a Lead SoC Architect interview, you are asked:\n\n"
            "'In an AXI4 multi-master, multi-slave crossbar interconnect supporting out-of-order responses with ID tagging:\n"
            "1. Explain how circular dependencies can cause bus protocol deadlock when transactions with identical AXI IDs target different slave endpoints.\n"
            "2. What is the AXI ordering rule regarding requests with the same ID vs requests with different IDs?\n"
            "3. How does the interconnect prevent slave deadlock when master A sends transactions with ID=0 to Slave 1 and Slave 2 concurrently?\n"
            "4. How do AXI4 read and write response channels (R/B) maintain ordering without head-of-line blocking?'"
        ),
        "rubric_criteria": [
            {
                "criterion": "AXI ID Ordering Rule",
                "points": 25,
                "keywords": ["same id", "different id", "in order", "out of order", "independent"],
                "desc": "Correctly states that transactions with the SAME ID MUST be returned in order, whereas transactions with DIFFERENT IDs have no ordering requirement and can be reordered freely."
            },
            {
                "criterion": "Circular Deadlock Mechanism",
                "points": 25,
                "keywords": ["deadlock", "head of line", "buffer", "interconnect", "stall", "circular dependency"],
                "desc": "Explains that if a master issues ID=1 to Slave A then ID=1 to Slave B, the interconnect must return Slave A's response before Slave B's. If Slave B's response fills the interconnect buffer while Slave A is delayed, Slave B blocks Slave A, creating a deadlock."
            },
            {
                "criterion": "ID Prepend / Remapping in Interconnect",
                "points": 25,
                "keywords": ["id append", "id prepend", "master id", "remapping", "unique id", "sideband"],
                "desc": "Explains that interconnects prepend Master ID bits (`AxID_slave = {Master_ID, AxID_master}`) so that different masters using ID=0 cannot collide or cross-contaminate ordering restrictions."
            },
            {
                "criterion": "Head-of-Line Blocking Mitigation",
                "points": 25,
                "keywords": ["reorder buffer", "rob", "multiple id", "separate queues", "tag"],
                "desc": "Details how Reorder Buffers (ROBs) or separate ID queue trackers route out-of-order responses to bypass stalled queues when IDs differ."
            }
        ],
        "model_answer": (
            "1. AXI Ordering Rules: Transactions sharing the same ARID/AWID MUST complete and return responses strictly in the order they were issued. "
            "Transactions with different IDs have no ordering restriction and can complete out of order.\n\n"
            "2. Circular Dependency Deadlock: If Master M issues Tx1(ID=0) to slow Slave S1, then Tx2(ID=0) to fast Slave S2, "
            "the interconnect is strictly forbidden from returning Tx2 before Tx1. If S2 finishes first and pushes its response into the interconnect's "
            "response buffer until it is full, S2's pending response blocks the interconnect crossbar. If S1 requires the crossbar to complete its transfer, "
            "a circular dependency deadlock occurs.\n\n"
            "3. Interconnect Protection: Interconnects resolve this either by: (a) Enforcing single-slave routing per ID (stalling Tx2 at the master interface until Tx1 completes), "
            "or (b) Assigning internal tracking tags so responses can be held in a Reorder Buffer (ROB) until the earlier transaction from S1 commits.\n\n"
            "4. Multi-Master ID Isolation: When multiple masters use the same ID, the interconnect prepends the master's unique port index: "
            "`ARID_interconnect = {Master_Port_ID, ARID_master}`, ensuring complete isolation of ordering domains."
        ),
        "progressive_hints": [
            {
                "index": 0,
                "cost": 0.0,
                "title": "Core AXI Rule",
                "text": "Start by stating the cardinal rule of AXI4: Transactions with the same ID must be delivered in order; transactions with different IDs may be delivered in any order."
            }
        ],
        "source_metadata": {
            "source": "HDL Arena Interview Bank",
            "author": "HDL Arena Engineering Team",
            "license": "MIT",
            "attribution": "Advanced AMBA AXI4 interconnect verification and architecture interview scenario."
        },
        "test_suite_version": "1.0.0"
    }
}

# Dynamically merge validated imported questions from the license-aware catalog
try:
    from importer import IMPORTED_QUESTIONS_CATALOG
    for _iq in IMPORTED_QUESTIONS_CATALOG:
        if _iq["id"] not in QUESTIONS_REGISTRY:
            QUESTIONS_REGISTRY[_iq["id"]] = _iq
except Exception:
    pass

# Dynamically merge original generated questions across target curriculum topics
try:
    from content_generator import ORIGINAL_QUESTIONS_BATCH
    for _oq in ORIGINAL_QUESTIONS_BATCH:
        if _oq["id"] not in QUESTIONS_REGISTRY:
            QUESTIONS_REGISTRY[_oq["id"]] = _oq
except Exception:
    pass

# 100% Backward compatibility alias for legacy imports
PROBLEMS_REGISTRY = QUESTIONS_REGISTRY
