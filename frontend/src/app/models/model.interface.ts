export interface Model {
  id: string;
  name: string;
  description?: string;
  owner: string;
  created_at: string;
}

export interface ModelCreate {
  name: string;
  description?: string;
  owner: string;
}

export interface ModelListResponse {
  items: Model[];
  next_cursor?: string;
}
