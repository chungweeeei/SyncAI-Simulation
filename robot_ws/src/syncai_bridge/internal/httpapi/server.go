package httpapi

import (
	"context"
	"encoding/json"
	"log/slog"
	"net/http"
	"strings"

	"github.com/nicosyncai/syncai-bridge/internal/dispatch"
	"github.com/nicosyncai/syncai-bridge/internal/state"
)

type Server struct {
	addr   string
	store  *state.Store
	router *dispatch.Router
	logger *slog.Logger
	srv    *http.Server
}

func NewServer(addr string, store *state.Store, router *dispatch.Router, logger *slog.Logger) *Server {
	s := &Server{
		addr:   addr,
		store:  store,
		router: router,
		logger: logger,
	}

	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/v1/state", s.handleGetAllState)
	mux.HandleFunc("GET /api/v1/state/", s.handleGetState)
	mux.HandleFunc("POST /api/v1/dispatch", s.handleDispatch)

	s.srv = &http.Server{
		Addr:    addr,
		Handler: mux,
	}
	return s
}

func (s *Server) Start() error {
	s.logger.Info("HTTP server listening", "addr", s.addr)
	return s.srv.ListenAndServe()
}

func (s *Server) Shutdown(ctx context.Context) error {
	return s.srv.Shutdown(ctx)
}

func (s *Server) handleGetAllState(w http.ResponseWriter, _ *http.Request) {
	states := s.store.GetAll()
	writeJSON(w, http.StatusOK, states)
}

func (s *Server) handleGetState(w http.ResponseWriter, r *http.Request) {
	// Extract robot ID from path: /api/v1/state/{robot_id}
	robotID := strings.TrimPrefix(r.URL.Path, "/api/v1/state/")
	if robotID == "" {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "missing robot_id"})
		return
	}

	st := s.store.Get(robotID)
	if st == nil {
		writeJSON(w, http.StatusNotFound, map[string]string{"error": "robot not found: " + robotID})
		return
	}
	writeJSON(w, http.StatusOK, st)
}

func (s *Server) handleDispatch(w http.ResponseWriter, r *http.Request) {
	var req dispatch.Request
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid request: " + err.Error()})
		return
	}

	resp, err := s.router.Dispatch(r.Context(), req)
	if err != nil {
		s.logger.Error("dispatch failed", "error", err, "protocol", req.Protocol, "target", req.Target, "action", req.Action)
		writeJSON(w, http.StatusInternalServerError, dispatch.Response{
			Success: false,
			Message: err.Error(),
		})
		return
	}

	writeJSON(w, http.StatusOK, resp)
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}
