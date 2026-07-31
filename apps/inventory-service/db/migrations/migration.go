package migrations

import (
	"context"
	"embed"
	"fmt"
	"sort"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
	"go.uber.org/zap"
)

//go:embed *.sql
var migrationFS embed.FS

// Run executes pending database migrations in sorted order within transactions
func Run(ctx context.Context, db *pgxpool.Pool, log *zap.Logger) error {
	// Create migrations version tracking table
	createTableSQL := `
	CREATE TABLE IF NOT EXISTS schema_migrations (
		version VARCHAR(255) PRIMARY KEY,
		applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
	);`
	_, err := db.Exec(ctx, createTableSQL)
	if err != nil {
		return fmt.Errorf("failed to create schema_migrations table: %w", err)
	}

	// Read embedded migrations
	entries, err := migrationFS.ReadDir(".")
	if err != nil {
		return fmt.Errorf("failed to read embedded migrations: %w", err)
	}

	var files []string
	for _, entry := range entries {
		if !entry.IsDir() && strings.HasSuffix(entry.Name(), ".sql") {
			files = append(files, entry.Name())
		}
	}
	sort.Strings(files)

	// Query already applied migrations
	rows, err := db.Query(ctx, "SELECT version FROM schema_migrations")
	if err != nil {
		return fmt.Errorf("failed to query schema_migrations: %w", err)
	}
	defer rows.Close()

	applied := make(map[string]bool)
	for rows.Next() {
		var version string
		if err := rows.Scan(&version); err != nil {
			return fmt.Errorf("failed to scan migration version: %w", err)
		}
		applied[version] = true
	}

	// Run pending migrations in transaction blocks
	for _, file := range files {
		if applied[file] {
			continue
		}

		log.Info("Running migration", zap.String("file", file))
		content, err := migrationFS.ReadFile(file)
		if err != nil {
			return fmt.Errorf("failed to read migration file %s: %w", file, err)
		}

		tx, err := db.Begin(ctx)
		if err != nil {
			return fmt.Errorf("failed to start transaction: %w", err)
		}
		defer func() {
			_ = tx.Rollback(ctx)
		}()

		_, err = tx.Exec(ctx, string(content))
		if err != nil {
			return fmt.Errorf("failed to execute migration %s: %w", file, err)
		}

		_, err = tx.Exec(ctx, "INSERT INTO schema_migrations (version) VALUES ($1)", file)
		if err != nil {
			return fmt.Errorf("failed to record migration %s: %w", file, err)
		}

		err = tx.Commit(ctx)
		if err != nil {
			return fmt.Errorf("failed to commit transaction for migration %s: %w", file, err)
		}

		log.Info("Migration completed successfully", zap.String("file", file))
	}

	return nil
}
