package dds

/*
#cgo CFLAGS: -I/opt/ros/jazzy/include/CycloneDDS
#cgo LDFLAGS: -L/opt/ros/jazzy/lib/aarch64-linux-gnu -lddsc -Wl,-rpath,/opt/ros/jazzy/lib/aarch64-linux-gnu

#include <stdlib.h>
#include <string.h>
#include "dds/dds.h"
#include "robot_state_ros2.h"
#include "bridge_service.h"

// Forward declaration of the Go callback (defined in callback.go via //export).
extern void goOnDataAvailable(int reader);

// C callback wrapper invoked by CycloneDDS listener thread.
static void on_data_available_cb(dds_entity_t reader, void *arg) {
    (void)arg;
    goOnDataAvailable((int)reader);
}

// Helper: create a participant on the given domain.
static dds_entity_t create_participant(int32_t domain_id) {
    return dds_create_participant((dds_domainid_t)domain_id, NULL, NULL);
}

// Helper: create a topic for RobotState_.
static dds_entity_t create_robot_state_topic(dds_entity_t participant, const char *topic_name) {
    return dds_create_topic(participant, &syncai_common_msg_dds__RobotState__desc, topic_name, NULL, NULL);
}

// Helper: create a reader with BEST_EFFORT, VOLATILE QoS and a listener.
static dds_entity_t create_reader_with_listener(dds_entity_t participant, dds_entity_t topic) {
    // Create QoS: BEST_EFFORT, VOLATILE, depth 5
    dds_qos_t *qos = dds_create_qos();
    dds_qset_reliability(qos, DDS_RELIABILITY_BEST_EFFORT, 0);
    dds_qset_durability(qos, DDS_DURABILITY_VOLATILE);
    dds_qset_history(qos, DDS_HISTORY_KEEP_LAST, 5);

    // Create listener with on_data_available callback
    dds_listener_t *listener = dds_create_listener(NULL);
    dds_lset_data_available(listener, on_data_available_cb);

    dds_entity_t reader = dds_create_reader(participant, topic, qos, listener);

    dds_delete_listener(listener);
    dds_delete_qos(qos);
    return reader;
}

// Helper: take one sample from the reader.
// Returns 1 if a sample was taken, 0 if no data, negative on error.
// Caller must call free_robot_state_sample(sample) after use.
static int32_t take_robot_state(dds_entity_t reader, syncai_common_msg_dds__RobotState_ **sample_out) {
    void *samples[1];
    dds_sample_info_t infos[1];
    samples[0] = syncai_common_msg_dds__RobotState___alloc();
    if (!samples[0]) return -1;

    dds_return_t rc = dds_take(reader, samples, infos, 1, 1);
    if (rc > 0 && infos[0].valid_data) {
        *sample_out = (syncai_common_msg_dds__RobotState_ *)samples[0];
        return 1;
    }

    // Free sample if no valid data
    syncai_common_msg_dds__RobotState__free(samples[0], DDS_FREE_ALL);
    *sample_out = NULL;
    return (rc >= 0) ? 0 : (int32_t)rc;
}

// Helper: free a sample.
static void free_robot_state_sample(syncai_common_msg_dds__RobotState_ *sample) {
    if (sample) {
        syncai_common_msg_dds__RobotState__free(sample, DDS_FREE_ALL);
    }
}

// Helper: create a topic for Twist_.
static dds_entity_t create_twist_topic(dds_entity_t participant, const char *topic_name) {
    return dds_create_topic(participant, &geometry_msgs_msg_dds__Twist__desc, topic_name, NULL, NULL);
}

// Helper: create a writer with default QoS.
static dds_entity_t create_writer(dds_entity_t participant, dds_entity_t topic) {
    return dds_create_writer(participant, topic, NULL, NULL);
}

// Helper: publish a Twist message.
static int32_t publish_twist(dds_entity_t writer,
    double lx, double ly, double lz,
    double ax, double ay, double az) {
    geometry_msgs_msg_dds__Twist_ msg;
    memset(&msg, 0, sizeof(msg));
    msg.linear.x = lx; msg.linear.y = ly; msg.linear.z = lz;
    msg.angular.x = ax; msg.angular.y = ay; msg.angular.z = az;
    return (int32_t)dds_write(writer, &msg);
}

// Helper: create BridgeCommand topic.
static dds_entity_t create_bridge_cmd_topic(dds_entity_t participant, const char *topic_name) {
    return dds_create_topic(participant, &syncai_common_msg_dds__BridgeCommand__desc, topic_name, NULL, NULL);
}

// Helper: create BridgeCommandResponse topic.
static dds_entity_t create_bridge_cmd_resp_topic(dds_entity_t participant, const char *topic_name) {
    return dds_create_topic(participant, &syncai_common_msg_dds__BridgeCommandResponse__desc, topic_name, NULL, NULL);
}

// Helper: create a reader with RELIABLE QoS and no listener (for polling).
static dds_entity_t create_reader_no_listener(dds_entity_t participant, dds_entity_t topic) {
    dds_qos_t *qos = dds_create_qos();
    dds_qset_reliability(qos, DDS_RELIABILITY_RELIABLE, DDS_SECS(1));
    dds_qset_durability(qos, DDS_DURABILITY_VOLATILE);
    dds_qset_history(qos, DDS_HISTORY_KEEP_LAST, 16);

    dds_entity_t reader = dds_create_reader(participant, topic, qos, NULL);
    dds_delete_qos(qos);
    return reader;
}

// Helper: publish a BridgeCommand.
static int32_t publish_bridge_cmd(dds_entity_t writer,
    const char *request_id, const char *action, const char *payload_json) {
    syncai_common_msg_dds__BridgeCommand_ msg;
    memset(&msg, 0, sizeof(msg));
    msg.request_id = (char *)request_id;
    msg.action = (char *)action;
    msg.payload_json = (char *)payload_json;
    return (int32_t)dds_write(writer, &msg);
}

// Helper: take one BridgeCommandResponse sample.
static int32_t take_bridge_cmd_resp(dds_entity_t reader,
    syncai_common_msg_dds__BridgeCommandResponse_ **sample_out) {
    void *samples[1];
    dds_sample_info_t infos[1];
    samples[0] = syncai_common_msg_dds__BridgeCommandResponse___alloc();
    if (!samples[0]) return -1;

    dds_return_t rc = dds_take(reader, samples, infos, 1, 1);
    if (rc > 0 && infos[0].valid_data) {
        *sample_out = (syncai_common_msg_dds__BridgeCommandResponse_ *)samples[0];
        return 1;
    }

    syncai_common_msg_dds__BridgeCommandResponse__free(samples[0], DDS_FREE_ALL);
    *sample_out = NULL;
    return (rc >= 0) ? 0 : (int32_t)rc;
}

// Helper: free a BridgeCommandResponse sample.
static void free_bridge_cmd_resp(syncai_common_msg_dds__BridgeCommandResponse_ *sample) {
    if (sample) {
        syncai_common_msg_dds__BridgeCommandResponse__free(sample, DDS_FREE_ALL);
    }
}

// Helper: delete a DDS entity.
static int32_t delete_entity(dds_entity_t entity) {
    return (int32_t)dds_delete(entity);
}
*/
import "C"

import (
	"fmt"
	"unsafe"
)

// DDSParticipant wraps a CycloneDDS participant handle.
type DDSParticipant struct {
	handle C.dds_entity_t
}

// DDSTopic wraps a CycloneDDS topic handle.
type DDSTopic struct {
	handle C.dds_entity_t
}

// DDSReader wraps a CycloneDDS reader handle.
type DDSReader struct {
	handle C.dds_entity_t
}

// CreateParticipant creates a DDS domain participant.
func CreateParticipant(domainID int32) (*DDSParticipant, error) {
	h := C.create_participant(C.int32_t(domainID))
	if h < 0 {
		return nil, fmt.Errorf("dds_create_participant failed: %d", h)
	}
	return &DDSParticipant{handle: h}, nil
}

// CreateRobotStateTopic creates a topic for RobotState messages.
func CreateRobotStateTopic(p *DDSParticipant, topicName string) (*DDSTopic, error) {
	cName := C.CString(topicName)
	defer C.free(unsafe.Pointer(cName))

	h := C.create_robot_state_topic(p.handle, cName)
	if h < 0 {
		return nil, fmt.Errorf("dds_create_topic failed: %d", h)
	}
	return &DDSTopic{handle: h}, nil
}

// CreateReaderWithListener creates a reader with BEST_EFFORT QoS and
// a listener callback that will invoke goOnDataAvailable.
func CreateReaderWithListener(p *DDSParticipant, t *DDSTopic) (*DDSReader, error) {
	h := C.create_reader_with_listener(p.handle, t.handle)
	if h < 0 {
		return nil, fmt.Errorf("dds_create_reader failed: %d", h)
	}
	return &DDSReader{handle: h}, nil
}

// TakeRobotState takes one RobotState sample from the reader.
// Returns nil if no data is available.
func TakeRobotState(r *DDSReader) (*RobotState, error) {
	var cSample *C.syncai_common_msg_dds__RobotState_
	rc := C.take_robot_state(r.handle, &cSample)
	if rc < 0 {
		return nil, fmt.Errorf("dds_take failed: %d", rc)
	}
	if rc == 0 || cSample == nil {
		return nil, nil
	}
	defer C.free_robot_state_sample(cSample)

	state := &RobotState{
		TimestampSec:  int32(cSample.header.stamp.sec),
		TimestampNsec: uint32(cSample.header.stamp.nanosec),
		FrameID:       C.GoString(cSample.header.frame_id),
		RobotID:       C.GoString(cSample.robot_id),
		RobotName:     C.GoString(cSample.robot_name),
		Model:         C.GoString(cSample.model),
		Map:           C.GoString(cSample.map_),
		PoseX:         float64(cSample.pose.position.x),
		PoseY:         float64(cSample.pose.position.y),
		PoseZ:         float64(cSample.pose.position.z),
		OrientX:       float64(cSample.pose.orientation.x),
		OrientY:       float64(cSample.pose.orientation.y),
		OrientZ:       float64(cSample.pose.orientation.z),
		OrientW:       float64(cSample.pose.orientation.w),
		LinearX:       float64(cSample.velocity.linear.x),
		LinearY:       float64(cSample.velocity.linear.y),
		LinearZ:       float64(cSample.velocity.linear.z),
		AngularX:      float64(cSample.velocity.angular.x),
		AngularY:      float64(cSample.velocity.angular.y),
		AngularZ:      float64(cSample.velocity.angular.z),
		BatteryPct:    float32(cSample.battery_percentage),
		BatteryV:      float32(cSample.battery_voltage),
	}
	return state, nil
}

// DeleteEntity deletes a DDS entity (participant, topic, or reader).
func DeleteEntity(handle int32) error {
	rc := C.delete_entity(C.dds_entity_t(handle))
	if rc < 0 {
		return fmt.Errorf("dds_delete failed: %d", rc)
	}
	return nil
}

// ParticipantHandle returns the raw entity handle.
func (p *DDSParticipant) ParticipantHandle() int32 { return int32(p.handle) }

// ReaderHandle returns the raw entity handle.
func (r *DDSReader) ReaderHandle() int32 { return int32(r.handle) }

// DDSWriter wraps a CycloneDDS writer handle.
type DDSWriter struct {
	handle C.dds_entity_t
}

// CreateTwistTopic creates a topic for geometry_msgs/Twist messages.
func CreateTwistTopic(p *DDSParticipant, topicName string) (*DDSTopic, error) {
	cName := C.CString(topicName)
	defer C.free(unsafe.Pointer(cName))

	h := C.create_twist_topic(p.handle, cName)
	if h < 0 {
		return nil, fmt.Errorf("dds_create_topic (Twist) failed: %d", h)
	}
	return &DDSTopic{handle: h}, nil
}

// CreateWriter creates a DDS writer for the given topic.
func CreateWriter(p *DDSParticipant, t *DDSTopic) (*DDSWriter, error) {
	h := C.create_writer(p.handle, t.handle)
	if h < 0 {
		return nil, fmt.Errorf("dds_create_writer failed: %d", h)
	}
	return &DDSWriter{handle: h}, nil
}

// PublishTwist publishes a Twist message through the writer.
func PublishTwist(w *DDSWriter, lx, ly, lz, ax, ay, az float64) error {
	rc := C.publish_twist(w.handle,
		C.double(lx), C.double(ly), C.double(lz),
		C.double(ax), C.double(ay), C.double(az))
	if rc < 0 {
		return fmt.Errorf("dds_write (Twist) failed: %d", rc)
	}
	return nil
}

// WriterHandle returns the raw entity handle.
func (w *DDSWriter) WriterHandle() int32 { return int32(w.handle) }

// BridgeCmdResponse is the Go representation of a BridgeCommandResponse DDS sample.
type BridgeCmdResponse struct {
	RequestID string
	Success   bool
	Message   string
	DataJSON  string
}

// CreateBridgeCmdTopic creates a topic for BridgeCommand messages.
func CreateBridgeCmdTopic(p *DDSParticipant, topicName string) (*DDSTopic, error) {
	cName := C.CString(topicName)
	defer C.free(unsafe.Pointer(cName))

	h := C.create_bridge_cmd_topic(p.handle, cName)
	if h < 0 {
		return nil, fmt.Errorf("create BridgeCommand topic failed: %d", h)
	}
	return &DDSTopic{handle: h}, nil
}

// CreateBridgeCmdRespTopic creates a topic for BridgeCommandResponse messages.
func CreateBridgeCmdRespTopic(p *DDSParticipant, topicName string) (*DDSTopic, error) {
	cName := C.CString(topicName)
	defer C.free(unsafe.Pointer(cName))

	h := C.create_bridge_cmd_resp_topic(p.handle, cName)
	if h < 0 {
		return nil, fmt.Errorf("create BridgeCommandResponse topic failed: %d", h)
	}
	return &DDSTopic{handle: h}, nil
}

// CreateReaderNoListener creates a reader with RELIABLE QoS and no listener (for polling).
func CreateReaderNoListener(p *DDSParticipant, t *DDSTopic) (*DDSReader, error) {
	h := C.create_reader_no_listener(p.handle, t.handle)
	if h < 0 {
		return nil, fmt.Errorf("create reader (no listener) failed: %d", h)
	}
	return &DDSReader{handle: h}, nil
}

// PublishBridgeCmd publishes a BridgeCommand message.
func PublishBridgeCmd(w *DDSWriter, requestID, action, payloadJSON string) error {
	cReqID := C.CString(requestID)
	defer C.free(unsafe.Pointer(cReqID))
	cAction := C.CString(action)
	defer C.free(unsafe.Pointer(cAction))
	cPayload := C.CString(payloadJSON)
	defer C.free(unsafe.Pointer(cPayload))

	rc := C.publish_bridge_cmd(w.handle, cReqID, cAction, cPayload)
	if rc < 0 {
		return fmt.Errorf("publish BridgeCommand failed: %d", rc)
	}
	return nil
}

// TakeBridgeCmdResp takes one BridgeCommandResponse sample from the reader.
// Returns nil if no data is available.
func TakeBridgeCmdResp(r *DDSReader) (*BridgeCmdResponse, error) {
	var cSample *C.syncai_common_msg_dds__BridgeCommandResponse_
	rc := C.take_bridge_cmd_resp(r.handle, &cSample)
	if rc < 0 {
		return nil, fmt.Errorf("take BridgeCommandResponse failed: %d", rc)
	}
	if rc == 0 || cSample == nil {
		return nil, nil
	}
	defer C.free_bridge_cmd_resp(cSample)

	return &BridgeCmdResponse{
		RequestID: C.GoString(cSample.request_id),
		Success:   bool(cSample.success),
		Message:   C.GoString(cSample.message),
		DataJSON:  C.GoString(cSample.data_json),
	}, nil
}
