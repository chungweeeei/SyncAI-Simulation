package dispatch

import "context"

// OutboundAdapter translates a dispatch request into a protocol-specific call.
type OutboundAdapter interface {
	Protocol() string
	Dispatch(ctx context.Context, req Request) (*Response, error)
}
