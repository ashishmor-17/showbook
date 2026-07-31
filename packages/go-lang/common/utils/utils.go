package utils

import "time"

func FormatISO8601(t time.Time) string {
	return t.UTC().Format(time.RFC3339)
}
