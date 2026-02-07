package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
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
