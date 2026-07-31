package logger

import (
	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"
)

// New initializes and returns a custom Zap logger instance
func New(serviceName string, logLevel string) (*zap.Logger, error) {
	encoderConfig := zap.NewProductionEncoderConfig()
	encoderConfig.TimeKey = "T"
	encoderConfig.LevelKey = "L"
	encoderConfig.CallerKey = "C"
	encoderConfig.MessageKey = "M"

	encoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder
	encoderConfig.EncodeLevel = zapcore.CapitalLevelEncoder
	encoderConfig.EncodeCaller = zapcore.ShortCallerEncoder
	encoderConfig.ConsoleSeparator = " "

	var level zapcore.Level
	if err := level.UnmarshalText([]byte(logLevel)); err != nil {
		level = zapcore.InfoLevel
	}

	config := zap.Config{
		Level:            zap.NewAtomicLevelAt(level),
		Development:      false,
		Encoding:         "console",
		EncoderConfig:    encoderConfig,
		OutputPaths:      []string{"stdout"},
		ErrorOutputPaths: []string{"stderr"},
	}

	logger, err := config.Build(
		zap.AddStacktrace(zapcore.ErrorLevel),
	)
	if err != nil {
		return nil, err
	}

	return logger.With(zap.String("service", serviceName)), nil
}
