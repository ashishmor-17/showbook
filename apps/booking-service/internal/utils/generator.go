package utils

import (
	"crypto/rand"
	"fmt"
	"math/big"
)

func GenerateBookingRef(dateStr string) (string, error) {
	const letters = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789" // Omit ambiguous characters
	result := make([]byte, 6)
	for i := 0; i < 6; i++ {
		num, err := rand.Int(rand.Reader, big.NewInt(int64(len(letters))))
		if err != nil {
			return "", err
		}
		result[i] = letters[num.Int64()]
	}
	return fmt.Sprintf("SHB-%s-%s", dateStr, string(result)), nil
}
