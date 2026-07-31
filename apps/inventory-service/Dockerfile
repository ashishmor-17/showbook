# Build stage
FROM golang:1.25-alpine AS builder

WORKDIR /build

COPY packages/go-lang/common ./packages/go-lang/common
COPY apps/inventory-service ./apps/inventory-service

WORKDIR /build/apps/inventory-service

RUN go mod download

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /app/inventory-service ./cmd/main.go

FROM alpine:3.19

WORKDIR /app

COPY --from=builder /app/inventory-service /app/inventory-service

EXPOSE 8003

# Run the binary
CMD ["/app/inventory-service"]
