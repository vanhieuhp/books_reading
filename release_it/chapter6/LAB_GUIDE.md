# 🧪 Chapter 6: Foundations - Code Lab Guide

## Lab: Measuring System Latency

### 🎯 Goal

Build a benchmarking tool that measures actual latency of different operations on your system and compares them to the theoretical values from the chapter.

### ⏱ Time

~30-45 minutes

### 🛠 Requirements

- Go 1.18+ (or Python 3.8+)
- Access to local machine
- Terminal/command prompt

---

## Step 1: Setup

Create a new folder for your lab work:

```bash
mkdir -p ~/release_it_lab
cd ~/release_it_lab
```

Initialize a Go module (if using Go):

```bash
go mod init lab
```

---

## Step 2: Create the Benchmark Tool

### Option A: Go Implementation

Create `benchmark.go`:

```go
package main

import (
	"fmt"
	"math"
	"math/rand"
	"os"
	"time"
)

// BenchmarkResult holds timing information
type BenchmarkResult struct {
	Operation   string
	Iterations  int
	MinNs       int64
	MaxNs       int64
	AvgNs       int64
	P50Ns       int64
	P95Ns       int64
	P99Ns       int64
	TotalTimeMs float64
}

func main() {
	fmt.Println("╔══════════════════════════════════════════════════════════════╗")
	fmt.Println("║     Foundations Benchmark Lab - Measuring Latency         ║")
	fmt.Println("╚══════════════════════════════════════════════════════════════╝")
	fmt.Println()

	results := []*BenchmarkResult{}

	// 1. In-memory operation (baseline)
	results = append(results, benchmarkInMemory(1000000))

	// 2. Sequential file write
	results = append(results, benchmarkSequentialFileWrite(10000))

	// 3. Random file write
	results = append(results, benchmarkRandomFileWrite(1000))

	// Print results
	fmt.Println("\n╔══════════════════════════════════════════════════════════════╗")
	fmt.Println("║                      Results Summary                        ║")
	fmt.Println("╠══════════════════════════════════════════════════════════════╣")
	fmt.Printf("║ %-25s │ %10s │ %12s │ %8s ║\n", "Operation", "Avg", "P99", "Expected")
	fmt.Println("╠══════════════════════════════════════════════════════════════╣")

	for _, r := range results {
		expected := getExpected(r.Operation)
		fmt.Printf("║ %-25s │ %10s │ %12s │ %8s ║\n",
			r.Operation, formatDuration(r.AvgNs), formatDuration(r.P99Ns), expected)
	}
	fmt.Println("╚══════════════════════════════════════════════════════════════╝")

	fmt.Println("\n📊 Analysis:")
	fmt.Println("- Compare your results to the expected values from the chapter")
	fmt.Println("- If significantly different, investigate: disk type, system load")
}

func benchmarkInMemory(iterations int) *BenchmarkResult {
	data := make([]int, iterations)
	rand.Seed(time.Now().UnixNano())

	start := time.Now()
	for i := 0; i < iterations; i++ {
		data[i] = i * rand.Intn(100)
		_ = data[i]
	}
	elapsed := time.Since(start)

	perOp := elapsed.Nanoseconds() / int64(iterations)
	return &BenchmarkResult{
		Operation:   "In-memory loop",
		Iterations:  iterations,
		MinNs:       perOp,
		MaxNs:       perOp,
		AvgNs:       perOp,
		P50Ns:       perOp,
		P95Ns:       perOp,
		P99Ns:       perOp,
		TotalTimeMs: elapsed.Seconds() * 1000,
	}
}

func benchmarkSequentialFileWrite(iterations int) *BenchmarkResult {
	tmpfile, err := os.CreateTemp("", "bench_*.txt")
	if err != nil {
		return &BenchmarkResult{Operation: "Seq File Write", Iterations: iterations}
	}
	defer os.Remove(tmpfile.Name())
	tmpfile.Close()

	times := make([]int64, iterations)
	start := time.Now()

	for i := 0; i < iterations; i++ {
		t0 := time.Now()
		f, _ := os.OpenFile(tmpfile.Name(), os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
		if f != nil {
			_, _ = f.WriteString(fmt.Sprintf("line %d\n", i))
			f.Close()
		}
		times[i] = time.Since(t0).Nanoseconds()
	}
	totalTime := time.Since(start)

	os.Remove(tmpfile.Name())

	return &BenchmarkResult{
		Operation:   "Seq File Write",
		Iterations:  iterations,
		MinNs:       findMin(times),
		MaxNs:       findMax(times),
		AvgNs:       findAvg(times),
		P50Ns:       findPercentile(times, 50),
		P95Ns:       findPercentile(times, 95),
		P99Ns:       findPercentile(times, 99),
		TotalTimeMs: totalTime.Seconds() * 1000,
	}
}

func benchmarkRandomFileWrite(iterations int) *BenchmarkResult {
	tmpdir, _ := os.MkdirTemp("", "bench_random_*")
	defer os.RemoveAll(tmpdir)

	times := make([]int64, iterations)
	start := time.Now()

	for i := 0; i < iterations; i++ {
		t0 := time.Now()
		filename := fmt.Sprintf("%s/file_%d.txt", tmpdir, rand.Intn(100))
		f, _ := os.OpenFile(filename, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
		if f != nil {
			_, _ = f.WriteString(fmt.Sprintf("data %d\n", i))
			f.Close()
		}
		times[i] = time.Since(t0).Nanoseconds()
	}
	totalTime := time.Since(start)

	os.RemoveAll(tmpdir)

	return &BenchmarkResult{
		Operation:   "Random File Write",
		Iterations:  iterations,
		MinNs:       findMin(times),
		MaxNs:       findMax(times),
		AvgNs:       findAvg(times),
		P50Ns:       findPercentile(times, 50),
		P95Ns:       findPercentile(times, 95),
		P99Ns:       findPercentile(times, 99),
		TotalTimeMs: totalTime.Seconds() * 1000,
	}
}

func findMin(times []int64) int64 {
	min := times[0]
	for _, t := range times {
		if t < min {
			min = t
		}
	}
	return min
}

func findMax(times []int64) int64 {
	max := times[0]
	for _, t := range times {
		if t > max {
			max = t
		}
	}
	return max
}

func findAvg(times []int64) int64 {
	var sum int64
	for _, t := range times {
		sum += t
	}
	return sum / int64(len(times))
}

func findPercentile(times []int64, percentile int) int64 {
	if len(times) == 0 {
		return 0
	}
	sorted := make([]int64, len(times))
	copy(sorted, times)
	for i := 0; i < len(sorted); i++ {
		for j := i + 1; j < len(sorted); j++ {
			if sorted[i] > sorted[j] {
				sorted[i], sorted[j] = sorted[j], sorted[i]
			}
		}
	}
	index := int(math.Ceil(float64(len(sorted))*float64(percentile)/100)) - 1
	if index < 0 {
		index = 0
	}
	return sorted[index]
}

func formatDuration(ns int64) string {
	if ns < 1000 {
		return fmt.Sprintf("%d ns", ns)
	}
	if ns < 1000000 {
		return fmt.Sprintf("%.1f μs", float64(ns)/1000)
	}
	return fmt.Sprintf("%.2f ms", float64(ns)/1000000)
}

func getExpected(operation string) string {
	switch operation {
	case "In-memory loop":
		return "< 10 ns"
	case "Seq File Write":
		return "1-100 μs"
	case "Random File Write":
		return "1-10 ms"
	default:
		return "varies"
	}
}
```

### Option B: Python Implementation

Create `benchmark.py`:

```python
#!/usr/bin/env python3
"""Benchmark different system operations"""

import time
import tempfile
import os
import random
import statistics

def benchmark_in_memory(iterations=1000000):
    """Benchmark in-memory operations"""
    data = [0] * iterations
    start = time.perf_counter_ns()
    for i in range(iterations):
        data[i] = i * random.randint(0, 100)
    elapsed = time.perf_counter_ns() - start
    per_op = elapsed // iterations
    return {
        "operation": "In-memory loop",
        "avg_ns": per_op,
        "expected": "< 10 ns"
    }

def benchmark_sequential_write(iterations=10000):
    """Benchmark sequential file writes"""
    times = []
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        tmpfile = f.name

    try:
        for i in range(iterations):
            start = time.perf_counter_ns()
            with open(tmpfile, 'a') as f:
                f.write(f"line {i}\n")
            elapsed = time.perf_counter_ns() - start
            times.append(elapsed)
    finally:
        os.remove(tmpfile)

    return {
        "operation": "Seq File Write",
        "avg_ns": statistics.mean(times),
        "p99_ns": sorted(times)[int(len(times) * 0.99)],
        "expected": "1-100 μs"
    }

def benchmark_random_write(iterations=1000):
    """Benchmark random file writes"""
    tmpdir = tempfile.mkdtemp()
    times = []

    try:
        for i in range(iterations):
            filename = os.path.join(tmpdir, f"file_{random.randint(0, 99)}.txt")
            start = time.perf_counter_ns()
            with open(filename, 'a') as f:
                f.write(f"data {i}\n")
            elapsed = time.perf_counter_ns() - start
            times.append(elapsed)
    finally:
        import shutil
        shutil.rmtree(tmpdir)

    return {
        "operation": "Random File Write",
        "avg_ns": statistics.mean(times),
        "p99_ns": sorted(times)[int(len(times) * 0.99)],
        "expected": "1-10 ms"
    }

def format_ns(ns):
    """Format nanoseconds to human readable"""
    if ns < 1000:
        return f"{ns} ns"
    elif ns < 1000000:
        return f"{ns/1000:.1f} μs"
    else:
        return f"{ns/1000000:.2f} ms"

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     Foundations Benchmark Lab - Measuring Latency           ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    results = []
    results.append(benchmark_in_memory())
    results.append(benchmark_sequential_write())
    results.append(benchmark_random_write())

    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║                      Results Summary                        ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║ {'Operation':<25} │ {'Avg':>10} │ {'P99':>12} │ {'Expected':<8} ║")
    print("╠══════════════════════════════════════════════════════════════╣")

    for r in results:
        avg = format_ns(r["avg_ns"])
        p99 = format_ns(r.get("p99_ns", r["avg_ns"]))
        expected = r["expected"]
        print(f"║ {r['operation']:<25} │ {avg:>10} │ {p99:>12} │ {expected:<8} ║")

    print("╚══════════════════════════════════════════════════════════════╝")

    print("\n📊 Analysis:")
    print("- Compare your results to the expected values from the chapter")
    print("- If significantly different, investigate: disk type, system load")

if __name__ == '__main__':
    main()
```

---

## Step 3: Run the Benchmark

### Go
```bash
go run benchmark.go
```

### Python
```bash
python benchmark.py
```

---

## Step 4: Analyze Results

Expected output:

```
╔══════════════════════════════════════════════════════════════╗
║     Foundations Benchmark Lab - Measuring Latency           ║
╚══════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════╗
║                      Results Summary                        ║
╠══════════════════════════════════════════════════════════════╣
║ Operation                  │      Avg │         P99 │ Expected ║
╠══════════════════════════════════════════════════════════════╣
║ In-memory loop            │    5 ns  │        5 ns │ < 10 ns  ║
║ Seq File Write            │  12.5 μs │      150 μs │ 1-100 μs ║
║ Random File Write        │   2.5 ms │         8 ms │ 1-10 ms  ║
╚══════════════════════════════════════════════════════════════╝
```

### Questions to Answer:

1. **In-memory loop**: Is it under 10ns? (If slower, your CPU might be thermal throttling or under load)

2. **Sequential write**: Is it in the microsecond range? (If in milliseconds, you might be on HDD)

3. **Random write**: Is it under 10ms? (If over, investigate disk type and filesystem)

---

## Step 5: Stretch Challenges

### Challenge 1: Add Network Benchmark
Create a simple HTTP server and measure:
- Connection setup time
- Request/response latency
- Compare HTTP/1.1 vs HTTP/2

### Challenge 2: Memory Cache Benchmark
Compare:
- In-memory access vs file access
- Hot cache vs cold cache
- Different data structures

### Challenge 3: Batch Operations
Compare:
- 1000 individual writes vs 1 batch of 1000
- Measure the improvement

---

## 📝 Lab Summary

In this lab, you:

1. ✅ Created a benchmark tool to measure actual system latency
2. ✅ Compared results to theoretical values from the chapter
3. ✅ Identified factors that affect performance (disk type, system load)
4. ✅ Applied knowledge of latency hierarchy to interpret results

### Key Takeaways

- **Latency varies widely**: From nanoseconds (cache) to milliseconds (disk)
- **Your results may differ**: Hardware, OS, and system load all affect measurements
- **Order of magnitude matters**: Don't optimize what doesn't matter
- **Measure, don't guess**: Always benchmark your specific environment

---

*Lab Guide - Release It! Chapter 6: Foundations*
