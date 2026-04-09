package dds

/*
#cgo CFLAGS: -I/opt/ros/jazzy/include/CycloneDDS
#cgo LDFLAGS: -L/opt/ros/jazzy/lib/aarch64-linux-gnu -lddsc -Wl,-rpath,/opt/ros/jazzy/lib/aarch64-linux-gnu

#include <stdlib.h>
#include <string.h>
#include "dds/dds.h"
#include "robot_state_ros2.h"

// Forward declaration of the Go callback (defined in callback.go via //export).
extern void goOnDataAvailable(int reader);

// C callback wrapper invoked by CycloneDDS listener thread.
static void on_data_available_cb(dds_entity_t reader, void *arg) {
    (void)arg;
    goOnDataAvailable((int)reader);
}

// Helper: create a participant on the given domain.
// If config_xml is non-NULL and non-empty, creates a domain with that XML
// configuration before creating the participant.
static dds_entity_t create_participant_with_config(int32_t domain_id, const char *config_xml) {
    if (config_xml && config_xml[0] != '\0') {
        dds_entity_t domain = dds_create_domain((dds_domainid_t)domain_id, config_xml);
        if (domain < 0) return domain;
    }
    return dds_create_participant((dds_domainid_t)domain_id, NULL, NULL);
}

// Helper: create a topic for RobotState_.
static dds_entity_t create_robot_state_topic(dds_entity_t participant, const char *topic_name) {
    return dds_create_topic(participant, &syncai_common_msg_dds__RobotState__desc, topic_name, NULL, NULL);
}

// Helper: create a topic with an arbitrary descriptor.
static dds_entity_t create_topic(dds_entity_t participant, const dds_topic_descriptor_t *desc, const char *topic_name) {
    return dds_create_topic(participant, desc, topic_name, NULL, NULL);
}

// Helper: create a reader with BEST_EFFORT, VOLATILE QoS and a listener.
// If user_data is non-NULL, sets USER_DATA QoS (used for ROS 2 type hash).
static dds_entity_t create_reader_with_listener(dds_entity_t participant, dds_entity_t topic, const void *user_data, size_t user_data_len) {
    dds_qos_t *qos = dds_create_qos();
    dds_qset_reliability(qos, DDS_RELIABILITY_BEST_EFFORT, 0);
    dds_qset_durability(qos, DDS_DURABILITY_VOLATILE);
    dds_qset_history(qos, DDS_HISTORY_KEEP_LAST, 5);
    if (user_data && user_data_len > 0) {
        dds_qset_userdata(qos, user_data, user_data_len);
    }

    dds_listener_t *listener = dds_create_listener(NULL);
    dds_lset_data_available(listener, on_data_available_cb);

    dds_entity_t reader = dds_create_reader(participant, topic, qos, listener);

    dds_delete_listener(listener);
    dds_delete_qos(qos);
    return reader;
}

// Helper: take one sample from the reader.
// Returns 1 if a sample was taken, 0 if no data, negative on error.
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

// Helper: reset (remove) the listener on a DDS entity so no more callbacks fire.
static int32_t reset_listener(dds_entity_t entity) {
    return (int32_t)dds_set_listener(entity, NULL);
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
// If configXML is non-empty, the domain is created with that XML configuration.
func CreateParticipant(domainID int32, configXML string) (*DDSParticipant, error) {
	var cConfig *C.char
	if configXML != "" {
		cConfig = C.CString(configXML)
		defer C.free(unsafe.Pointer(cConfig))
	}

	h := C.create_participant_with_config(C.int32_t(domainID), cConfig)
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
// If typeHash is non-empty, it is set as USER_DATA QoS for ROS 2 type hash compatibility.
func CreateReaderWithListener(p *DDSParticipant, t *DDSTopic, typeHash string) (*DDSReader, error) {
	var cHash *C.char
	if typeHash != "" {
		cHash = C.CString(typeHash)
		defer C.free(unsafe.Pointer(cHash))
	}
	h := C.create_reader_with_listener(p.handle, t.handle, unsafe.Pointer(cHash), C.size_t(len(typeHash)))
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

// ResetListener removes the listener from a DDS entity so no more callbacks fire.
func ResetListener(handle int32) error {
	rc := C.reset_listener(C.dds_entity_t(handle))
	if rc < 0 {
		return fmt.Errorf("dds_set_listener(NULL) failed: %d", rc)
	}
	return nil
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
