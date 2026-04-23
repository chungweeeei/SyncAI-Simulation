//go:build linux && amd64

package dds

// #cgo LDFLAGS: -L/opt/ros/jazzy/lib/x86_64-linux-gnu -Wl,-rpath,/opt/ros/jazzy/lib/x86_64-linux-gnu
import "C"
