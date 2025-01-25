package main

import (
	"bufio"
	"flag"
	"fmt"
	"github.com/PuerkitoBio/goquery"
	"github.com/fatih/color"
	"io"
	"log"
	"net"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"sync"
	"syscall"
	"time"
)

// Configuration constants
const (
	UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
		"AppleWebKit/537.36 (KHTML, like Gecko) " +
		"Chrome/112.0.0.0 Safari/537.36"
	LogFormat = "%s - %s - %s (%s:%d)"
)

// Log levels
const (
	DEBUG = iota
	INFO
	WARNING
	ERROR
	CRITICAL
)

// Logger with color support
type Logger struct {
	mu       sync.Mutex
	logFile  *os.File
	logLevel int
	useColor bool
}

func NewLogger(filePath string, level int, useColor bool) (*Logger, error) {
	file, err := os.OpenFile(filePath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return nil, err
	}
	return &Logger{
		logFile:  file,
		logLevel: level,
		useColor: useColor,
	}, nil
}

func (l *Logger) logf(level int, levelStr, msg string, file string, line int) {
	if level < l.logLevel {
		return
	}

	l.mu.Lock()
	defer l.mu.Unlock()

	formatted := fmt.Sprintf(LogFormat, time.Now().Format(time.RFC3339), levelStr, msg, filepath.Base(file), line)
	// Write to log file
	fmt.Fprintln(l.logFile, formatted)

	// Write to console with colors
	if l.useColor {
		switch level {
		case DEBUG:
			color.Cyan(formatted)
		case INFO:
			color.Green(formatted)
		case WARNING:
			color.Yellow(formatted)
		case ERROR:
			color.Red(formatted)
		case CRITICAL:
			color.Magenta(formatted)
		default:
			fmt.Println(formatted)
		}
	} else {
		fmt.Println(formatted)
	}
}

func (l *Logger) Debug(msg string, file string, line int) {
	l.logf(DEBUG, "DEBUG", msg, file, line)
}

func (l *Logger) Info(msg string, file string, line int) {
	l.logf(INFO, "INFO", msg, file, line)
}

func (l *Logger) Warning(msg string, file string, line int) {
	l.logf(WARNING, "WARNING", msg, file, line)
}

func (l *Logger) Error(msg string, file string, line int) {
	l.logf(ERROR, "ERROR", msg, file, line)
}

func (l *Logger) Critical(msg string, file string, line int) {
	l.logf(CRITICAL, "CRITICAL", msg, file, line)
}

func (l *Logger) Close() {
	l.logFile.Close()
}

// UsernameChecker struct
type UsernameChecker struct {
	usernames   []string
	threads     int
	proxies     []string
	logger      *Logger
	outputFile  string
	client      *http.Client
	resultsMu   sync.Mutex
	results     []string
	processed   int
	processedMu sync.Mutex
	stopChan    chan struct{}
	wg          sync.WaitGroup
}

func NewUsernameChecker(usernames []string, threads int, proxies []string, logger *Logger, outputFile string) *UsernameChecker {
	client := &http.Client{
		Timeout: 10 * time.Second,
	}
	if len(proxies) > 0 {
		proxyURL, err := url.Parse(proxies[0]) // Using the first proxy
		if err == nil {
			client.Transport = &http.Transport{
				Proxy: http.ProxyURL(proxyURL),
				DialContext: (&net.Dialer{
					Timeout:   10 * time.Second,
					KeepAlive: 10 * time.Second,
				}).DialContext,
			}
		}
	}
	return &UsernameChecker{
		usernames:  usernames,
		threads:    threads,
		proxies:    proxies,
		logger:     logger,
		outputFile: outputFile,
		client:     client,
		stopChan:   make(chan struct{}),
	}
}

func (uc *UsernameChecker) Run() {
	uc.logger.Info(fmt.Sprintf("Starting check for %d usernames with %d threads.", len(uc.usernames), uc.threads), "main.go", 0)
	sem := make(chan struct{}, uc.threads)

	for _, username := range uc.usernames {
		select {
		case <-uc.stopChan:
			uc.logger.Warning("Received stop signal. Exiting...", "main.go", 0)
			return
		default:
			sem <- struct{}{}
			uc.wg.Add(1)
			go func(u string) {
				defer uc.wg.Done()
				uc.checkUsername(u)
				<-sem
			}(username)
		}
	}

	uc.wg.Wait()
	uc.logger.Info("Username checking completed.", "main.go", 0)
}

func (uc *UsernameChecker) checkUsername(username string) {
	username = strings.TrimSpace(strings.TrimPrefix(username, "@"))
	url := fmt.Sprintf("https://fragment.com/username/%s", username)

	uc.logger.Debug(fmt.Sprintf("Sending request for %s to URL: %s", username, url), "main.go", 0)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		uc.logResult(fmt.Sprintf("@%s | Error: %v\n", username, err))
		uc.logger.Error(fmt.Sprintf("Error creating request for %s: %v", username, err), "main.go", 0)
		uc.incrementProcessed()
		return
	}
	req.Header.Set("User-Agent", UserAgent)
	req.Header.Set("Accept-Language", "en-US,en;q=0.9")
	req.Header.Set("Accept-Encoding", "gzip, deflate")
	req.Header.Set("Connection", "keep-alive")

	resp, err := uc.client.Do(req)
	if err != nil {
		uc.logResult(fmt.Sprintf("@%s | Error: %v\n", username, err))
		uc.logger.Error(fmt.Sprintf("Request error for %s: %v", username, err), "main.go", 0)
		uc.incrementProcessed()
		return
	}
	defer resp.Body.Close()

	finalURL := resp.Request.URL.String()
	uc.logger.Debug(fmt.Sprintf("Received response from URL: %s for %s", finalURL, username), "main.go", 0)

	if finalURL == fmt.Sprintf("https://fragment.com/?query=%s", username) {
		result := fmt.Sprintf("@%s | Free\n", username)
		uc.logResult(result)
		uc.logger.Info(strings.TrimSpace(result), "main.go", 0)
	} else {
		// Parse HTML to find status
		doc, err := goquery.NewDocumentFromReader(resp.Body)
		if err != nil {
			uc.logResult(fmt.Sprintf("@%s | Error parsing HTML: %v\n", username, err))
			uc.logger.Error(fmt.Sprintf("HTML parsing error for %s: %v", username, err), "main.go", 0)
			uc.incrementProcessed()
			return
		}

		statusSpan := doc.Find("span.tm-section-header-status")
		if statusSpan.Length() > 0 {
			status := strings.ToLower(strings.TrimSpace(statusSpan.Text()))
			var result string
			switch status {
			case "sold", "available", "taken":
				statusCap := strings.Title(status)
				result = fmt.Sprintf("@%s | %s\n", username, statusCap)
			default:
				result = fmt.Sprintf("@%s | Unknown status (%s)\n", username, status)
			}
			uc.logResult(result)
			if strings.HasPrefix(result, "@"+username+" | Unknown") {
				uc.logger.Warning(strings.TrimSpace(result), "main.go", 0)
			} else {
				uc.logger.Info(strings.TrimSpace(result), "main.go", 0)
			}
		} else {
			result := fmt.Sprintf("@%s | Status not found\n", username)
			uc.logResult(result)
			uc.logger.Warning(strings.TrimSpace(result), "main.go", 0)
		}
	}

	uc.incrementProcessed()
}

func (uc *UsernameChecker) logResult(result string) {
	uc.resultsMu.Lock()
	defer uc.resultsMu.Unlock()
	uc.results = append(uc.results, result)
	err := appendToFile(uc.outputFile, result)
	if err != nil {
		uc.logger.Error(fmt.Sprintf("Error writing to file: %v", err), "main.go", 0)
	}
}

func appendToFile(filePath, text string) error {
	f, err := os.OpenFile(filePath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = f.WriteString(text)
	return err
}

func (uc *UsernameChecker) incrementProcessed() {
	uc.processedMu.Lock()
	defer uc.processedMu.Unlock()
	uc.processed++
}

func (uc *UsernameChecker) GetProgress() (int, int, float64) {
	uc.processedMu.Lock()
	defer uc.processedMu.Unlock()
	total := len(uc.usernames)
	processed := uc.processed
	progress := (float64(processed) / float64(total)) * 100
	return processed, total, progress
}

func main() {
	// Command-line arguments
	inputPath := flag.String("input", "", "Path to the input file with usernames")
	outputPath := flag.String("output", "", "Path to the output file for results")
	threads := flag.Int("threads", 10, "Number of concurrent threads")
	proxies := flag.String("proxy", "", "Proxy servers in format scheme://user:pass@host:port (comma-separated for multiple)")
	logPath := flag.String("log", "username_checker.log", "Path to the log file")
	noColor := flag.Bool("no-color", false, "Disable colored output in logs")
	flag.Parse()

	// Validate required arguments
	if *inputPath == "" || *outputPath == "" {
		fmt.Println("Input and output file paths are required.")
		flag.Usage()
		os.Exit(1)
	}

	// Initialize logger
	logger, err := NewLogger(*logPath, DEBUG, !*noColor)
	if err != nil {
		log.Fatalf("Failed to initialize logger: %v", err)
	}
	defer logger.Close()

	// Parse proxies
	var proxyList []string
	if *proxies != "" {
		proxyList = strings.Split(*proxies, ",")
		logger.Info(fmt.Sprintf("Using proxies: %v", proxyList), "main.go", 0)
	}

	// Clear or create output file
	f, err := os.OpenFile(*outputPath, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0644)
	if err != nil {
		logger.Critical(fmt.Sprintf("Failed to clear output file %s: %v", *outputPath, err), "main.go", 0)
		os.Exit(1)
	}
	f.Close()

	// Read usernames from input file
	usernames, err := readLines(*inputPath)
	if err != nil {
		logger.Critical(fmt.Sprintf("Failed to read input file %s: %v", *inputPath, err), "main.go", 0)
		os.Exit(1)
	}
	logger.Info(fmt.Sprintf("Loaded %d usernames from %s.", len(usernames), *inputPath), "main.go", 0)

	// Initialize UsernameChecker
	checker := NewUsernameChecker(usernames, *threads, proxyList, logger, *outputPath)

	// Handle OS signals for graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		sig := <-sigChan
		logger.Warning(fmt.Sprintf("Received signal %s. Stopping...", sig), "main.go", 0)
		close(checker.stopChan)
	}()

	// Start progress updater
	done := make(chan struct{})
	go func() {
		ticker := time.NewTicker(1 * time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-ticker.C:
				processed, total, progress := checker.GetProgress()
				title := fmt.Sprintf("Username Checker - %d/%d (%.2f%%)", processed, total, progress)
				setWindowTitle(title)
			case <-done:
				return
			}
		}
	}()

	// Start timer
	startTime := time.Now()

	// Run the checker
	checker.Run()

	// Stop progress updater
	close(done)

	// Calculate elapsed time
	elapsed := time.Since(startTime)
	logger.Info(fmt.Sprintf("Execution time: %.2f seconds.", elapsed.Seconds()), "main.go", 0)

	// Final message
	logger.Info(fmt.Sprintf("Results saved to %s.", *outputPath), "main.go", 0)
}

// readLines reads a file and returns a slice of lines
func readLines(path string) ([]string, error) {
	var lines []string
	f, err := os.Open(path)
	if err != nil {
		return lines, err
	}
	defer f.Close()

	reader := bufio.NewReader(f)
	for {
		line, err := reader.ReadString('\n')
		line = strings.TrimSpace(line)
		if line != "" {
			lines = append(lines, line)
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			return lines, err
		}
	}
	return lines, nil
}

// setWindowTitle sets the terminal window title on Unix-like systems.
func setWindowTitle(title string) {
	// ANSI escape sequence to set the terminal title
	fmt.Printf("\033]0;%s\007", title)
}
