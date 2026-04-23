//go:build linux && arm64

package dds

// #cgo LDFLAGS: -L/opt/ros/jazzy/lib/aarch64-linux-gnu -Wl,-rpath,/opt/ros/jazzy/lib/aarch64-linux-gnu
import "C"
