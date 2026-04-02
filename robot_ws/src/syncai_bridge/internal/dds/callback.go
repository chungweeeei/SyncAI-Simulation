package dds

// This file must import "C" for the //export directive to work.
// The exported function is called from C code in cyclonedds.go.

import "C"
import "sync"

// Global registry mapping DDS reader handles to DDSBridge instances.
// Needed because CycloneDDS listener callbacks are C functions that
// cannot carry Go closure context.
var (
	readerRegistry   = make(map[int32]*DDSBridge)
	readerRegistryMu sync.RWMutex
)

//export goOnDataAvailable
func goOnDataAvailable(readerHandle C.int) {
	handle := int32(readerHandle)
	readerRegistryMu.RLock()
	b, ok := readerRegistry[handle]
	readerRegistryMu.RUnlock()
	if !ok {
		return
	}
	b.onDataAvailable()
}
