package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestMatchStringValue_Tokens(t *testing.T) {
	t.Parallel()

	if !matchStringValue("@any_number", 42.0) {
		t.Fatal("expected @any_number to match float64")
	}
	if !matchStringValue("@any_number", "42") {
		t.Fatal("expected @any_number to match numeric string")
	}
	if matchStringValue("@any_number", "abc") {
		t.Fatal("expected @any_number to reject non-numeric string")
	}

	if !matchStringValue("@is_iso8601", "2025-01-01T00:00:00Z") {
		t.Fatal("expected @is_iso8601 to match RFC3339")
	}
	if matchStringValue("@is_iso8601", "2025/01/01") {
		t.Fatal("expected @is_iso8601 to reject non-ISO string")
	}
}

func TestMatchStringValue_EmbeddedTokens(t *testing.T) {
	t.Parallel()

	if !matchStringValue("/users/@any_number", "/users/123") {
		t.Fatal("expected embedded @any_number token to match")
	}
	if matchStringValue("/users/@any_number", "/users/abc") {
		t.Fatal("expected embedded @any_number token to reject non-number")
	}

	if !matchStringValue("created:@is_iso8601", "created:2025-01-01T00:00:00.000Z") {
		t.Fatal("expected embedded @is_iso8601 token to match")
	}
}

func TestCompareValue_RecursiveObjectAndArray(t *testing.T) {
	t.Parallel()

	expected := map[string]interface{}{
		"id": "@any_number",
		"meta": map[string]interface{}{
			"createdAt": "@is_iso8601",
		},
		"items": []interface{}{map[string]interface{}{"value": "@any_number"}},
	}

	actual := map[string]interface{}{
		"id": 1.0,
		"meta": map[string]interface{}{
			"createdAt": "2025-01-01T00:00:00Z",
		},
		"items": []interface{}{map[string]interface{}{"value": 12.0}},
		"extra": "allowed",
	}

	ok, msg := compareValue(expected, actual)
	if !ok {
		t.Fatalf("expected compareValue to pass, got msg=%s", msg)
	}
}

func TestCompareValue_ArrayLengthMismatch(t *testing.T) {
	t.Parallel()

	ok, _ := compareValue([]interface{}{1.0, 2.0}, []interface{}{1.0})
	if ok {
		t.Fatal("expected compareValue to fail on array length mismatch")
	}
}

func TestParityFixtures_AreWellFormed(t *testing.T) {
	t.Parallel()

	scenarioDir := filepath.Join("..", "..", "test", "fixtures", "parity", "scenarios")
	entries, err := os.ReadDir(scenarioDir)
	if err != nil {
		t.Fatalf("failed to read scenario dir: %v", err)
	}
	if len(entries) == 0 {
		t.Fatal("expected at least one scenario file")
	}

	for _, entry := range entries {
		if entry.IsDir() || filepath.Ext(entry.Name()) != ".json" {
			continue
		}
		path := filepath.Join(scenarioDir, entry.Name())
		data, readErr := os.ReadFile(path)
		if readErr != nil {
			t.Fatalf("failed reading %s: %v", path, readErr)
		}

		var scenarios []Scenario
		if unmarshalErr := json.Unmarshal(data, &scenarios); unmarshalErr != nil {
			t.Fatalf("invalid scenario JSON %s: %v", path, unmarshalErr)
		}
		if len(scenarios) == 0 {
			t.Fatalf("expected at least one scenario in %s", path)
		}

		seen := make(map[string]bool)
		for _, s := range scenarios {
			if s.Name == "" {
				t.Fatalf("scenario with empty name in %s", path)
			}
			if seen[s.Name] {
				t.Fatalf("duplicate scenario name %q in %s", s.Name, path)
			}
			seen[s.Name] = true

			if s.Request.Path == "" {
				t.Fatalf("scenario %q has empty request.path in %s", s.Name, path)
			}
			if s.Response.Status <= 0 {
				t.Fatalf("scenario %q has invalid response.status in %s", s.Name, path)
			}
		}
	}
}

func TestSeedTarget_DisabledEndpoint(t *testing.T) {
	t.Parallel()

	if err := seedTarget("http://example.invalid", "does-not-matter", "", time.Second); err != nil {
		t.Fatalf("expected nil when seed endpoint disabled, got %v", err)
	}
}

func TestSeedTarget_MissingSeedFileIsNoop(t *testing.T) {
	t.Parallel()

	tmp := t.TempDir()
	if err := seedTarget("http://example.invalid", tmp, "/debug/parity/seed", time.Second); err != nil {
		t.Fatalf("expected nil when seed.json missing, got %v", err)
	}
}

func TestSeedTarget_HTTPFailure(t *testing.T) {
	t.Parallel()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	tmp := t.TempDir()
	seedPath := filepath.Join(tmp, "seed.json")
	if err := os.WriteFile(seedPath, []byte(`{"users":[]}`), 0o644); err != nil {
		t.Fatalf("failed writing seed file: %v", err)
	}

	err := seedTarget(server.URL, tmp, "/debug/parity/seed", time.Second)
	if err == nil {
		t.Fatal("expected error for non-2xx seed response")
	}
	if !strings.Contains(err.Error(), "seed request returned 500") {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestRunScenario_StatusMismatch(t *testing.T) {
	t.Parallel()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"ok":true}`))
	}))
	defer server.Close()

	s := Scenario{
		Name:     "status mismatch",
		Request:  RequestSpec{Path: "/health"},
		Response: ResponseSpec{Status: http.StatusCreated, Body: map[string]interface{}{"ok": true}},
	}

	err := runScenario(&http.Client{Timeout: time.Second}, server.URL, s)
	if err == nil || !strings.Contains(err.Error(), "status 200 != 201") {
		t.Fatalf("expected status mismatch error, got %v", err)
	}
}

func TestRunScenario_HeaderMismatch(t *testing.T) {
	t.Parallel()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("X-Version", "v1")
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"ok":true}`))
	}))
	defer server.Close()

	s := Scenario{
		Name:    "header mismatch",
		Request: RequestSpec{Path: "/health"},
		Response: ResponseSpec{
			Status:  http.StatusOK,
			Headers: map[string]string{"X-Version": "v2"},
			Body:    map[string]interface{}{"ok": true},
		},
	}

	err := runScenario(&http.Client{Timeout: time.Second}, server.URL, s)
	if err == nil || !strings.Contains(err.Error(), "header X-Version mismatch") {
		t.Fatalf("expected header mismatch error, got %v", err)
	}
}

func TestRunScenario_InvalidJSONResponse(t *testing.T) {
	t.Parallel()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("not-json"))
	}))
	defer server.Close()

	s := Scenario{
		Name:     "invalid json",
		Request:  RequestSpec{Path: "/health"},
		Response: ResponseSpec{Status: http.StatusOK, Body: map[string]interface{}{"ok": true}},
	}

	err := runScenario(&http.Client{Timeout: time.Second}, server.URL, s)
	if err == nil || !strings.Contains(err.Error(), "invalid response JSON") {
		t.Fatalf("expected invalid JSON error, got %v", err)
	}
}

func TestRunScenario_DefaultMethodIsGET(t *testing.T) {
	t.Parallel()

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			t.Fatalf("expected default method GET, got %s", r.Method)
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"ok":true}`))
	}))
	defer server.Close()

	s := Scenario{
		Name:     "default method",
		Request:  RequestSpec{Path: "/health"},
		Response: ResponseSpec{Status: http.StatusOK, Body: map[string]interface{}{"ok": true}},
	}

	if err := runScenario(&http.Client{Timeout: time.Second}, server.URL, s); err != nil {
		t.Fatalf("unexpected runScenario error: %v", err)
	}
}

func TestMatchStringValue_InterpolatedTokensRejectInvalidSegments(t *testing.T) {
	t.Parallel()

	if matchStringValue("/users/@any_number/events/@is_iso8601", "/users/abc/events/2025-01-01T00:00:00Z") {
		t.Fatal("expected non-numeric segment to fail @any_number")
	}
	if matchStringValue("/users/@any_number/events/@is_iso8601", "/users/123/events/not-a-date") {
		t.Fatal("expected non-iso segment to fail @is_iso8601")
	}
}

func TestParityFixtures_NegativeContractCases(t *testing.T) {
	t.Parallel()

	cases := []struct {
		name     string
		scenario Scenario
	}{
		{
			name: "empty request path",
			scenario: Scenario{
				Name: "bad-path",
				Request: RequestSpec{
					Path: "",
				},
				Response: ResponseSpec{Status: 200},
			},
		},
		{
			name: "invalid response status",
			scenario: Scenario{
				Name:     "bad-status",
				Request:  RequestSpec{Path: "/health"},
				Response: ResponseSpec{Status: 0},
			},
		},
	}

	for _, tc := range cases {
		tc := tc
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel()
			if tc.scenario.Request.Path != "" && tc.scenario.Response.Status > 0 {
				t.Fatalf("expected invalid fixture contract for case %q", tc.name)
			}
		})
	}
}
