package manager

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/bitxeno/atvloadly/internal/app"
	"github.com/bitxeno/atvloadly/internal/model"
)

func TestPairCompletionFromCommandResult(t *testing.T) {
	for _, tc := range []struct {
		name        string
		code        string
		wantSuccess bool
	}{
		{"successful command without success marker", "0", true},
		{"failed command", "1", false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			dir := t.TempDir()
			if err := os.WriteFile(filepath.Join(dir, "plumesign"), []byte("#!/bin/sh\nprintf 'Pairing successful\\n'\nexit "+tc.code+"\n"), 0755); err != nil {
				t.Fatal(err)
			}
			t.Setenv("PATH", dir+":"+os.Getenv("PATH"))
			previousConfig, previousSettings := app.Config, app.Settings
			app.Config = &app.Configuration{}
			app.Config.Server.DataDir = dir
			app.Settings = &app.SettingsConfiguration{}
			t.Cleanup(func() { app.Config, app.Settings = previousConfig, previousSettings })
			mgr := NewPairManager()
			defer mgr.Close()
			completed := make(chan struct{}, 1)
			mgr.OnOutput(func(line string) {
				if strings.Contains(line, "SUCCESS") {
					completed <- struct{}{}
				}
			})
			err := mgr.Start(context.Background(), model.Device{IP: "127.0.0.1", Port: 1234})
			if (err == nil) != tc.wantSuccess {
				t.Fatalf("unexpected command result: %v", err)
			}
			if tc.wantSuccess {
				select {
				case <-completed:
				case <-time.After(time.Second):
					t.Fatal("browser did not receive completion")
				}
			} else if strings.Contains(mgr.OutputLog(), "SUCCESS") {
				t.Fatal("failed pairing emitted success")
			}
		})
	}
}
