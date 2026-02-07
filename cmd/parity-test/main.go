// Package main implements the parity test runner that validates API behavior across services.
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

// Scenario defines a single test case pointing at an API endpoint.
type Scenario struct {
	Name     string       `json:"name"`
	Request  RequestSpec  `json:"request"`
	Response ResponseSpec `json:"response"`
}

// RequestSpec describes the HTTP request parameters for a scenario.
type RequestSpec struct {
	Method  string            `json:"method"`
	Path    string            `json:"path"`
	Headers map[string]string `json:"headers"`
	Body    interface{}       `json:"body"`
}

// ResponseSpec defines the expected HTTP response for a scenario.
type ResponseSpec struct {
	Status  int               `json:"status"`
	Headers map[string]string `json:"headers"`
	Body    interface{}       `json:"body"`
}

// main runs the parity test runner against the configured target service.
func main() {
	target := flag.String("target", "", "Base URL of the service to validate (e.g. http://localhost:3001)")
	fixtures := flag.String("fixtures", "test/fixtures/parity", "Directory containing parity fixtures")
	seedEndpoint := flag.String("seed-endpoint", "/debug/parity/seed", "Endpoint to POST seed data to (ignored if empty)")
	timeout := flag.Duration("timeout", 5*time.Second, "HTTP request timeout per scenario")
	flag.Parse()

	if *target == "" {
		fmt.Fprintln(os.Stderr, "--target is required")
		os.Exit(1)
	}

	base := strings.TrimRight(*target, "/")
	if err := seedTarget(base, *fixtures, *seedEndpoint, *timeout); err != nil {
		fmt.Fprintf(os.Stderr, "seed warning: %v\n", err)
	}

	scenarioDir := filepath.Join(*fixtures, "scenarios")
	files, err := filepath.Glob(filepath.Join(scenarioDir, "*.json"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to list scenarios: %v\n", err)
		os.Exit(1)
	}
	if len(files) == 0 {
		fmt.Fprintf(os.Stderr, "no scenarios found in %s\n", scenarioDir)
		os.Exit(1)
	}
	sort.Strings(files)

	client := &http.Client{Timeout: *timeout}
	failures := 0

	for _, file := range files {
		data, err := os.ReadFile(file)
		if err != nil {
			fmt.Fprintf(os.Stderr, "failed to read %s: %v\n", file, err)
			failures++
			continue
		}
		var scenarios []Scenario
		if err := json.Unmarshal(data, &scenarios); err != nil {
			fmt.Fprintf(os.Stderr, "invalid fixture %s: %v\n", file, err)
			failures++
			continue
		}

		for _, scenario := range scenarios {
			fmt.Printf("Running scenario: %s\n", scenario.Name)
			if err := runScenario(client, base, scenario); err != nil {
				fmt.Fprintf(os.Stderr, "FAIL %s: %v\n", scenario.Name, err)
				failures++
			} else {
				fmt.Printf("PASS %s\n", scenario.Name)
			}
		}
	}

	if failures > 0 {
		os.Exit(1)
	}
}

// seedTarget posts the seed fixture to the target seed endpoint if available.
func seedTarget(base, fixturesDir, endpoint string, timeout time.Duration) error {
	if endpoint == "" {
		return nil
	}
	seedPath := filepath.Join(fixturesDir, "seed.json")
	data, err := os.ReadFile(seedPath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return err
	}
	req, err := http.NewRequest("POST", base+endpoint, bytes.NewReader(data))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	client := &http.Client{Timeout: timeout}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("seed request failed: %w", err)
	}
	defer resp.Body.Close()
	io.Copy(io.Discard, resp.Body)
	if resp.StatusCode >= 300 {
		return fmt.Errorf("seed request returned %d", resp.StatusCode)
	}
	return nil
}

// runScenario executes a Scenario and validates the actual HTTP response.
func runScenario(client *http.Client, base string, scenario Scenario) error {
	reqBody := []byte{}
	if scenario.Request.Body != nil {
		buf, err := json.Marshal(scenario.Request.Body)
		if err != nil {
			return fmt.Errorf("marshal request body: %w", err)
		}
		reqBody = buf
	}

	method := strings.ToUpper(scenario.Request.Method)
	if method == "" {
		method = "GET"
	}
	url := base + scenario.Request.Path
	req, err := http.NewRequest(method, url, bytes.NewReader(reqBody))
	if err != nil {
		return err
	}
	for k, v := range scenario.Request.Headers {
		req.Header.Set(k, v)
	}
	if req.Header.Get("Content-Type") == "" && len(reqBody) > 0 {
		req.Header.Set("Content-Type", "application/json")
	}

	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("read response: %w", err)
	}

	if resp.StatusCode != scenario.Response.Status {
		return fmt.Errorf("status %d != %d", resp.StatusCode, scenario.Response.Status)
	}

	if err := checkHeaders(scenario.Response.Headers, resp.Header); err != nil {
		return err
	}

	var actualBody interface{}
	if len(respBody) > 0 {
		if err := json.Unmarshal(respBody, &actualBody); err != nil {
			return fmt.Errorf("invalid response JSON: %w", err)
		}
	}

	if ok, msg := compareValue(scenario.Response.Body, actualBody); !ok {
		return fmt.Errorf("body mismatch: %s", msg)
	}

	return nil
}

// checkHeaders asserts that the actual HTTP headers contain the expected values.
func checkHeaders(expected map[string]string, actual http.Header) error {
	for key, expVal := range expected {
		got := actual.Get(key)
		if got == "" {
			return fmt.Errorf("missing header %s", key)
		}
		if !matchStringValue(expVal, got) {
			return fmt.Errorf("header %s mismatch: want %s, got %s", key, expVal, got)
		}
	}
	return nil
}

// compareValue recursively compares expected fixture values against actual responses.
func compareValue(expected, actual interface{}) (bool, string) {
	switch exp := expected.(type) {
	case map[string]interface{}:
		actMap, ok := actual.(map[string]interface{})
		if !ok {
			return false, fmt.Sprintf("expected object, got %T", actual)
		}
		for key, val := range exp {
			actVal, found := actMap[key]
			if !found {
				return false, fmt.Sprintf("missing key %s", key)
			}
			if ok, msg := compareValue(val, actVal); !ok {
				return false, fmt.Sprintf("%s.%s", key, msg)
			}
		}
		return true, ""
	case []interface{}:
		actArr, ok := actual.([]interface{})
		if !ok {
			return false, fmt.Sprintf("expected array, got %T", actual)
		}
		if len(actArr) != len(exp) {
			return false, fmt.Sprintf("array length %d != %d", len(actArr), len(exp))
		}
		for i := range exp {
			if ok, msg := compareValue(exp[i], actArr[i]); !ok {
				return false, fmt.Sprintf("[%d]%s", i, msg)
			}
		}
		return true, ""
	case string:
		if matchStringValue(exp, actual) {
			return true, ""
		}
		return false, fmt.Sprintf("string mismatch: expected %s", exp)
	case float64, bool, nil:
		if fmt.Sprintf("%v", exp) == fmt.Sprintf("%v", actual) {
			return true, ""
		}
		return false, fmt.Sprintf("value %v != %v", actual, exp)
	default:
		if fmt.Sprintf("%v", exp) == fmt.Sprintf("%v", actual) {
			return true, ""
		}
		return false, fmt.Sprintf("value %v != %v", actual, exp)
	}
}

// matchStringValue applies matcher tokens to strings (e.g., @any_number).
func matchStringValue(expected string, actual interface{}) bool {
	switch expected {
	case "@any_number":
		return isNumber(actual)
	case "@is_iso8601":
		if actStr, ok := actual.(string); ok {
			return isISO8601(actStr)
		}
		return false
	}
	actStr, ok := actual.(string)
	if !ok {
		return false
	}
	tokenRe := regexp.MustCompile(`@any_number|@is_iso8601`)
	if tokenRe.MatchString(expected) {
		tokens := tokenRe.FindAllString(expected, -1)
		parts := tokenRe.Split(expected, -1)
		var pattern strings.Builder
		checks := make([]func(string) bool, 0, len(tokens))
		for i, part := range parts {
			pattern.WriteString(regexp.QuoteMeta(part))
			if i < len(tokens) {
				switch tokens[i] {
				case "@any_number":
					pattern.WriteString(`(-?\d+(?:\.\d+)?)`)
					checks = append(checks, func(value string) bool { return isNumber(value) })
				case "@is_iso8601":
					pattern.WriteString(`(.+)`)
					checks = append(checks, func(value string) bool { return isISO8601(value) })
				}
			}
		}
		re := regexp.MustCompile("^" + pattern.String() + "$")
		matches := re.FindStringSubmatch(actStr)
		if matches == nil {
			return false
		}
		for idx, check := range checks {
			if !check(matches[idx+1]) {
				return false
			}
		}
		return true
	}
	return expected == actStr
}

// isNumber reports whether the provided value represents a number.
func isNumber(value interface{}) bool {
	switch value.(type) {
	case float64, float32, int, int64, json.Number:
		return true
	case string:
		match, _ := regexp.MatchString(`^-?\d+(\.\d+)?$`, value.(string))
		return match
	default:
		return false
	}
}

// isISO8601 checks whether a string is an ISO 8601 timestamp.
func isISO8601(value string) bool {
	if _, err := time.Parse(time.RFC3339Nano, value); err == nil {
		return true
	}
	if _, err := time.Parse(time.RFC3339, value); err == nil {
		return true
	}
	return false
}
