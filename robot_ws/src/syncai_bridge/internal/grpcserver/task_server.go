package grpcserver

import (
	"context"
	"log/slog"

	pb "github.com/nicosyncai/syncai-bridge/internal/grpcserver/pb"
	"github.com/nicosyncai/syncai-bridge/internal/restclient"
)

// TaskServer implements pb.TaskServiceServer by proxying to the robot REST API.
type TaskServer struct {
	pb.UnimplementedTaskServiceServer

	logger *slog.Logger
	rest   *restclient.Client
}

// NewTaskServer creates a new TaskServer.
func NewTaskServer(logger *slog.Logger, rest *restclient.Client) *TaskServer {
	return &TaskServer{
		logger: logger,
		rest:   rest,
	}
}

// CreateTask creates a task via the robot REST API.
func (s *TaskServer) CreateTask(ctx context.Context, req *pb.CreateTaskRequest) (*pb.CreateTaskResponse, error) {
	restReq := &restclient.TaskCreateRequest{
		Action:    taskActionToString(req.GetAction()),
		ID:        req.GetId(),
		Timestamp: req.GetTimestamp(),
		Payload:   protoPayloadToRest(req.GetPayload()),
	}

	resp, err := s.rest.CreateTask(ctx, restReq)
	if err != nil {
		s.logger.Error("CreateTask failed", "error", err)
		return nil, mapHTTPError(err)
	}

	return &pb.CreateTaskResponse{
		Id:      resp.ID,
		Status:  taskStatusToProto(resp.Status),
		Message: resp.Message,
	}, nil
}

// ListTasks fetches all tasks from the robot REST API.
func (s *TaskServer) ListTasks(ctx context.Context, _ *pb.ListTasksRequest) (*pb.ListTasksResponse, error) {
	tasks, err := s.rest.ListTasks(ctx)
	if err != nil {
		s.logger.Error("ListTasks failed", "error", err)
		return nil, mapHTTPError(err)
	}

	pbTasks := make([]*pb.Task, len(tasks))
	for i := range tasks {
		pbTasks[i] = taskToProto(&tasks[i])
	}
	return &pb.ListTasksResponse{Tasks: pbTasks}, nil
}

// GetTask fetches a single task by ID from the robot REST API.
func (s *TaskServer) GetTask(ctx context.Context, req *pb.GetTaskRequest) (*pb.Task, error) {
	task, err := s.rest.GetTask(ctx, req.GetTaskId())
	if err != nil {
		s.logger.Error("GetTask failed", "task_id", req.GetTaskId(), "error", err)
		return nil, mapHTTPError(err)
	}
	return taskToProto(task), nil
}

// --- conversion helpers ---

func taskToProto(t *restclient.Task) *pb.Task {
	var steps []*pb.Step
	for i := range t.Payload.Steps {
		steps = append(steps, stepToProto(&t.Payload.Steps[i]))
	}

	return &pb.Task{
		Action:           taskActionToProto(t.Action),
		Id:               t.ID,
		Timestamp:        t.Timestamp,
		Payload:          &pb.TaskPayload{Steps: steps},
		Status:           taskStatusToProto(t.Status),
		CurrentStepIndex: int32(t.CurrentStepIndex),
		ErrorMsg:         t.ErrorMsg,
		WorkflowId:       t.WorkflowID,
		CompletedAt:      t.CompletedAt,
	}
}

func stepToProto(s *restclient.TaskStep) *pb.Step {
	ps := &pb.Step{
		Id:       s.ID,
		Name:     s.Name,
		Type:     stepTypeToProto(s.Type),
		Status:   taskStatusToProto(s.Status),
		ErrorMsg: s.ErrorMsg,
	}

	switch s.Type {
	case "MOVE", "CHARGE", "NAVIGATE_WITH_ALERT":
		p := &pb.PoseParams{}
		if s.Params.X != nil {
			p.X = float32(*s.Params.X)
		}
		if s.Params.Y != nil {
			p.Y = float32(*s.Params.Y)
		}
		if s.Params.R != nil {
			p.R = float32(*s.Params.R)
		}
		ps.Params = &pb.Step_PoseParams{PoseParams: p}
	case "WAIT":
		p := &pb.WaitParams{}
		if s.Params.DurationSec != nil {
			p.DurationSec = float32(*s.Params.DurationSec)
		}
		ps.Params = &pb.Step_WaitParams{WaitParams: p}
	case "DOOR":
		p := &pb.DoorParams{}
		if s.Params.Open != nil {
			p.Open = *s.Params.Open
		}
		ps.Params = &pb.Step_DoorParams{DoorParams: p}
	}

	return ps
}

func protoPayloadToRest(p *pb.TaskPayload) restclient.TaskPayload {
	if p == nil {
		return restclient.TaskPayload{}
	}
	steps := make([]restclient.TaskStep, len(p.GetSteps()))
	for i, s := range p.GetSteps() {
		steps[i] = protoStepToRest(s)
	}
	return restclient.TaskPayload{Steps: steps}
}

func protoStepToRest(s *pb.Step) restclient.TaskStep {
	st := restclient.TaskStep{
		ID:   s.GetId(),
		Name: s.GetName(),
		Type: stepTypeToString(s.GetType()),
	}

	switch p := s.GetParams().(type) {
	case *pb.Step_PoseParams:
		x, y, r := float64(p.PoseParams.GetX()), float64(p.PoseParams.GetY()), float64(p.PoseParams.GetR())
		st.Params = restclient.TaskStepParams{X: &x, Y: &y, R: &r}
	case *pb.Step_WaitParams:
		d := float64(p.WaitParams.GetDurationSec())
		st.Params = restclient.TaskStepParams{DurationSec: &d}
	case *pb.Step_DoorParams:
		o := p.DoorParams.GetOpen()
		st.Params = restclient.TaskStepParams{Open: &o}
	}

	return st
}

func taskActionToString(a pb.TaskAction) string {
	switch a {
	case pb.TaskAction_TASK:
		return "TASK"
	case pb.TaskAction_COMMAND:
		return "COMMAND"
	default:
		return "TASK"
	}
}

func stepTypeToString(t pb.StepType) string {
	switch t {
	case pb.StepType_MOVE:
		return "MOVE"
	case pb.StepType_WAIT:
		return "WAIT"
	case pb.StepType_DOOR:
		return "DOOR"
	case pb.StepType_CHARGE:
		return "CHARGE"
	case pb.StepType_NAVIGATE_WITH_ALERT:
		return "NAVIGATE_WITH_ALERT"
	default:
		return "MOVE"
	}
}

func taskActionToProto(s string) pb.TaskAction {
	switch s {
	case "TASK":
		return pb.TaskAction_TASK
	case "COMMAND":
		return pb.TaskAction_COMMAND
	default:
		return pb.TaskAction_TASK_ACTION_UNSPECIFIED
	}
}

func stepTypeToProto(s string) pb.StepType {
	switch s {
	case "MOVE":
		return pb.StepType_MOVE
	case "WAIT":
		return pb.StepType_WAIT
	case "DOOR":
		return pb.StepType_DOOR
	case "CHARGE":
		return pb.StepType_CHARGE
	case "NAVIGATE_WITH_ALERT":
		return pb.StepType_NAVIGATE_WITH_ALERT
	default:
		return pb.StepType_STEP_TYPE_UNSPECIFIED
	}
}

func taskStatusToProto(s string) pb.TaskStatus {
	switch s {
	case "PENDING":
		return pb.TaskStatus_PENDING
	case "IN_PROGRESS":
		return pb.TaskStatus_IN_PROGRESS
	case "COMPLETED":
		return pb.TaskStatus_COMPLETED
	case "FAILED":
		return pb.TaskStatus_FAILED
	case "CANCELLED":
		return pb.TaskStatus_CANCELLED
	default:
		return pb.TaskStatus_TASK_STATUS_UNSPECIFIED
	}
}
