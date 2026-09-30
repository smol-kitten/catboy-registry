module github.com/smol-kitten/catboy-registry/tests/runners/go

go 1.23.0

require github.com/smol-kitten/catboy-registry/go v0.0.0

require (
	golang.org/x/net v0.38.0 // indirect
	golang.org/x/text v0.23.0 // indirect
)

replace github.com/smol-kitten/catboy-registry/go => ../../../build/go
