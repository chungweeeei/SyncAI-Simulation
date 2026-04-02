package dispatch

import (
	"context"
	"fmt"
)

// Router dispatches requests to the appropriate outbound adapter by protocol.
type Router struct {
	adapters map[string]OutboundAdapter
}

func NewRouter() *Router {
	return &Router{
		adapters: make(map[string]OutboundAdapter),
	}
}

func (r *Router) Register(a OutboundAdapter) {
	r.adapters[a.Protocol()] = a
}

func (r *Router) Dispatch(ctx context.Context, req Request) (*Response, error) {
	a, ok := r.adapters[req.Protocol]
	if !ok {
		return nil, fmt.Errorf("no adapter registered for protocol: %s", req.Protocol)
	}
	return a.Dispatch(ctx, req)
}
