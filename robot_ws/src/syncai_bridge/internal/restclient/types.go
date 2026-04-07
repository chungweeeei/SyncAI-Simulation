package restclient

// MapPayload is the response from GET /api/v1/map.
type MapPayload struct {
	MapMetadata MapMetadata `json:"mapMetadata"`
	Vertexes    []Vertex    `json:"vertexes"`
}

// MapMetadata describes the map grid properties.
type MapMetadata struct {
	MapID      string  `json:"mapId"`
	Resolution float64 `json:"resolution"`
	Width      int     `json:"width"`
	Height     int     `json:"height"`
	Origin     Pose    `json:"origin"`
}

// Pose represents a 2D position with orientation.
type Pose struct {
	X     float64 `json:"x"`
	Y     float64 `json:"y"`
	Theta float64 `json:"theta"`
}

// Vertex is a named position on the map.
type Vertex struct {
	Name string `json:"name"`
	Pose Pose   `json:"pose"`
}
