export interface UserPublic {
  id: number;
  username: string;
  email?: string | null;
  avatar_url?: string | null;
  created_at: string;
}

export interface AvatarUploadResponse {
  avatar_url: string;
}

export interface HealthResponse {
  status: string;
  gptsovits: boolean;
  qdrant: boolean;
  postgres: boolean;
}
