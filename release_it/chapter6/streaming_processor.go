package main

import (
	"bufio"
	"encoding/csv"
	"fmt"
	"io"
	"os"
	"time"
)

// BenchmarkResult holds timing information for benchmarks
type BenchmarkResult struct {
	Operation    string
	Iterations   int
	MinNs        int64
	MaxNs        int64
	AvgNs        int64
	TotalTimeMs  float64
}

// ❌ NAIVE APPROACH: Load everything into memory
// Problem: For large files, this will OOM kill your process
// At scale: This is the #1 cause of production incidents
func processFileNaive(filename string) error {
	// staff-level: This looks innocent but will fail at scale
	file, err := os.Open(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	// Load entire file into memory - DANGEROUS with large files
	// This allocates memory proportional to file size
	allData := make([]byte, 0, 1024*1024) // 1MB initial, will grow
	buf := make([]byte, 4096)
	for {
		n, err := file.Read(buf)
		if n > 0 {
			allData = append(allData, buf[:n]...)
		}
		if err != nil {
			break
		}
	}

	// Parse entire dataset into memory
	reader := csv.NewReader(stringReader(string(allData)))
	records, err := reader.ReadAll()
	if err != nil {
		return err
	}

	// Process all records - but they're already in memory!
	for _, record := range records {
		if err := processRecord(record); err != nil {
			return err
		}
	}

	return nil
}

// ✅ PRODUCTION APPROACH: Streaming with bounded memory
// Why: Memory stays constant regardless of file size
// Trade-off: Can't do operations that require full dataset
func processFileStream(filename string) error {
	file, err := os.Open(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	// staff-level: Buffered reading reduces syscalls
	// Buffer size should match typical I/O block size (4KB-64KB)
	scanner := bufio.NewScanner(file)

	// For very long lines, increase buffer
	const maxCapacity = 1024 * 1024 // 1MB max line
	buf := make([]byte, maxCapacity)
	scanner.Buffer(buf, maxCapacity)

	lineNum := 0
	for scanner.Scan() {
		lineNum++

		// Parse single line - only one line in memory at a time
		record, err := csv.NewReader(stringReader(scanner.Text())).Read()
		if err != nil {
			fmt.Printf("Error parsing line %d: %v\n", lineNum, err)
			continue
		}

		// Process immediately, don't store
		if err := processRecord(record); err != nil {
			fmt.Printf("Error processing line %d: %v\n", lineNum, err)
		}
	}

	if err := scanner.Err(); err != nil {
		return fmt.Errorf("error reading file: %w", err)
	}

	fmt.Printf("Processed %d lines\n", lineNum)
	return nil
}

// ✅ PRODUCTION APPROACH: Batch processing with memory limit
// Why: Allows aggregations while keeping memory bounded
// Trade-off: Slightly more complex, but handles large datasets safely
func processFileBatched(filename string, batchSize int) error {
	file, err := os.Open(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	reader := csv.NewReader(bufio.NewReader(file))

	// Pre-allocate batch with known capacity
	batch := make([][]string, 0, batchSize)
	lineNum := 0
	processed := 0

	for {
		record, err := reader.Read()
		if err == io.EOF {
			// Process final batch
			if len(batch) > 0 {
				if err := processBatch(batch); err != nil {
					return fmt.Errorf("error processing final batch: %w", err)
				}
			}
			break
		}
		if err != nil {
			fmt.Printf("Error parsing line %d: %v\n", lineNum, err)
			continue
		}

		lineNum++
		batch = append(batch, record)

		// Process batch when full
		if len(batch) >= batchSize {
			if err := processBatch(batch); err != nil {
				return fmt.Errorf("error processing batch: %w", err)
			}
			processed += len(batch)
			fmt.Printf("Processed %d records total\n", processed)

			// Clear batch but keep allocated memory (reuse)
			batch = batch[:0]
		}
	}

	fmt.Printf("Finished processing %d records\n", lineNum)
	return nil
}

// Benchmark streaming vs batch processing
func benchmarkProcessing(filename string) {
	fmt.Println("\n=== Processing Benchmark ===")

	// Benchmark streaming
	start := time.Now()
	if err := processFileStream(filename); err != nil {
		fmt.Printf("Streaming error: %v\n", err)
	}
	streamTime := time.Since(start)
	fmt.Printf("Streaming time: %v\n", streamTime)

	// Benchmark batched (1000 records per batch)
	start = time.Now()
	if err := processFileBatched(filename, 1000); err != nil {
		fmt.Printf("Batch error: %v\n", err)
	}
	batchTime := time.Since(start)
	fmt.Printf("Batch time: %v\n", batchTime)

	fmt.Printf("\nComparison: Batch is %.2fx %s than streaming\n",
		func() float64 {
			if streamTime < batchTime {
				return float64(batchTime) / float64(streamTime)
			}
			return float64(streamTime) / float64(batchTime)
		}(),
		func() string {
			if streamTime < batchTime {
				return "slower"
			}
			return "faster"
		}(),
	)
}

// processRecord handles a single record
func processRecord(record []string) error {
	// Simulate processing work
	// In real code, this might be validation, transformation, etc.
	if len(record) == 0 {
		return nil
	}
	return nil
}

// processBatch handles a batch of records
// Batch processing enables:
// - Bulk inserts to database
// - In-batch aggregations
// - More efficient I/O
func processBatch(batch [][]string) error {
	// Example: Bulk insert to database
	// return db.BulkInsert(batch)

	// For now, just process each record
	for _, record := range batch {
		if err := processRecord(record); err != nil {
			return err
		}
	}
	return nil
}

// Helper for string reader - converts string to io.Reader
type stringReader struct {
	s string
	i int
}

func stringReader(s string) *stringReader {
	return &stringReader{s: s}
}

func (r *stringReader) Read(p []byte) (n int, err error) {
	if r.i >= len(r.s) {
		return 0, io.EOF
	}
	n = copy(p, r.s[r.i:])
	r.i += n
	return n, nil
}

// Create a test file for benchmarking
func createTestFile(filename string, numLines int) error {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	writer := csv.NewWriter(file)

	// Write header
	writer.Write([]string{"id", "name", "email", "value"})

	// Write data
	for i := 0; i < numLines; i++ {
		writer.Write([]string{
			fmt.Sprintf("%d", i),
			fmt.Sprintf("name_%d", i),
			fmt.Sprintf("user_%d@example.com", i),
			fmt.Sprintf("%d", i*100),
		})
	}

	writer.Flush()
	return writer.Error()
}

func main() {
	// Create a small test file
	testFile := "test_data.csv"
	defer os.Remove(testFile)

	const numLines = 10000
	fmt.Printf("Creating test file with %d lines...\n", numLines)
	if err := createTestFile(testFile, numLines); err != nil {
		fmt.Printf("Error creating test file: %v\n", err)
		return
	}

	// Run benchmarks
	benchmarkProcessing(testFile)

	fmt.Println("\n=== Key Takeaways ===")
	fmt.Println("1. Streaming uses constant memory regardless of file size")
	fmt.Println("2. Batch processing allows aggregations while limiting memory")
	fmt.Println("3. Choose based on your use case:")
	fmt.Println("   - Streaming: when you only need to process once")
	fmt.Println("   - Batched: when you need bulk operations or in-batch analytics")
	fmt.Println("4. Always pre-allocate batches to avoid GC pressure")
}
