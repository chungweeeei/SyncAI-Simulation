package dds

import (
	"context"
	"crypto/rand"
	"encoding/json"
	"fmt"
	"log/slog"
	"sync"
	"time"

	"github.com/nicosyncai/syncai-bridge/internal/dispatch"
)

// robotEndpoint holds DDS writer and reader for a single robot's bridge_cmd service.
type robotEndpoint struct {
	cmdWriter  *DDSWriter
	respReader *DDSReader
}

// Adapter implements dispatch.OutboundAdapter for the DDS protocol.
// It supports both fire-and-forget (cmd_vel) and request/response (bridge_cmd).
type Adapter struct {
	logger      *slog.Logger
	participant *DDSParticipant
	timeout     time.Duration

	mu        sync.Mutex
	writers   map[string]*DDSWriter    // "{target}/{action}" → writer (fire-and-forget)
	endpoints map[string]*robotEndpoint // target → bridge_cmd endpoint

	pendingMu sync.Mutex
	pending   map[string]chan *BridgeCmdResponse // request_id → response channel

	stopOnce sync.Once
	stopCh   chan struct{}
}

func NewAdapter(logger *slog.Logger, participant *DDSParticipant) *Adapter {
	return &Adapter{
		logger:      logger,
		participant: participant,
		timeout:     30 * time.Second,
		writers:     make(map[string]*DDSWriter),
		endpoints:   make(map[string]*robotEndpoint),
		pending:     make(map[string]chan *BridgeCmdResponse),
		stopCh:      make(chan struct{}),
	}
}

func (a *Adapter) Protocol() string { return "dds" }

func (a *Adapter) Dispatch(ctx context.Context, req dispatch.Request) (*dispatch.Response, error) {
	switch req.Action {
	case "cmd_vel":
		return a.dispatchCmdVel(req)
	default:
		return a.dispatchBridgeCmd(ctx, req)
	}
}

// Stop terminates the response poller goroutines.
func (a *Adapter) Stop() {
	a.stopOnce.Do(func() { close(a.stopCh) })
}

// --- fire-and-forget (cmd_vel) ---

func (a *Adapter) dispatchCmdVel(req dispatch.Request) (*dispatch.Response, error) {
	lx := toFloat64(req.Payload, "linear_x")
	ly := toFloat64(req.Payload, "linear_y")
	lz := toFloat64(req.Payload, "linear_z")
	ax := toFloat64(req.Payload, "angular_x")
	ay := toFloat64(req.Payload, "angular_y")
	az := toFloat64(req.Payload, "angular_z")

	writer, err := a.getOrCreateTwistWriter(req.Target, "cmd_vel")
	if err != nil {
		return nil, fmt.Errorf("get writer: %w", err)
	}

	if err := PublishTwist(writer, lx, ly, lz, ax, ay, az); err != nil {
		return nil, fmt.Errorf("publish twist: %w", err)
	}

	a.logger.Info("published cmd_vel", "target", req.Target, "linear_x", lx, "angular_z", az)
	return &dispatch.Response{Success: true, Message: fmt.Sprintf("published cmd_vel to %s", req.Target)}, nil
}

func (a *Adapter) getOrCreateTwistWriter(target, action string) (*DDSWriter, error) {
	key := target + "/" + action
	a.mu.Lock()
	defer a.mu.Unlock()

	if w, ok := a.writers[key]; ok {
		return w, nil
	}

	topicName := fmt.Sprintf("rt/%s/%s", target, action)
	topic, err := CreateTwistTopic(a.participant, topicName)
	if err != nil {
		return nil, err
	}
	writer, err := CreateWriter(a.participant, topic)
	if err != nil {
		return nil, err
	}

	a.writers[key] = writer
	a.logger.Info("created Twist writer", "topic", topicName)
	return writer, nil
}

// --- request/response (bridge_cmd) ---

func (a *Adapter) dispatchBridgeCmd(ctx context.Context, req dispatch.Request) (*dispatch.Response, error) {
	ep, err := a.getOrCreateEndpoint(req.Target)
	if err != nil {
		return nil, fmt.Errorf("get endpoint: %w", err)
	}

	requestID := newUUID()
	payloadJSON, err := json.Marshal(req.Payload)
	if err != nil {
		return nil, fmt.Errorf("marshal payload: %w", err)
	}

	// Register pending response channel
	ch := make(chan *BridgeCmdResponse, 1)
	a.pendingMu.Lock()
	a.pending[requestID] = ch
	a.pendingMu.Unlock()
	defer func() {
		a.pendingMu.Lock()
		delete(a.pending, requestID)
		a.pendingMu.Unlock()
	}()

	// Publish command
	if err := PublishBridgeCmd(ep.cmdWriter, requestID, req.Action, string(payloadJSON)); err != nil {
		return nil, fmt.Errorf("publish bridge cmd: %w", err)
	}

	a.logger.Info("published bridge_cmd",
		"target", req.Target, "action", req.Action, "request_id", requestID)

	// Wait for response
	select {
	case resp := <-ch:
		return &dispatch.Response{Success: resp.Success, Message: resp.Message}, nil
	case <-time.After(a.timeout):
		return nil, fmt.Errorf("timeout waiting for response from %s (request_id=%s)", req.Target, requestID)
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

// getOrCreateEndpoint lazily creates DDS cmd writer + resp reader for a robot,
// and starts a poller goroutine for the response reader.
func (a *Adapter) getOrCreateEndpoint(target string) (*robotEndpoint, error) {
	a.mu.Lock()
	defer a.mu.Unlock()

	if ep, ok := a.endpoints[target]; ok {
		return ep, nil
	}

	// Command writer
	cmdTopicName := fmt.Sprintf("rt/%s/bridge_cmd", target)
	cmdTopic, err := CreateBridgeCmdTopic(a.participant, cmdTopicName)
	if err != nil {
		return nil, err
	}
	cmdWriter, err := CreateWriter(a.participant, cmdTopic)
	if err != nil {
		return nil, err
	}

	// Response reader
	respTopicName := fmt.Sprintf("rt/%s/bridge_cmd_resp", target)
	respTopic, err := CreateBridgeCmdRespTopic(a.participant, respTopicName)
	if err != nil {
		return nil, err
	}
	respReader, err := CreateReaderNoListener(a.participant, respTopic)
	if err != nil {
		return nil, err
	}

	ep := &robotEndpoint{cmdWriter: cmdWriter, respReader: respReader}
	a.endpoints[target] = ep

	a.logger.Info("created bridge_cmd endpoint",
		"cmd_topic", cmdTopicName, "resp_topic", respTopicName)

	// Start response poller
	go a.pollResponses(target, respReader)

	return ep, nil
}

// pollResponses continuously polls the response reader and dispatches
// responses to the matching pending channel by request_id.
func (a *Adapter) pollResponses(target string, reader *DDSReader) {
	ticker := time.NewTicker(10 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-a.stopCh:
			return
		case <-ticker.C:
			for {
				resp, err := TakeBridgeCmdResp(reader)
				if err != nil {
					a.logger.Error("poll response error", "target", target, "error", err)
					break
				}
				if resp == nil {
					break // no more data
				}

				a.pendingMu.Lock()
				ch, ok := a.pending[resp.RequestID]
				a.pendingMu.Unlock()

				if ok {
					ch <- resp
				} else {
					a.logger.Warn("received response for unknown request",
						"target", target, "request_id", resp.RequestID)
				}
			}
		}
	}
}

// --- helpers ---

func toFloat64(m map[string]any, key string) float64 {
	v, ok := m[key]
	if !ok {
		return 0
	}
	switch n := v.(type) {
	case float64:
		return n
	case float32:
		return float64(n)
	case int:
		return float64(n)
	default:
		return 0
	}
}

// newUUID generates a UUID v4 string without external dependencies.
func newUUID() string {
	var u [16]byte
	rand.Read(u[:])
	u[6] = (u[6] & 0x0f) | 0x40 // version 4
	u[8] = (u[8] & 0x3f) | 0x80 // variant 1
	return fmt.Sprintf("%08x-%04x-%04x-%04x-%012x",
		u[0:4], u[4:6], u[6:8], u[8:10], u[10:16])
}
