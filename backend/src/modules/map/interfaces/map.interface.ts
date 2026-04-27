export interface MapPose {
  x: number;
  y: number;
  theta: number;
}

export interface MapMetadata {
  mapId: string;
  resolution: number;
  width: number;
  height: number;
  origin: MapPose;
}

export interface Vertex {
  name: string;
  pose: MapPose;
}

export interface MapPayload {
  mapMetadata: MapMetadata;
  vertexes: Vertex[];
}
