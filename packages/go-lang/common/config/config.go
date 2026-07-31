package config

import (
	"fmt"
	"os"
)

// GetEnv helper reads environment variables with a default fallback
func GetEnv(key, defaultVal string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultVal
}

// GetRequiredEnv reads environment variables and returns error if missing
func GetRequiredEnv(key string) (string, error) {
	value, exists := os.LookupEnv(key)
	if !exists {
		return "", fmt.Errorf("missing required environment variable: %s", key)
	}
	return value, nil
}
