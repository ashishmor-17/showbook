# apps/booking-service/Dockerfile
FROM golang:1.25.1-alpine AS builder

WORKDIR /build

COPY packages/go-lang/common ./packages/go-lang/common
COPY apps/booking-service ./apps/booking-service

WORKDIR /build/apps/booking-service

RUN go mod download
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /app/booking-service ./cmd/main.go

FROM alpine:3.19

WORKDIR /app

COPY --from=builder /app/booking-service /app/booking-service

EXPOSE 8006

CMD ["/app/booking-service"]
